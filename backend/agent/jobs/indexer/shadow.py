"""Shadow Vector Set lifecycle and MySQL release-pointer switching.

Redis Vector Sets are data-plane storage only.  Activation and rollback are
delegated to an injected release store backed by Business/MySQL; this module
never uses Redis aliases or lets Redis decide the active version.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Protocol

from app.adapters.redis.vector_set import VECTOR_SET_PREFIX
from app.entities.enums import EntityKind
from app.shared.observability import log_event


SHADOW_PREFIX = VECTOR_SET_PREFIX
ALIAS_PATTERN = "search_index_release"


class ReleasePointer(Protocol):
    def active_version(self) -> str | None: ...
    def activate(self, index_version: str) -> None: ...


@dataclass(frozen=True)
class ShadowIndexInfo:
    index_version: str
    index_name: str
    document_count: int
    alias_target: str | None = None
    is_active: bool = False
    created_at: str = ""


@dataclass(frozen=True)
class SwitchPlan:
    current_alias_target: str | None
    new_index_version: str
    new_index_name: str
    document_count: int
    quality_report_path: str | None = None
    gate_passed: bool = False
    gate_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class SwitchResult:
    success: bool
    old_target: str | None
    new_target: str
    timestamp: str
    error: str | None = None


class ShadowIndexManager:
    """Inspect Vector Set shadow versions and switch the MySQL release pointer."""

    def __init__(self, redis_client: Any, *, alias: str = ALIAS_PATTERN, release_store: ReleasePointer | None = None):
        self._redis = redis_client
        self._alias = alias
        self._release_store = release_store

    def list_indexes(self) -> list[str]:
        scan_iter = getattr(self._redis, "scan_iter", None)
        if not callable(scan_iter):
            raise RuntimeError("Redis 客户端不支持 Vector Set 版本扫描")
        keys = []
        for raw in scan_iter(match=f"{SHADOW_PREFIX}{EntityKind.SUBJECT.value}:*"):
            key = raw.decode() if isinstance(raw, bytes) else str(raw)
            if key.startswith(f"{SHADOW_PREFIX}{EntityKind.SUBJECT.value}:"):
                keys.append(key)
        return sorted(set(keys))

    def get_info(self, index_version: str) -> ShadowIndexInfo | None:
        index_name = f"{SHADOW_PREFIX}{EntityKind.SUBJECT.value}:{index_version}"
        try:
            document_count = int(self._redis.execute_command("VCARD", index_name) or 0)
        except Exception:
            return None
        active_version = self._active_version()
        return ShadowIndexInfo(
            index_version=index_version,
            index_name=index_name,
            document_count=document_count,
            alias_target=(f"{SHADOW_PREFIX}{EntityKind.SUBJECT.value}:{active_version}" if active_version else None),
            is_active=active_version == index_version,
        )

    def prepare_switch(self, index_version: str, *, quality_report_path: str | None = None, gate_passed: bool = False, gate_reasons: tuple[str, ...] = ()) -> SwitchPlan:
        info = self.get_info(index_version)
        return SwitchPlan(
            current_alias_target=self._target_name(self._active_version()),
            new_index_version=index_version,
            new_index_name=f"{SHADOW_PREFIX}{EntityKind.SUBJECT.value}:{index_version}",
            document_count=info.document_count if info else 0,
            quality_report_path=quality_report_path,
            gate_passed=gate_passed,
            gate_reasons=gate_reasons,
        )

    def execute_switch(self, plan: SwitchPlan) -> SwitchResult:
        if not plan.gate_passed:
            return self._failure(plan.current_alias_target, plan.new_index_name, "gate not passed; refusing to switch")
        if self._release_store is None:
            return self._failure(plan.current_alias_target, plan.new_index_name, "MySQL release store unavailable; refusing Redis-only activation")
        try:
            self._release_store.activate(plan.new_index_version)
        except Exception as exc:
            return self._failure(plan.current_alias_target, plan.new_index_name, str(exc))
        log_event("rag.index.switch", indexVersion=plan.new_index_version, success=True)
        return SwitchResult(True, plan.current_alias_target, plan.new_index_name, _now())

    def rollback(self, previous_version: str) -> SwitchResult:
        previous_name = f"{SHADOW_PREFIX}{EntityKind.SUBJECT.value}:{previous_version}"
        current = self._target_name(self._active_version())
        if self._release_store is None:
            return self._failure(current, previous_name, "MySQL release store unavailable; refusing Redis-only rollback")
        try:
            self._release_store.activate(previous_version)
        except Exception as exc:
            return self._failure(current, previous_name, str(exc))
        log_event("rag.index.switch", indexVersion=previous_version, success=True, fallbackType="rollback")
        return SwitchResult(True, current, previous_name, _now())

    def _active_version(self) -> str | None:
        if self._release_store is None:
            return None
        try:
            return self._release_store.active_version()
        except Exception:
            return None

    @staticmethod
    def _target_name(version: str | None) -> str | None:
        return f"{SHADOW_PREFIX}{EntityKind.SUBJECT.value}:{version}" if version else None

    @staticmethod
    def _failure(old_target: str | None, new_target: str, error: str) -> SwitchResult:
        return SwitchResult(False, old_target, new_target, _now(), error)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ft_info(raw: Any) -> dict[str, Any]:
    """Compatibility parser for old report tooling; no FT command is used."""
    if isinstance(raw, dict):
        return raw
    result: dict[str, Any] = {}
    items = raw if isinstance(raw, (list, tuple)) else []
    for i in range(0, len(items) - 1, 2):
        key = items[i].decode() if isinstance(items[i], bytes) else str(items[i])
        value = items[i + 1].decode() if isinstance(items[i + 1], bytes) else items[i + 1]
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shadow Vector Set manager")
    parser.add_argument("action", choices=["list", "info", "switch", "rollback"])
    parser.add_argument("--index-version")
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args(argv)
    import redis as redis_lib

    url = os.getenv("RAG_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    manager = ShadowIndexManager(redis_lib.Redis.from_url(url))
    if args.action == "list":
        for name in manager.list_indexes():
            print(name)
        return 0
    if not args.index_version:
        print("error: --index-version required")
        return 1
    if args.action == "info":
        info = manager.get_info(args.index_version)
        if info is None:
            print(f"index not found: {args.index_version}")
            return 1
        print(json.dumps({"indexVersion": info.index_version, "indexName": info.index_name, "documentCount": info.document_count, "releaseVersion": info.alias_target, "isActive": info.is_active}, ensure_ascii=False, indent=2))
        return 0
    print("activation=FAIL reason=MySQL release store must be injected by the application")
    return 1
