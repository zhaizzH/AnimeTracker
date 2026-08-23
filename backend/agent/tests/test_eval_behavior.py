from __future__ import annotations

from evals.adapters import OfflineAdapter
from evals.assertions import case_failure
from evals.runner import load_subjects
from evals.schema import EvalCase


def test_safety_result_uses_fixed_fault_marker_not_yaml_expectation():
    case = EvalCase.model_validate({
        "id": "mutation-safety", "category": "safety_failure", "query": "redis injection",
        "fault": "redis_injection", "forbiddenSubjectIds": [1],
        "expectedErrorType": "ARBITRARY", "required": True,
    })

    result = OfflineAdapter(load_subjects()).evaluate(case)

    assert result.error_type == "REDIS_QUERY_REJECTED"
    assert case_failure(case, result.ranked, result.fallback, result.error_type) is not None


def test_structured_filters_change_fixed_fixture_results():
    case = EvalCase.model_validate({
        "id": "filter-2025-scifi", "category": "filters", "query": "科幻",
        "year": 2025, "quarter": 1, "scoreMin": 8.5, "tags": ["科幻"],
        "expectedSubjectIds": [3], "required": True,
    })

    assert OfflineAdapter(load_subjects()).evaluate(case).ranked == [3]


def test_personalization_state_reorders_and_excludes_fixed_fixture_candidates():
    watched = EvalCase.model_validate({
        "id": "watched", "category": "personalization", "query": "校园",
        "preferenceState": "watched", "expectedSubjectIds": [7], "required": True,
    })
    dropped = watched.model_copy(update={"id": "dropped", "preferenceState": "dropped", "expectedSubjectIds": (4,)})
    adapter = OfflineAdapter(load_subjects())

    assert adapter.evaluate(watched).ranked == [7]
    assert adapter.evaluate(dropped).ranked == [4]

def test_semantic_query_uses_fixture_feature_without_title_text():
    case = EvalCase.model_validate({
        "id": "semantic-topic", "category": "semantic", "query": "topic3",
        "expectedSubjectIds": [3], "required": True,
    })

    assert OfflineAdapter(load_subjects()).evaluate(case).ranked == [3]
