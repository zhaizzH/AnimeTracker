"""影子索引管理：创建、切换与回滚。

影子索引允许在不影响在线检索的情况下构建新版本索引，
验证数据质量后通过 alias 原子切换上线。
旧索引不提前删除，保留回滚窗口。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from app.shared.observability import log_event


ALIAS_PATTERN = "idx:rag:subject:active"
SHADOW_PREFIX = "idx:rag:subject:"


@dataclass(frozen=True)
class ShadowIndexInfo:
    """影子索引状态摘要。"""

    index_version: str
    index_name: str
    document_count: int
    alias_target: str | None = None
    is_active: bool = False
    created_at: str = ""


@dataclass(frozen=True)
class SwitchPlan:
    """alias 切换计划，需人工确认后执行。"""

    current_alias_target: str | None
    new_index_version: str
    new_index_name: str
    document_count: int
    quality_report_path: str | None = None
    gate_passed: bool = False
    gate_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class SwitchResult:
    """切换执行结果。"""

    success: bool
    old_target: str | None
    new_target: str
    timestamp: str
    error: str | None = None


class ShadowIndexManager:
    """管理影子索引生命周期：创建、查询状态、切换 alias、回滚。"""

    def __init__(self, redis_client: Any, *, alias: str = ALIAS_PATTERN):
        self._redis = redis_client
        self._alias = alias

    def list_indexes(self) -> list[str]:
        """列出所有已创建的 RAG 索引版本名。"""
        raw = self._redis.execute_command("FT._LIST")
        if not isinstance(raw, (list, tuple)):
            return []
        names = [item.decode() if isinstance(item, bytes) else str(item) for item in raw]
        return [name for name in names if name.startswith(SHADOW_PREFIX)]

    def get_info(self, index_version: str) -> ShadowIndexInfo | None:
        """获取指定版本索引的文档数和 alias 状态。"""
        index_name = f"{SHADOW_PREFIX}{index_version}"
        try:
            info = self._redis.execute_command("FT.INFO", index_name)
        except Exception:
            return None
        parsed = _parse_ft_info(info)
        doc_count = int(parsed.get("num_docs", 0))

        # 检查 alias 是否指向此索引
        alias_target = self._get_alias_target()
        is_active = alias_target == index_name

        return ShadowIndexInfo(
            index_version=index_version,
            index_name=index_name,
            document_count=doc_count,
            alias_target=alias_target,
            is_active=is_active,
        )

    def prepare_switch(
        self, index_version: str, *, quality_report_path: str | None = None, gate_passed: bool = False, gate_reasons: tuple[str, ...] = ()
    ) -> SwitchPlan:
        """生成切换计划；不执行实际切换。"""
        info = self.get_info(index_version)
        return SwitchPlan(
            current_alias_target=self._get_alias_target(),
            new_index_version=index_version,
            new_index_name=f"{SHADOW_PREFIX}{index_version}",
            document_count=info.document_count if info else 0,
            quality_report_path=quality_report_path,
            gate_passed=gate_passed,
            gate_reasons=gate_reasons,
        )

    def execute_switch(self, plan: SwitchPlan) -> SwitchResult:
        """执行 alias 原子切换；仅在 gate_passed=True 时允许。"""
        if not plan.gate_passed:
            return SwitchResult(
                success=False,
                old_target=plan.current_alias_target,
                new_target=plan.new_index_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error="gate not passed; refusing to switch",
            )
        old_target = plan.current_alias_target
        try:
            self._redis.execute_command("FT.ALIASUPDATE", self._alias, plan.new_index_name)
        except Exception as exc:
            return SwitchResult(
                success=False,
                old_target=old_target,
                new_target=plan.new_index_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(exc),
            )
        log_event(
            "rag.index.switch",
            indexVersion=plan.new_index_version,
            success=True,
        )
        return SwitchResult(
            success=True,
            old_target=old_target,
            new_target=plan.new_index_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def rollback(self, previous_version: str) -> SwitchResult:
        """回滚到之前的索引版本。"""
        previous_name = f"{SHADOW_PREFIX}{previous_version}"
        current = self._get_alias_target()
        try:
            self._redis.execute_command("FT.ALIASUPDATE", self._alias, previous_name)
        except Exception as exc:
            return SwitchResult(
                success=False,
                old_target=current,
                new_target=previous_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=str(exc),
            )
        log_event("rag.index.switch", indexVersion=previous_version, success=True, fallbackType="rollback")
        return SwitchResult(
            success=True,
            old_target=current,
            new_target=previous_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _get_alias_target(self) -> str | None:
        """尝试获取当前 alias 指向的索引名。"""
        try:
            # FT.INFO on alias returns info about the underlying index
            info = self._redis.execute_command("FT.INFO", self._alias)
            parsed = _parse_ft_info(info)
            return parsed.get("index_name")
        except Exception:
            return None


def _parse_ft_info(raw: Any) -> dict[str, Any]:
    """解析 FT.INFO 返回的 flat list 为字典。"""
    if isinstance(raw, dict):
        return raw
    result: dict[str, Any] = {}
    items = raw if isinstance(raw, (list, tuple)) else []
    for i in range(0, len(items) - 1, 2):
        key = items[i].decode() if isinstance(items[i], bytes) else str(items[i])
        value = items[i + 1]
        if isinstance(value, bytes):
            try:
                value = value.decode()
            except UnicodeDecodeError:
                pass
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    """CLI：影子索引管理。"""
    parser = argparse.ArgumentParser(description="Shadow index manager")
    parser.add_argument("action", choices=["list", "info", "switch", "rollback"])
    parser.add_argument("--index-version")
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args(argv)

    import redis as redis_lib

    url = os.getenv("RAG_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = redis_lib.Redis.from_url(url)
    manager = ShadowIndexManager(client)

    if args.action == "list":
        for name in manager.list_indexes():
            print(name)
        return 0

    if args.action == "info":
        if not args.index_version:
            print("error: --index-version required")
            return 1
        info = manager.get_info(args.index_version)
        if info is None:
            print(f"index not found: {args.index_version}")
            return 1
        print(json.dumps({
            "indexVersion": info.index_version,
            "indexName": info.index_name,
            "documentCount": info.document_count,
            "aliasTarget": info.alias_target,
            "isActive": info.is_active,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.action == "switch":
        if not args.index_version:
            print("error: --index-version required")
            return 1
        from jobs.indexer.gate import load_gate_inputs, evaluate_gate

        gate_passed = False
        gate_reasons: tuple[str, ...] = ()
        if args.report_dir:
            inputs = load_gate_inputs(args.report_dir, args.index_version)
            decision = evaluate_gate(inputs)
            gate_passed = decision.allowed
            gate_reasons = decision.reasons
        else:
            print("error: --report-dir required for switch")
            return 1

        plan = manager.prepare_switch(
            args.index_version,
            quality_report_path=str(args.report_dir) if args.report_dir else None,
            gate_passed=gate_passed,
            gate_reasons=gate_reasons,
        )
        result = manager.execute_switch(plan)
        print(json.dumps({
            "success": result.success,
            "oldTarget": result.old_target,
            "newTarget": result.new_target,
            "timestamp": result.timestamp,
            "error": result.error,
        }, ensure_ascii=False, indent=2))
        return 0 if result.success else 1

    if args.action == "rollback":
        if not args.index_version:
            print("error: --index-version required")
            return 1
        result = manager.rollback(args.index_version)
        print(json.dumps({
            "success": result.success,
            "oldTarget": result.old_target,
            "newTarget": result.new_target,
            "timestamp": result.timestamp,
            "error": result.error,
        }, ensure_ascii=False, indent=2))
        return 0 if result.success else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
