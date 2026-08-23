from __future__ import annotations

from evals.runner import DEFAULT_RAG_CASE_PATHS, run_offline


def test_offline_required_dataset_meets_quality_gate():
    report = run_offline(DEFAULT_RAG_CASE_PATHS)

    assert report.required_total == 120
    assert report.required_passed == 120
    assert report.mrr_at_10 >= 0.90
    assert report.recall_at_20 >= 0.85
    assert report.ndcg_at_10 >= 0.75
    assert report.valid_subject_id_ratio == 1.0
