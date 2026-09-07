"""Regression tests for release gate report safety."""

from jobs.indexer.gate import GateInputs, _normalize_contract, evaluate_gate, load_gate_inputs


def _passing_inputs(**overrides):
    values = {
        "index_version": "v1",
        "coverage": 1.0,
        "nsfw_count": 0,
        "non_anime_count": 0,
        "required_failed": 0,
        "required_passed": 120,
        "required_total": 120,
        "eval_failures": (),
        "mrr10": 0.95,
        "recall20": 0.95,
        "ndcg10": 0.95,
        "evidence_completeness": 1.0,
        "redis_p95_ms": 100.0,
        "hydrated_p95_ms": 200.0,
        "memory_utilization": 0.2,
        "human_severe_errors": 0,
        "human_check_count": 20,
        "report_versions": {name: "v1" for name in ("quality", "capacity", "eval", "latency", "human")},
        "content_hash_sample_match": True,
        "embedding_contract_match": True,
        "reports_complete": True,
    }
    values.update(overrides)
    return GateInputs(**values)


def test_shadow_only_eval_cannot_pass_gate():
    decision = evaluate_gate(_passing_inputs(evaluation_status="SHADOW_ONLY"))

    assert decision.allowed is False
    assert "eval report status must be explicit RELEASE_CANDIDATE; SHADOW_ONLY or missing status cannot activate a release" in decision.reasons


def test_missing_eval_status_cannot_pass_gate():
    decision = evaluate_gate(_passing_inputs())

    assert decision.allowed is False


def test_only_explicit_release_candidate_can_pass_status_check():
    decision = evaluate_gate(_passing_inputs(evaluation_status="RELEASE_CANDIDATE"))

    assert decision.allowed is True


def test_incomplete_evidence_cannot_pass_gate():
    decision = evaluate_gate(_passing_inputs(evidence_completeness=0.99))

    assert decision.allowed is False
    assert "evidence completeness is below 100%" in decision.reasons


def test_release_profile_version_overrides_entity_projection_profile():
    contract = _normalize_contract(
        {
            "provider": "dashscope",
            "model": "text-embedding-v4",
            "dimensions": 1024,
            "profileVersion": "subject-profile-v1",
            "releaseProfileVersion": "subject-profile-v1",
        }
    )

    assert contract["profileVersion"] == "subject-profile-v1"


def test_missing_eval_case_results_fails_closed():
    inputs = load_gate_inputs(__file__, "v1")

    assert "missing eval case results" in inputs.report_errors
