from __future__ import annotations

from collections import Counter

from evals.runner import DEFAULT_RAG_CASE_PATHS, load_cases


def test_required_rag_dataset_counts():
    cases = load_cases(DEFAULT_RAG_CASE_PATHS)
    assert Counter(case.category for case in cases) == {
        "title_alias": 20,
        "semantic": 30,
        "filters": 20,
        "personalization": 20,
        "safety_failure": 30,
    }
    assert all(case.required for case in cases)
    assert len({case.id for case in cases}) == 120
