from __future__ import annotations

from dataclasses import replace
import json

import pytest
from indexer.gate import GateInputs, _contract_match, activate_alias, evaluate_gate, load_gate_inputs


def _passing_inputs() -> GateInputs:
    return GateInputs(
        index_version="v1",
        coverage=.995,
        nsfw_count=0,
        non_anime_count=0,
        required_failed=0,
        required_total=120,
        mrr10=.90,
        recall20=.85,
        ndcg10=.75,
        redis_p95_ms=249.99,
        hydrated_p95_ms=499.99,
        memory_utilization=.60,
        human_severe_errors=0,
        human_check_count=20,
        report_versions={name: "v1" for name in ("quality", "capacity", "eval", "latency", "human")},
        content_hash_sample_match=True,
        embedding_contract_match=True,
        reports_complete=True,
    )


def test_gate_rejects_single_failed_requirement():
    passing = _passing_inputs()
    for field, bad in {
        "coverage": .994, "nsfw_count": 1, "non_anime_count": 1,
        "required_failed": 1, "mrr10": .899, "recall20": .849,
        "ndcg10": .749, "redis_p95_ms": 250, "hydrated_p95_ms": 500,
        "memory_utilization": .601, "human_severe_errors": 1,
    }.items():
        assert evaluate_gate(replace(passing, **{field: bad})).allowed is False, field


def test_gate_rejects_missing_reports_and_inconsistent_evidence():
    assert evaluate_gate(replace(_passing_inputs(), reports_complete=False)).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), report_versions={"quality": "v2"})).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), content_hash_sample_match=False)).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), embedding_contract_match=False)).allowed is False


def test_contract_check_does_not_accept_first_true_when_reports_disagree():
    match, reason = _contract_match(
        {"embeddingContractMatch": True, "embeddingContract": {"model": "v4", "dimensions": 1024}},
        {"embeddingContract": {"model": "v3", "dimensions": 1024}},
    )
    assert match is False
    assert reason == "embedding contract mismatch"


def test_load_gate_inputs_is_fail_closed_for_missing_and_version_mismatch(tmp_path):
    assert evaluate_gate(load_gate_inputs(tmp_path, "v1")).allowed is False
    for name, payload in {
        "quality": {"indexVersion": "v1", "coverage": .995, "counts": {"NSFW": 0, "NON_ANIME": 0}, "contentHashSampleMatch": True, "embeddingContractMatch": True},
        "capacity": {"indexVersion": "v1", "utilization": .6, "embeddingContract": {"model": "x"}},
        "eval": {"indexVersion": "v2", "requiredTotal": 120, "requiredFailed": 0, "mrrAt10": .9, "recallAt20": .85, "ndcgAt10": .75},
        "latency": {"indexVersion": "v1", "redisP95Ms": 1, "hydratedP95Ms": 1},
        "human": {"indexVersion": "v1", "severeErrors": 0, "checkCount": 20},
    }.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
    decision = evaluate_gate(load_gate_inputs(tmp_path, "v1"))
    assert decision.allowed is False
    assert any("inconsistent" in reason for reason in decision.reasons)


def test_activate_alias_only_calls_alias_update_and_never_deletes():
    class FakeRedis:
        def __init__(self):
            self.commands = []

        def execute_command(self, *command):
            self.commands.append(command)

    redis = FakeRedis()
    activate_alias(redis, "v1", alias="idx:rag:subject:active")
    assert redis.commands == [("FT.ALIASUPDATE", "idx:rag:subject:active", "idx:rag:subject:v1")]
    with pytest.raises(ValueError):
        activate_alias(redis, "v1", alias="idx:rag:subject:active;DEL")
