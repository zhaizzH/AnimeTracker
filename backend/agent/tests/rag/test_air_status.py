"""播出状态推断的单源回归：过滤侧与输出侧必须用同一条保守规则。

历史缺陷：``retrieval._infer_air_status_name`` 把无权威状态的过去日期判为
``FINISHED``，``use_case._infer_air_status`` 判为 ``UNKNOWN``。单个首播日期
不能证明作品已完结，本文件把「唯一共享函数」和「保守语义」同时钉死。
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.rag import retrieval as retrieval_module
from app.rag import use_case as use_case_module
from app.rag.air_status import infer_air_status
from app.rag.retrieval import RagRetrievalService
from app.rag.schemas import RetrievalQuery

_TODAY = date.today()
_PAST = (_TODAY - timedelta(days=365)).isoformat()
_FUTURE = (_TODAY + timedelta(days=365)).isoformat()
_AUTHORITATIVE = {"UPCOMING", "AIRING", "FINISHED"}


# A. 共享函数本身：权威值优先，兜底保守


@pytest.mark.parametrize("status", sorted(_AUTHORITATIVE))
def test_explicit_authoritative_status_passes_through(status):
    """权威 airStatus 直接采用，不受 airDate 影响。"""
    assert infer_air_status(_PAST, status) == status
    assert infer_air_status(_FUTURE, status) == status
    assert infer_air_status(None, status) == status


@pytest.mark.parametrize("status", sorted(_AUTHORITATIVE))
def test_explicit_status_is_case_insensitive(status):
    assert infer_air_status(_PAST, status.lower()) == status


def test_future_air_date_without_authority_is_upcoming():
    assert infer_air_status(_FUTURE) == "UPCOMING"


def test_past_air_date_without_authority_is_unknown():
    """过去日期不足以证明已完结。"""
    assert infer_air_status(_PAST) == "UNKNOWN"


def test_today_air_date_is_not_finished():
    assert infer_air_status(_TODAY.isoformat()) == "UNKNOWN"


@pytest.mark.parametrize("value", [None, "", "not-a-date", "2024-13-45", "2024"])
def test_unparsable_air_date_is_unknown(value):
    assert infer_air_status(value) == "UNKNOWN"


def test_inference_never_returns_finished():
    """兜底路径绝不臆断 FINISHED。"""
    for value in (None, _PAST, _FUTURE, "not-a-date"):
        for explicit in (None, "unknown", "", "  "):
            assert infer_air_status(value, explicit) != "FINISHED"


def test_non_authoritative_explicit_status_falls_back_to_date():
    """非三值的显式状态不能当权威值。"""
    assert infer_air_status(_FUTURE, "UNKNOWN") == "UPCOMING"
    assert infer_air_status(_PAST, "UNKNOWN") == "UNKNOWN"


@pytest.mark.parametrize("value", [None, _PAST, _FUTURE, "2024-01-01T12:00:00"])
def test_returns_only_known_status_labels(value):
    assert infer_air_status(value) in _AUTHORITATIVE | {"UNKNOWN"}


# B. 两处调用点必须复用同一函数，不得再存本地实现


def test_local_inference_functions_are_removed():
    assert not hasattr(retrieval_module, "_infer_air_status_name")
    assert not hasattr(use_case_module, "_infer_air_status")


def test_both_call_sites_use_the_shared_function():
    for module in (retrieval_module, use_case_module):
        imported = module.infer_air_status
        assert imported is infer_air_status, f"{module.__name__} 未复用共享推断函数"
        assert imported.__module__ == "app.rag.air_status"


# C. 过滤路径：权威值优先，兜底保守


def test_past_date_without_authority_is_excluded_from_finished_filter():
    """air_status=FINISHED 且无权威状态、airDate 在过去 → 排除。"""
    query = RetrievalQuery(keywords=["test"], air_status="FINISHED")
    assert RagRetrievalService._matches_query_filters({"airDate": _PAST}, query) is False


def test_past_date_with_authoritative_finished_is_included():
    """有权威 airStatus=FINISHED 时按权威值纳入。"""
    query = RetrievalQuery(keywords=["test"], air_status="FINISHED")
    item = {"airDate": _PAST, "airStatus": "FINISHED"}
    assert RagRetrievalService._matches_query_filters(item, query) is True


def test_future_date_still_matches_upcoming_filter():
    query = RetrievalQuery(keywords=["test"], air_status="UPCOMING")
    assert RagRetrievalService._matches_query_filters({"airDate": _FUTURE}, query) is True
    assert RagRetrievalService._matches_query_filters({"airDate": _PAST}, query) is False


def test_authoritative_status_overrides_air_date():
    query = RetrievalQuery(keywords=["test"], air_status="FINISHED")
    assert RagRetrievalService._matches_query_filters(
        {"airDate": _FUTURE, "airStatus": "FINISHED"}, query
    ) is True
    assert RagRetrievalService._matches_query_filters(
        {"airDate": _PAST, "airStatus": "AIRING"}, query
    ) is False


def test_non_authoritative_status_field_falls_back_to_date():
    """显式 UNKNOWN 不是权威值，仍走保守兜底。"""
    query = RetrievalQuery(keywords=["test"], air_status="FINISHED")
    assert RagRetrievalService._matches_query_filters(
        {"airDate": _PAST, "airStatus": "UNKNOWN"}, query
    ) is False
    assert RagRetrievalService._matches_query_filters({"airDate": _PAST}, query) is False


def test_missing_air_date_and_status_is_excluded():
    query = RetrievalQuery(keywords=["test"], air_status="FINISHED")
    assert RagRetrievalService._matches_query_filters({}, query) is False


def test_snake_case_air_fields_are_supported():
    query = RetrievalQuery(keywords=["test"], air_status="FINISHED")
    assert RagRetrievalService._matches_query_filters(
        {"air_date": _PAST, "air_status": "FINISHED"}, query
    ) is True
