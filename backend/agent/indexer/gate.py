"""Fail-closed gate for switching a versioned RAG index.

The gate deliberately treats reports as untrusted input.  It does not import
the offline evaluation package: a report may be produced by a temporary eval
checkout and can be removed after rollout without making this module depend on
it.  The default CLI mode only reads reports.  Alias mutation is reachable
only through the explicit ``--activate`` flag and consists of one
``FT.ALIASUPDATE`` command.
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
    """Normalized evidence consumed by :func:`evaluate_gate`.

    ``None`` means that the corresponding evidence was not present.  Keeping
    missing values distinct from zero is important: a missing report must not
    accidentally pass a zero-valued metric.  The report loader fills every
    field, while tests and callers may construct this value directly.
    """

    index_version: str | None = None
    coverage: float | None = None
    nsfw_count: int | None = None
    non_anime_count: int | None = None
    required_failed: int | None = None
    required_total: int | None = None
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
    """Evaluate all rollout requirements; any missing/invalid value rejects."""

    checks: dict[str, bool] = {}
    reasons: list[str] = list(inputs.report_errors)

    def require(name: str, condition: bool, reason: str) -> None:
        checks[name] = bool(condition)
        if not condition:
            reasons.append(reason)

    require("reports_complete", inputs.reports_complete, "required report is missing or malformed")
    require("index_version", _valid_version(inputs.index_version), "index version is missing or invalid")
    versions = dict(inputs.report_versions)
    version_ok = bool(versions) and _all_versions_match(versions, inputs.index_version)
    require("report_versions", version_ok, "report versions are missing or inconsistent")
    require(
        "content_hash_sample_match",
        inputs.content_hash_sample_match is True,
        "content_hash sample does not match the authoritative catalog",
    )
    require(
        "embedding_contract_match",
        inputs.embedding_contract_match is True,
        "embedding provider/model/dimensions/profile version are inconsistent",
    )

    require("coverage", _at_least(inputs.coverage, INDEX_COVERAGE_MIN), "coverage is below 99.5%")
    require("nsfw_count", inputs.nsfw_count == 0, "index contains NSFW entries")
    require("non_anime_count", inputs.non_anime_count == 0, "index contains non-anime entries")
    require("required_failed", inputs.required_failed == 0, "required eval cases failed")
    require("required_total", inputs.required_total == 120, "required eval count is missing or is not exactly 120")
    require("mrr10", _at_least(inputs.mrr10, MRR10_MIN), "MRR@10 is below 0.90")
    require("recall20", _at_least(inputs.recall20, RECALL20_MIN), "Recall@20 is below 0.85")
    require("ndcg10", _at_least(inputs.ndcg10, NDCG10_MIN), "nDCG@10 is below 0.75")
    require("redis_p95_ms", _strictly_below(inputs.redis_p95_ms, REDIS_P95_MAX_MS), "Redis P95 is not below 250 ms")
    require("hydrated_p95_ms", _strictly_below(inputs.hydrated_p95_ms, HYDRATED_P95_MAX_MS), "hydrated P95 is not below 500 ms")
    require("memory_utilization", _at_most(inputs.memory_utilization, MEMORY_UTILIZATION_MAX), "memory utilization exceeds 60%")
    require("human_severe_errors", inputs.human_severe_errors == 0, "human review found severe errors")
    require("human_check_count", inputs.human_check_count is not None and inputs.human_check_count >= 20, "human check count is missing or below 20")

    # Preserve report order while avoiding duplicate messages from one failed
    # requirement being surfaced twice.
    unique_reasons = tuple(dict.fromkeys(reasons))
    return GateDecision(not unique_reasons, unique_reasons, checks)


def load_gate_inputs(report_dir: str | Path, index_version: str) -> GateInputs:
    """Load the five rollout reports from ``report_dir``.

    Reports must be explicit JSON files.  Missing files, malformed JSON,
    missing versions, and missing required evidence are represented in the
    returned value and therefore fail closed through :func:`evaluate_gate`.
    """

    directory = Path(report_dir)
    payloads: dict[str, Mapping[str, Any]] = {}
    errors: list[str] = []
    versions: dict[str, str] = {}
    for name in REPORT_NAMES:
        path = _report_path(directory, name, index_version)
        if path is None:
            errors.append(f"missing report: {name}")
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            errors.append(f"invalid report: {name}")
            continue
        if not isinstance(raw, Mapping):
            errors.append(f"invalid report root: {name}")
            continue
        payloads[name] = raw
        version = _text(raw, "indexVersion", "index_version", "version") or _version_from_filename(path, index_version)
        if version is None:
            errors.append(f"missing report version: {name}")
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
    if required_total is None:
        errors.append("missing required eval count")
    if required_passed is not None and required_failed is None and required_total is not None:
        required_failed = required_total - required_passed
    human_check_count = _integer(human_values, "checkCount", "humanCheckCount", "human_check_count")
    if human_check_count is None:
        errors.append("missing human check count")
    return GateInputs(
        index_version=index_version,
        coverage=_number(quality, "coverage", "indexCoverage", "coverageRatio"),
        nsfw_count=_integer(counts, "NSFW", "nsfw", "nsfwCount") if counts else _integer(quality, "nsfwCount", "nsfw_count"),
        non_anime_count=_integer(counts, "NON_ANIME", "nonAnime", "nonAnimeCount") if counts else _integer(quality, "nonAnimeCount", "non_anime_count"),
        required_failed=required_failed,
        required_total=required_total,
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


# Backwards-friendly name for callers that use the plan's report terminology.
read_gate_reports = load_gate_inputs


def activate_alias(redis_client: Any, index_version: str, *, alias: str | None = None) -> None:
    """Atomically update the alias; this function never deletes old data."""

    _validate_name(index_version, "index version")
    alias_name = alias or os.getenv("RAG_INDEX_ALIAS", "idx:rag:subject:active")
    _validate_alias(alias_name)
    index_name = f"idx:rag:subject:{index_version}"
    redis_client.execute_command("FT.ALIASUPDATE", alias_name, index_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check and optionally activate a RAG index gate")
    parser.add_argument("--index-version", required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--activate", action="store_true", help="activate only after every gate passes")
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

    # Keep the activation summary visible immediately before the sole alias
    # mutation.  Values are report-derived; no secrets or query text are shown.
    print(f"old_index=unchanged new_index=idx:rag:subject:{args.index_version}")
    for name in REPORT_NAMES:
        print(f"report={name} present={name in inputs.report_summaries}")
    try:
        import redis

        url = os.getenv("RAG_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.Redis.from_url(url)
        activate_alias(client, args.index_version)
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


def _version_from_filename(path: Path, expected: str) -> str | None:
    stem = path.stem
    if any(stem.endswith(f"{separator}{expected}") for separator in ("-", "_", ".")):
        return expected
    return None


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
            return None, "missing content_hash sample evidence"
        if "expected" in samples or "observed" in samples:
            pairs = (samples,)
        else:
            pairs = tuple(value for value in samples.values() if isinstance(value, Mapping))
            if len(pairs) != len(samples):
                return None, "invalid content_hash sample evidence"
    elif isinstance(samples, list) and samples:
        pairs = tuple(item for item in samples if isinstance(item, Mapping))
        if len(pairs) != len(samples):
            return None, "invalid content_hash sample evidence"
    else:
        return None, "missing content_hash sample evidence"
    if not pairs or any(not _nonempty(pair.get("expected")) or not _nonempty(pair.get("observed")) for pair in pairs):
        return None, "invalid content_hash sample evidence"
    match = all(pair["expected"] == pair["observed"] for pair in pairs)
    reported = payload.get("contentHashSampleMatch", payload.get("content_hash_sample_match"))
    if isinstance(reported, bool) and reported != match:
        match = False
    return match, None if match else "content_hash sample mismatch"


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
            return (False, "embedding contract mismatch") if flag is False else (None, "missing embedding contract evidence")
        contract = _normalize_contract(raw)
        if contract is None:
            return False, "embedding contract is incomplete"
        contracts.append(contract)
    if not contracts:
        return None, "missing embedding contract evidence"
    normalized = {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in contracts}
    if len(normalized) != 1:
        return False, "embedding contract mismatch"
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
        raise ValueError(f"invalid {label}")


def _validate_alias(value: str) -> None:
    if not value or not all(char.isalnum() or char in "._:-" for char in value):
        raise ValueError("invalid index alias")


if __name__ == "__main__":
    raise SystemExit(main())
