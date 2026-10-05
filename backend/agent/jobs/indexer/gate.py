"""用于切换带版本 RAG 索引的失败即闭合门禁。

本门禁刻意把报告视为不可信输入。它不导入离线评估包：
报告可能由临时的 eval checkout 生成，并在上线后删除，
而不会让本模块产生依赖。默认 CLI 模式只读取报告。
激活委托给 MySQL 的 ``search_index_release`` 存储；本模块绝不修改 Redis。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping


INDEX_COVERAGE_MIN = 0.995
MRR10_MIN = 0.90
RECALL20_MIN = 0.85
NDCG10_MIN = 0.75
REDIS_P95_MAX_MS = 250.0
HYDRATED_P95_MAX_MS = 500.0
MEMORY_UTILIZATION_MAX = 0.60
REPORT_NAMES = ("quality", "capacity", "eval", "latency", "human")


@dataclass(frozen=True)
class GateInputs:
    """:func:`evaluate_gate` 消费的归一化证据。

    ``None`` 表示对应证据不存在。把缺失值与零区分开很重要：
    缺失的报告不得因指标为零而意外通过。报告加载器会填充每个字段，
    而测试与调用方可以直接构造该值。
    """

    index_version: str | None = None
    coverage: float | None = None
    nsfw_count: int | None = None
    non_anime_count: int | None = None
    required_failed: int | None = None
    required_passed: int | None = None
    required_total: int | None = None
    eval_failures: tuple[str, ...] | None = None
    evaluation_status: str | None = None
    evidence_completeness: float | None = None
    mrr10: float | None = None
    recall20: float | None = None
    ndcg10: float | None = None
    redis_p95_ms: float | None = None
    hydrated_p95_ms: float | None = None
    memory_utilization: float | None = None
    human_severe_errors: int | None = None
    human_check_count: int | None = None
    report_versions: Mapping[str, str] = field(default_factory=dict)
    content_hash_sample_match: bool | None = None
    embedding_contract_match: bool | None = None
    reports_complete: bool = False
    report_errors: tuple[str, ...] = ()
    report_summaries: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reasons: tuple[str, ...] = ()
    checks: Mapping[str, bool] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "checks": dict(self.checks),
        }


def evaluate_gate(inputs: GateInputs) -> GateDecision:
    """评估所有上线要求；任何缺失/无效值都会导致拒绝。"""

    checks: dict[str, bool] = {}
    reasons: list[str] = list(inputs.report_errors)

    def require(name: str, condition: bool, reason: str) -> None:
        checks[name] = bool(condition)
        if not condition:
            reasons.append(reason)

    require("reports_complete", inputs.reports_complete, "必需的报告缺失或格式错误")
    require("index_version", _valid_version(inputs.index_version), "索引版本缺失或无效")
    versions = dict(inputs.report_versions)
    version_ok = bool(versions) and _all_versions_match(versions, inputs.index_version)
    require("report_versions", version_ok, "报告版本缺失或不一致")
    require(
        "content_hash_sample_match",
        inputs.content_hash_sample_match is True,
        "content_hash 样本与权威目录不匹配",
    )
    require(
        "embedding_contract_match",
        inputs.embedding_contract_match is True,
        "向量 provider/model/维度/档案版本不一致",
    )

    require("coverage", _at_least(inputs.coverage, INDEX_COVERAGE_MIN), "覆盖率低于 99.5%")
    require("nsfw_count", inputs.nsfw_count == 0, "索引包含 NSFW 条目")
    require("non_anime_count", inputs.non_anime_count == 0, "索引包含非动画条目")
    require("required_failed", inputs.required_failed == 0, "必需评测用例失败")
    require("required_passed", inputs.required_passed == 120, "必需评测通过数缺失或不为 120")
    require("required_total", inputs.required_total == 120, "必需评测总数缺失或不是恰好 120")
    require("required_consistency", inputs.required_passed is not None and inputs.required_failed is not None and inputs.required_total is not None and inputs.required_passed + inputs.required_failed == inputs.required_total, "必需评测计数不一致")
    require("eval_failures", inputs.eval_failures == (), "评测报告包含失败项或缺少失败项")
    require(
        "evaluation_status",
        inputs.evaluation_status == "RELEASE_CANDIDATE",
        "评测报告状态必须显式为 RELEASE_CANDIDATE；SHADOW_ONLY 或状态缺失都不能激活发布",
    )
    require(
        "evidence_completeness",
        _at_least(inputs.evidence_completeness, 1.0),
        "证据完整度低于 100%",
    )
    require("mrr10", _at_least(inputs.mrr10, MRR10_MIN), "MRR@10 低于 0.90")
    require("recall20", _at_least(inputs.recall20, RECALL20_MIN), "Recall@20 低于 0.85")
    require("ndcg10", _at_least(inputs.ndcg10, NDCG10_MIN), "nDCG@10 低于 0.75")
    require("redis_p95_ms", _strictly_below(inputs.redis_p95_ms, REDIS_P95_MAX_MS), "Redis P95 不低于 250 ms")
    require("hydrated_p95_ms", _strictly_below(inputs.hydrated_p95_ms, HYDRATED_P95_MAX_MS), "补齐后 P95 不低于 500 ms")
    require("memory_utilization", _at_most(inputs.memory_utilization, MEMORY_UTILIZATION_MAX), "内存利用率超过 60%")
    require("human_severe_errors", inputs.human_severe_errors == 0, "人工审核发现严重错误")
    require("human_check_count", inputs.human_check_count is not None and inputs.human_check_count >= 20, "人工检查数量缺失或低于 20")

    # 保持报告顺序，同时避免同一失败要求产生重复消息。
    unique_reasons = tuple(dict.fromkeys(reasons))
    return GateDecision(not unique_reasons, unique_reasons, checks)


def load_gate_inputs(report_dir: str | Path, index_version: str) -> GateInputs:
    """从 ``report_dir`` 加载五份上线报告。

    报告必须是显式的 JSON 文件。文件缺失、JSON 格式错误、
    版本缺失以及必需证据缺失都会体现在返回值中，
    并因此通过 :func:`evaluate_gate` 失败即闭合。
    """

    directory = Path(report_dir)
    payloads: dict[str, Mapping[str, Any]] = {}
    errors: list[str] = []
    versions: dict[str, str] = {}
    for name in REPORT_NAMES:
        path = _report_path(directory, name, index_version)
        if path is None:
            errors.append(f"缺少报告: {name}")
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append(f"报告无效: {name}")
            continue
        if not isinstance(raw, Mapping):
            errors.append(f"报告根结构无效: {name}")
            continue
        payloads[name] = raw
        version = _text(raw, "indexVersion", "index_version", "version")
        if version is None:
            errors.append(f"缺少报告版本: {name}")
        else:
            versions[name] = version

    quality = payloads.get("quality", {})
    capacity = payloads.get("capacity", {})
    evaluation = payloads.get("eval", {})
    latency = payloads.get("latency", {})
    human = payloads.get("human", {})

    content_match, content_error = _content_hash_match(quality)
    if content_error:
        errors.append(content_error)
    contract_match, contract_error = _contract_match(*(payloads.get(name, {}) for name in REPORT_NAMES))
    if contract_error:
        errors.append(contract_error)

    counts = _mapping(quality.get("counts"))
    latency_values = _mapping(latency.get("latency"))
    human_values = _human_values(human)
    summaries = {name: dict(payload) for name, payload in payloads.items()}
    required_total = _integer(evaluation, "requiredTotal", "required_total")
    required_passed = _integer(evaluation, "requiredPassed", "required_passed")
    required_failed = _integer(evaluation, "requiredFailed", "required_failed")
    if required_total is None or required_passed is None or required_failed is None:
        errors.append("缺少必需评测计数")
    failures_value = evaluation.get("failures")
    if not isinstance(failures_value, list):
        errors.append("缺少评测失败项")
        eval_failures = None
    else:
        eval_failures = tuple(str(item) for item in failures_value)
    case_results = evaluation.get("caseResults", evaluation.get("case_results"))
    if not isinstance(case_results, list) or required_total is None or len(case_results) != required_total:
        errors.append("缺少评测用例结果")
    evaluation_status = _text(evaluation, "status")
    human_check_count = _integer(human_values, "checkCount", "humanCheckCount", "human_check_count")
    if human_check_count is None:
        errors.append("缺少人工检查数量")
    return GateInputs(
        index_version=index_version,
        coverage=_number(quality, "coverage", "indexCoverage", "coverageRatio"),
        nsfw_count=_integer(counts, "NSFW", "nsfw", "nsfwCount") if counts else _integer(quality, "nsfwCount", "nsfw_count"),
        non_anime_count=_integer(counts, "NON_ANIME", "nonAnime", "nonAnimeCount") if counts else _integer(quality, "nonAnimeCount", "non_anime_count"),
        required_failed=required_failed,
        required_passed=required_passed,
        required_total=required_total,
        eval_failures=eval_failures,
        evaluation_status=evaluation_status,
        evidence_completeness=_number(evaluation, "evidenceCompleteness", "evidence_completeness"),
        mrr10=_number(evaluation, "mrr10", "mrrAt10", "mrr_at_10"),
        recall20=_number(evaluation, "recall20", "recallAt20", "recall_at_20"),
        ndcg10=_number(evaluation, "ndcg10", "ndcgAt10", "ndcg_at_10"),
        redis_p95_ms=_first_number(latency_values, latency, "redisP95Ms", "redis_p95_ms", "redisP95"),
        hydrated_p95_ms=_first_number(latency_values, latency, "hydratedP95Ms", "hydrated_p95_ms", "hydratedP95"),
        memory_utilization=_number(capacity, "memoryUtilization", "memory_utilization", "utilization"),
        human_severe_errors=_integer(human_values, "severeErrors", "humanSevereErrors", "human_severe_errors"),
        human_check_count=human_check_count,
        report_versions=versions,
        content_hash_sample_match=content_match,
        embedding_contract_match=contract_match,
        reports_complete=not errors,
        report_errors=tuple(errors),
        report_summaries=summaries,
    )


# 为沿用计划报告术语的调用方保留的向后兼容名称。
read_gate_reports = load_gate_inputs


def activate_release(release_store: Any, index_version: str) -> None:
    """通过 MySQL 发布契约激活已通过门禁的版本。"""
    _validate_name(index_version, "index version")
    activate = getattr(release_store, "activate", None)
    if not callable(activate):
        raise TypeError("release_store 必须提供 activate(index_version)")
    activate(index_version)


def activate_alias(_redis_client: Any, _index_version: str, *, alias: str | None = None) -> None:
    """兼容性守卫：刻意不支持 Redis 别名。"""
    raise RuntimeError("Redis alias 已移除；请通过 MySQL search_index_release 激活")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查并可选地激活 RAG 索引门禁")
    parser.add_argument("--index-version", required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--activate", action="store_true", help="仅在所有门禁通过后才激活")
    args = parser.parse_args(argv)
    try:
        inputs = load_gate_inputs(args.report_dir, args.index_version)
        decision = evaluate_gate(inputs)
    except (OSError, ValueError, TypeError) as error:
        print(f"gate=FAIL reason={error}")
        return 1

    for name, passed in decision.checks.items():
        print(f"{name}={'PASS' if passed else 'FAIL'}")
    print(f"gate={'PASS' if decision.allowed else 'FAIL'}")
    if not decision.allowed:
        for reason in decision.reasons:
            print(f"reason={reason}")
        return 1
    if not args.activate:
        print("activation=SKIPPED")
        return 0

    # 保持激活摘要可见；发布变更需要应用提供 MySQL 存储，
    # 刻意不做隐式的 CLI I/O。
    print(f"old_index=unchanged new_index=rag:vectors:SUBJECT:{args.index_version}")
    for name in REPORT_NAMES:
        print(f"report={name} present={name in inputs.report_summaries}")
    try:
        from sqlalchemy.orm import Session

        from app.adapters.mysql.import_records import get_engine
        from app.adapters.mysql.release_store import MySqlReleaseStore

        engine = get_engine(
            os.getenv("DB_HOST", "127.0.0.1"),
            int(os.getenv("DB_PORT", "3306")),
            os.getenv("DB_USER", "root"),
            os.getenv("DB_PASSWORD", ""),
            os.getenv("DB_NAME", "anime_tracker"),
        )
        activate_release(MySqlReleaseStore(lambda: Session(engine)), args.index_version)
    except Exception as error:
        print(f"activation=FAIL reason={type(error).__name__}")
        return 1
    print("activation=PASS")
    return 0


def _report_path(directory: Path, name: str, version: str) -> Path | None:
    candidates = (
        directory / f"{name}.json",
        directory / f"{name}-{version}.json",
        directory / f"rag-{name}-{version}.json",
        directory / f"rag-{name}.json",
    )
    return next((path for path in candidates if path.is_file()), None)


def _valid_version(value: str | None) -> bool:
    return bool(value and value.strip() and ":" not in value and all(char.isalnum() or char in "._-" for char in value))


def _all_versions_match(versions: Mapping[str, str], expected: str | None) -> bool:
    return _valid_version(expected) and len(versions) == len(REPORT_NAMES) and all(value == expected for value in versions.values())


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _at_least(value: float | None, threshold: float) -> bool:
    return _finite(value) and float(value) >= threshold


def _strictly_below(value: float | None, threshold: float) -> bool:
    return _finite(value) and float(value) < threshold


def _at_most(value: float | None, threshold: float) -> bool:
    return _finite(value) and float(value) <= threshold


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(payload: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _number(payload: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = payload.get(key)
        if _finite(value):
            return float(value)
    return None


def _first_number(first: Mapping[str, Any], second: Mapping[str, Any], *keys: str) -> float | None:
    value = _number(first, *keys)
    return value if value is not None else _number(second, *keys)


def _integer(payload: Mapping[str, Any], *keys: str) -> int | None:
    value = _number(payload, *keys)
    return int(value) if value is not None and value.is_integer() else None


def _content_hash_match(payload: Mapping[str, Any]) -> tuple[bool | None, str | None]:
    samples = payload.get("contentHashSamples", payload.get("content_hash_samples"))
    if isinstance(samples, Mapping):
        if not samples:
            return None, "缺少 content_hash 样本证据"
        if "expected" in samples or "observed" in samples:
            pairs = (samples,)
        else:
            pairs = tuple(value for value in samples.values() if isinstance(value, Mapping))
            if len(pairs) != len(samples):
                return None, "content_hash 样本证据无效"
    elif isinstance(samples, list) and samples:
        pairs = tuple(item for item in samples if isinstance(item, Mapping))
        if len(pairs) != len(samples):
            return None, "content_hash 样本证据无效"
    else:
        return None, "缺少 content_hash 样本证据"
    if not pairs or any(not _nonempty(pair.get("expected")) or not _nonempty(pair.get("observed")) for pair in pairs):
        return None, "content_hash 样本证据无效"
    match = all(pair["expected"] == pair["observed"] for pair in pairs)
    reported = payload.get("contentHashSampleMatch", payload.get("content_hash_sample_match"))
    if isinstance(reported, bool) and reported != match:
        match = False
    return match, None if match else "content_hash 样本不匹配"


def _nonempty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def _contract_match(*payloads: Mapping[str, Any]) -> tuple[bool | None, str | None]:
    contracts: list[dict[str, Any]] = []
    for payload in payloads:
        raw = payload.get("embeddingContract", payload.get("embedding_contract"))
        if not isinstance(raw, Mapping):
            flag = next((payload[key] for key in ("embeddingContractMatch", "embedding_contract_match", "profileConsistent", "profile_consistent") if isinstance(payload.get(key), bool)), None)
            return (False, "向量契约不匹配") if flag is False else (None, "缺少向量契约证据")
        contract_payload = dict(raw)
        for key in ("releaseProfileVersion", "release_profile_version"):
            if key in payload and key not in contract_payload:
                contract_payload[key] = payload[key]
        contract = _normalize_contract(contract_payload)
        if contract is None:
            return False, "向量契约不完整"
        contracts.append(contract)
    if not contracts:
        return None, "缺少向量契约证据"
    normalized = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in contracts}
    if len(normalized) != 1:
        return False, "向量契约不匹配"
    return True, None


def _normalize_contract(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    aliases = {
        "provider": ("provider", "embeddingProvider", "embedding_provider"),
        "model": ("model", "embeddingModel", "embedding_model"),
        "dimensions": ("dimensions", "dimension", "embeddingDimensions", "embedding_dimensions"),
        "profileVersion": ("profileVersion", "profile_version", "schemaVersion", "schema_version"),
    }
    values: dict[str, Any] = {}
    for name, keys in aliases.items():
        value = next((payload[key] for key in keys if key in payload), None)
        # 一次发布可能包含实体专属的投影档案（如 SUBJECT 与 PERSON），
        # 而门禁使用的向量契约必须显式且由五份报告共享。
        # 提供发布级契约时优先使用；旧报告继续使用其
        # embeddingContract.profileVersion 值。
        if name == "profileVersion":
            release_profile = next(
                (payload[key] for key in ("releaseProfileVersion", "release_profile_version") if key in payload),
                None,
            )
            raw_contract = payload.get("embeddingContract", payload.get("embedding_contract"))
            if isinstance(raw_contract, Mapping):
                release_profile = next(
                    (raw_contract[key] for key in ("releaseProfileVersion", "release_profile_version") if key in raw_contract),
                    release_profile,
                )
            if _nonempty(release_profile):
                value = release_profile
        if not _nonempty(value):
            return None
        if name == "dimensions":
            try:
                value = int(value)
            except (TypeError, ValueError, OverflowError):
                return None
            if value < 1:
                return None
        values[name] = value if name == "dimensions" else str(value).strip()
    return values


def _human_values(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    checks = payload.get("checks")
    if not isinstance(checks, list):
        return payload
    severe = 0
    for item in checks:
        if isinstance(item, Mapping):
            value = item.get("severeError", item.get("severe_error", item.get("severity")))
            if value is True or (isinstance(value, str) and value.upper() in {"SEVERE", "HIGH"}):
                severe += 1
    return {**payload, "severeErrors": severe, "checkCount": len(checks)}


def _validate_name(value: str, label: str) -> None:
    if not _valid_version(value):
        raise ValueError(f"{label} 无效")


def _validate_alias(value: str) -> None:
    if not value or not all(char.isalnum() or char in "._:-" for char in value):
        raise ValueError("索引别名无效")


if __name__ == "__main__":
    raise SystemExit(main())
