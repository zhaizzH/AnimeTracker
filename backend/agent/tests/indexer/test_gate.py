from __future__ import annotations

from dataclasses import replace
import json

import pytest
from jobs.indexer.gate import GateInputs, _content_hash_match, _contract_match, activate_alias, evaluate_gate, load_gate_inputs


def _passing_inputs() -> GateInputs:
    return GateInputs(
        index_version="v1",
        coverage=.995,
        nsfw_count=0,
        non_anime_count=0,
        required_failed=0,
        required_passed=120,
        required_total=120,
        eval_failures=(),
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


def test_gate_cross_checks_eval_counts_and_failures():
    assert evaluate_gate(replace(_passing_inputs(), required_passed=None)).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), required_failed=1)).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), required_passed=119)).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), eval_failures=("case-1",))).allowed is False


def test_gate_rejects_missing_required_and_human_evidence():
    assert evaluate_gate(replace(_passing_inputs(), required_total=None)).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), required_total=119)).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), human_check_count=None)).allowed is False
    assert evaluate_gate(replace(_passing_inputs(), human_check_count=19)).allowed is False


def test_content_hash_samples_are_non_empty_and_have_expected_observed():
    assert _content_hash_match({"contentHashSamples": {}})[0] is None
    assert _content_hash_match({"contentHashSamples": []})[0] is None
    assert _content_hash_match({"contentHashSamples": [{"expected": "", "observed": "x"}]})[0] is None
    assert _content_hash_match({"contentHashSamples": [{"expected": "x", "observed": "x"}]}) == (True, None)


def test_contract_check_does_not_accept_first_true_when_reports_disagree():
    match, reason = _contract_match(
        {"embeddingContract": {"provider": "dashscope", "model": "v4", "dimensions": 1024, "profileVersion": "v1"}},
        {"embeddingContract": {"provider": "dashscope", "model": "v3", "dimensions": 1024, "profileVersion": "v1"}},
    )
    assert match is False
    assert reason == "embedding contract mismatch"


def test_boolean_contract_match_cannot_replace_complete_contract():
    match, reason = _contract_match({"embeddingContractMatch": True}, {"embeddingContractMatch": True})
    assert match is None
    assert reason == "missing embedding contract evidence"


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


def test_loader_accepts_actual_eval_snake_case_and_safe_filename_version(tmp_path):
    contract = {"provider": "dashscope", "model": "text-embedding-v4", "dimensions": 1024, "profileVersion": "subject-profile-v1"}
    reports = {
        "quality.json": {"indexVersion": "v1", "coverage": .995, "counts": {"NSFW": 0, "NON_ANIME": 0}, "contentHashSamples": [{"expected": "a", "observed": "a"}], "embeddingContract": contract},
        "capacity.json": {"indexVersion": "v1", "utilization": .6, "embeddingContract": contract},
        "eval-v1.json": {"indexVersion": "v1", "required_total": 120, "required_passed": 120, "required_failed": 0, "failures": [], "mrr_at_10": .9, "recall_at_20": .85, "ndcg_at_10": .75, "embeddingContract": contract},
        "latency.json": {"indexVersion": "v1", "redisP95Ms": 1, "hydratedP95Ms": 1, "embeddingContract": contract},
        "human.json": {"indexVersion": "v1", "severeErrors": 0, "checkCount": 20, "embeddingContract": contract},
    }
    for filename, payload in reports.items():
        (tmp_path / filename).write_text(json.dumps(payload), encoding="utf-8")
    assert evaluate_gate(load_gate_inputs(tmp_path, "v1")).allowed is True


def test_loader_does_not_infer_version_from_renamed_eval_file(tmp_path):
    (tmp_path / "eval-v1.json").write_text(json.dumps({"required_total": 120}), encoding="utf-8")
    loaded = load_gate_inputs(tmp_path, "v1")
    assert any("missing report version" in reason for reason in loaded.report_errors)


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
