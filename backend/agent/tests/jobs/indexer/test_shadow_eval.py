"""Tests for the read-only candidate-version evaluation adapter."""

from types import SimpleNamespace

import pytest

from app.rag.schemas import RetrievalQuery
from jobs.indexer.shadow_eval import (
    ShadowEvalReport,
    ShadowLexicalSearch,
    _required_case_passed,
    _single_subject_profile,
    build_shadow_sql,
)
from tests.evals.schemas import GoldenCase


def test_shadow_sql_is_version_scoped_and_parameterized():
    query = RetrievalQuery.model_validate(
        {"keywords": ["动画"], "year_from": 2024, "quarter": "autumn", "meta_tags": ["战斗"], "exclude_subject_ids": [9]}
    )
    sql, params = build_shadow_sql(query, index_version="v1", limit=20)

    assert "d.index_version = :index_version" in sql
    assert "MATCH(d.title, d.aliases, d.lexical_text)" in sql
    assert "d.entity_kind = 'SUBJECT'" in sql
    assert "v1" == params["index_version"]
    assert "动画" == params["query_text"]
    assert params["year_from"] == 2024
    assert params["quarter_month_from"] == 7
    assert params["quarter_month_to"] == 9
    assert params["tag_0"] == "战斗"
    assert params["exclude_0"] == 9
    assert "动画" not in sql


@pytest.mark.parametrize(
    ("quarter", "month_from", "month_to"),
    [
        ("spring", 1, 3),
        ("summer", 4, 6),
        ("autumn", 7, 9),
        ("winter", 10, 12),
    ],
)
def test_shadow_sql_maps_quarter_to_calendar_months(quarter, month_from, month_to):
    query = RetrievalQuery.model_validate({"quarter": quarter})

    _sql, params = build_shadow_sql(query, index_version="v1")

    assert params["quarter_month_from"] == month_from
    assert params["quarter_month_to"] == month_to


def test_shadow_sql_supports_filter_only_cases_without_match_expression():
    query = RetrievalQuery.model_validate({"year_from": 2024, "year_to": 2024})
    sql, params = build_shadow_sql(query, index_version="candidate-v1")

    assert "MATCH(" not in sql
    assert "s.air_date >= CONCAT(:year_from, '-01-01')" in sql
    assert params["year_to"] == 2024
    assert "ORDER BY s.score DESC, s.rating_total DESC, s.id ASC" in sql


def test_shadow_sql_uses_lexical_then_stable_subject_order_for_keyword_cases():
    query = RetrievalQuery.model_validate({"keywords": ["动画"]})
    sql, _ = build_shadow_sql(query, index_version="v1")

    assert "ORDER BY lexical_score DESC, s.score DESC, s.rating_total DESC, s.id ASC" in sql


def test_shadow_lexical_search_does_not_read_active_release(monkeypatch):
    statements = []

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def execute(self, statement, params):
            statements.append(str(statement))
            if "DISTINCT profile_version" in str(statement):
                return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: ["subject-profile-v1"]))
            return SimpleNamespace(mappings=lambda: SimpleNamespace(all=lambda: [{"subject_id": 7, "name": "A", "name_cn": "甲", "lexical_score": 2.5}]))

    class Engine:
        def connect(self):
            return Connection()

    adapter = ShadowLexicalSearch(Engine(), "shadow-v1")
    payload = adapter(RetrievalQuery.model_validate({"keywords": ["甲"]}))

    assert payload["indexVersion"] == "shadow-v1"
    assert payload["candidates"][0]["subjectId"] == 7
    assert all("search_index_release" not in statement for statement in statements)


def test_shadow_report_defaults_to_shadow_only_and_rejects_failed_candidate():
    report = ShadowEvalReport(
        indexVersion="v1",
        profileVersion="mixed-entity-v1",
        releaseProfileVersion="mixed-entity-v1",
        activeReleaseCount=0,
        datasetStatus="DEFINITION_ONLY",
        requiredTotal=120,
        requiredPassed=119,
        requiredFailed=1,
        failures=["title_name_01"],
        recall20=0.9,
        mrr10=0.9,
        ndcg10=0.8,
        hardFilterAccuracy=1.0,
        evidenceCompleteness=1.0,
        caseResults=[{} for _ in range(120)],
        embeddingContract={
            "provider": "dashscope",
            "model": "text-embedding-v4",
            "dimensions": 1024,
            "profileVersion": "mixed-entity-v1",
            "releaseProfileVersion": "mixed-entity-v1",
        },
    )
    assert report.status == "SHADOW_ONLY"

    with pytest.raises(ValueError):
        ShadowEvalReport(
            status="RELEASE_CANDIDATE",
            indexVersion="v1",
            profileVersion="subject-profile-v1",
            releaseProfileVersion="subject-profile-v1",
            activeReleaseCount=0,
            datasetStatus="DEFINITION_ONLY",
            requiredTotal=120,
            requiredPassed=119,
            requiredFailed=1,
            failures=["title_name_01"],
            recall20=1.0,
            mrr10=1.0,
            ndcg10=1.0,
            hardFilterAccuracy=1.0,
            evidenceCompleteness=1.0,
            caseResults=[{} for _ in range(120)],
            embeddingContract={
                "provider": "dashscope",
                "model": "text-embedding-v4",
                "dimensions": 1024,
                "profileVersion": "subject-profile-v1",
                "releaseProfileVersion": "subject-profile-v1",
            },
        )


def test_release_candidate_status_requires_clean_required_eval():
    report = ShadowEvalReport(
        status="RELEASE_CANDIDATE",
        indexVersion="v1",
        profileVersion="subject-profile-v1",
        releaseProfileVersion="subject-profile-v1",
        activeReleaseCount=0,
        datasetStatus="DEFINITION_ONLY",
        requiredTotal=120,
        requiredPassed=120,
        requiredFailed=0,
        failures=[],
        recall20=0.9,
        mrr10=0.9,
        ndcg10=0.8,
        hardFilterAccuracy=1.0,
        evidenceCompleteness=1.0,
        caseResults=[{} for _ in range(120)],
        embeddingContract={
            "provider": "dashscope",
            "model": "text-embedding-v4",
            "dimensions": 1024,
            "profileVersion": "subject-profile-v1",
            "releaseProfileVersion": "subject-profile-v1",
        },
    )
    assert report.status == "RELEASE_CANDIDATE"


def test_invalid_version_is_rejected():
    with pytest.raises(ValueError):
        build_shadow_sql(RetrievalQuery.model_validate({"keywords": ["甲"]}), index_version="v:1")


def test_airing_and_finished_filters_are_fail_closed_for_future_episodes():
    airing_sql, airing_params = build_shadow_sql(
        RetrievalQuery.model_validate({"air_status": "AIRING"}), index_version="v1"
    )
    finished_sql, finished_params = build_shadow_sql(
        RetrievalQuery.model_validate({"air_status": "FINISHED"}), index_version="v1"
    )

    assert "EXISTS (SELECT 1 FROM episode" in airing_sql
    assert "e.status='NA' OR e.airdate > :today" in airing_sql
    assert "NOT EXISTS (SELECT 1 FROM episode" in finished_sql
    assert "e.status='NA' OR e.airdate > :today" in finished_sql
    assert airing_params["today"] == finished_params["today"]


def test_multiple_subject_profiles_are_rejected_instead_of_limited():
    class Result:
        def scalars(self):
            return SimpleNamespace(all=lambda: ["subject-profile-v1", "subject-profile-v2"])

    class Connection:
        def execute(self, *_args, **_kwargs):
            return Result()

    with pytest.raises(ValueError, match="多个 SUBJECT profile_version"):
        _single_subject_profile(Connection(), "v1")


def test_required_pass_uses_must_contain_as_hard_requirement():
    case = GoldenCase.model_validate(
        {
            "id": "case-1",
            "category": "title_alias",
            "description": "test",
            "query": {"keywords": ["test"]},
            "expectation": {
                "expected_subject_ids": [1, 2, 3],
                "must_contain_all": [1],
            },
        }
    )

    assert _required_case_passed(case, [1]) is True
    assert _required_case_passed(case, [2]) is False
