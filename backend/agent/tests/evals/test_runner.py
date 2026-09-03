"""评测 runner 与 golden cases 加载测试。"""

import json
from pathlib import Path

import pytest

from tests.evals.runner import (
    EvalConfig,
    aggregate_report,
    evaluate_case,
    load_golden_cases,
    run_eval,
)
from tests.evals.schemas import GoldenCase, GoldenExpectation


@pytest.fixture
def sample_cases():
    return [
        GoldenCase(
            id="test_01",
            category="title_alias",
            description="精确命中",
            query={"keywords": ["测试"]},
            expectation=GoldenExpectation(expected_subject_ids=[1, 2], must_contain_all=[1]),
        ),
        GoldenCase(
            id="test_02",
            category="structured_filter",
            description="部分命中",
            query={"year_from": 2023, "year_to": 2023},
            expectation=GoldenExpectation(expected_subject_ids=[3, 4], must_contain_all=[3, 4]),
        ),
    ]


def _mock_retrieve(results_by_query: dict):
    """创建基于 query 的 mock 检索函数。"""
    def retrieve(query: dict) -> list[int]:
        key = json.dumps(query, sort_keys=True)
        return results_by_query.get(key, [])
    return retrieve


class TestLoadGoldenCases:
    def test_loads_from_default_path(self):
        cases = load_golden_cases()
        assert len(cases) >= 50, f"首版评测至少需要 50 条 golden cases，当前只有 {len(cases)} 条"

    def test_all_cases_have_required_fields(self):
        for case in load_golden_cases():
            assert case.id, f"case 缺少 id"
            assert case.category in {
                "title_alias", "structured_filter", "subjective_semantic",
                "person_character", "series_relation", "negation", "degradation",
            }, f"case {case.id} 的 category 无效: {case.category}"
            assert case.description, f"case {case.id} 缺少 description"
            assert case.query, f"case {case.id} 缺少 query"
            assert case.expectation.expected_subject_ids is not None

    def test_categories_coverage(self):
        """确保 golden cases 覆盖所有必需场景。"""
        cases = load_golden_cases()
        categories = {case.category for case in cases}
        required = {
            "title_alias", "structured_filter", "subjective_semantic",
            "person_character", "series_relation", "negation", "degradation",
        }
        missing = required - categories
        assert not missing, f"golden cases 缺少以下场景: {missing}"

    def test_loads_from_custom_path(self, tmp_path):
        data = [
            {
                "id": "custom_01",
                "category": "title_alias",
                "description": "自定义",
                "query": {"keywords": ["自定义"]},
                "expectation": {"expected_subject_ids": [99]},
            }
        ]
        path = tmp_path / "custom.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        cases = load_golden_cases(path)
        assert len(cases) == 1
        assert cases[0].id == "custom_01"


class TestEvaluateCase:
    def test_perfect_retrieval(self, sample_cases):
        case = sample_cases[0]
        retrieve = _mock_retrieve({
            json.dumps(case.query, sort_keys=True): [1, 2, 3],
        })
        result = evaluate_case(case, retrieve, config=EvalConfig(k=20))
        assert result.recall == 1.0
        assert result.ndcg == 1.0
        assert result.rr == 1.0
        assert result.all_must_contain_hit is True

    def test_partial_retrieval(self, sample_cases):
        case = sample_cases[0]
        retrieve = _mock_retrieve({
            json.dumps(case.query, sort_keys=True): [1, 5, 6],
        })
        result = evaluate_case(case, retrieve, config=EvalConfig(k=20))
        assert result.recall == 0.5
        assert result.rr == 1.0
        assert result.all_must_contain_hit is True

    def test_no_results(self, sample_cases):
        case = sample_cases[0]
        retrieve = _mock_retrieve({})
        result = evaluate_case(case, retrieve, config=EvalConfig(k=20))
        assert result.recall == 0.0
        assert result.rr == 0.0
        assert result.all_must_contain_hit is False

    def test_must_contain_failure(self, sample_cases):
        case = sample_cases[1]
        retrieve = _mock_retrieve({
            json.dumps(case.query, sort_keys=True): [3, 7, 8],
        })
        result = evaluate_case(case, retrieve, config=EvalConfig(k=20))
        assert result.all_must_contain_hit is False
        assert 3 in result.hit_ids
        assert 4 not in result.hit_ids


class TestAggregateReport:
    def test_empty_results(self):
        report = aggregate_report([])
        assert report.total_cases == 0
        assert report.recall_at_k == 0.0
        assert report.mrr_at_k == 0.0
        assert report.ndcg_at_k == 0.0

    def test_aggregates_metrics(self, sample_cases):
        results = [
            evaluate_case(sample_cases[0], _mock_retrieve({
                json.dumps(sample_cases[0].query, sort_keys=True): [1, 2],
            })),
            evaluate_case(sample_cases[1], _mock_retrieve({
                json.dumps(sample_cases[1].query, sort_keys=True): [3, 5],
            })),
        ]
        report = aggregate_report(results, config=EvalConfig(k=20))
        assert report.total_cases == 2
        assert report.recall_at_k == pytest.approx((1.0 + 0.5) / 2)
        assert "title_alias" in report.per_category
        assert "structured_filter" in report.per_category

    def test_per_category_breakdown(self, sample_cases):
        results = [
            evaluate_case(sample_cases[0], _mock_retrieve({
                json.dumps(sample_cases[0].query, sort_keys=True): [1, 2],
            })),
            evaluate_case(sample_cases[1], _mock_retrieve({
                json.dumps(sample_cases[1].query, sort_keys=True): [3, 5],
            })),
        ]
        report = aggregate_report(results)
        assert report.per_category["title_alias"]["count"] == 1
        assert report.per_category["structured_filter"]["count"] == 1


class TestRunEval:
    def test_run_eval_with_cases(self, sample_cases):
        def retrieve(query: dict) -> list[int]:
            return [1, 2, 3]
        report = run_eval(retrieve, cases=sample_cases, config=EvalConfig(k=20))
        assert report.total_cases == 2
        assert report.case_results is not None
        assert len(report.case_results) == 2

    def test_run_eval_loads_golden_cases(self):
        """使用真实 golden cases 运行评测。"""
        def retrieve(query: dict) -> list[int]:
            return []
        report = run_eval(retrieve, config=EvalConfig(k=20))
        assert report.total_cases >= 50
