"""季度映射跨层回归：Python 词表 == Java SeasonUtil == MySQL QUARTER()。

权威约定：动漫季 == 日历季度（winter=1 / spring=2 / summer=3 / autumn=4）。
本文件从 Java 源码、MySQL QUARTER() 语义、六个 Python 消费方三个方向钉死
同一约定；任何一端再次漂移都必须在这里失败，而不是在线上返回错季结果。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.adapters.redis.subject_index import _vector_filter
from app.rag.query_planner import plan_retrieval_query
from app.rag.retrieval import RagRetrievalService, _item_quarter
from app.rag.schemas import RetrievalQuery
from app.rag.seasons import SEASON_QUARTERS, season_month_range
from jobs.importer.main import parse_season_key
from jobs.indexer.shadow_eval import build_shadow_sql

EXPECTED_QUARTERS = {"winter": 1, "spring": 2, "summer": 3, "autumn": 4}
EXPECTED_MONTH_RANGES = {"winter": (1, 3), "spring": (4, 6), "summer": (7, 9), "autumn": (10, 12)}

SEASON_UTIL_PATH = (
    Path(__file__).resolve().parents[3]
    / "business"
    / "client"
    / "src"
    / "main"
    / "java"
    / "top"
    / "zhaizz"
    / "client"
    / "util"
    / "SeasonUtil.java"
)
_SEASON_UTIL_CASE = re.compile(
    r'case "(?P<season>winter|spring|summer|autumn)" -> new LocalDate\[\]\{'
    r"LocalDate\.of\(year, (?P<month_from>\d+), \d+\), LocalDate\.of\(year, (?P<month_to>\d+), \d+\)\}"
)


def _java_season_ranges() -> dict[str, tuple[int, int]]:
    """从 SeasonUtil.java 源码解析四季月份段；文件缺失或分支缺失时 fail loud。"""
    source = SEASON_UTIL_PATH.read_text(encoding="utf-8")
    return {
        match.group("season"): (int(match.group("month_from")), int(match.group("month_to")))
        for match in _SEASON_UTIL_CASE.finditer(source)
    }


# A. 词表自身就是权威约定


def test_season_quarters_is_the_single_authoritative_mapping():
    assert SEASON_QUARTERS == EXPECTED_QUARTERS


@pytest.mark.parametrize(("season", "expected"), sorted(EXPECTED_MONTH_RANGES.items()))
def test_season_month_range_matches_authoritative_months(season, expected):
    assert season_month_range(season) == expected


# B. Java SeasonUtil 源码级对齐（无需 JDK；任何一侧改动都会失败）


def test_python_vocabulary_matches_java_season_util():
    java_ranges = _java_season_ranges()
    assert set(java_ranges) == set(EXPECTED_QUARTERS), (
        f"SeasonUtil.java 季度分支缺失或文件已移动，仅解析到: {sorted(java_ranges)}"
    )
    for season, (month_from, month_to) in java_ranges.items():
        assert (month_from, month_to) == season_month_range(season)
        # SeasonUtil 月份段必须整体落在同一 MySQL 日历季度内
        assert SEASON_QUARTERS[season] == (month_from - 1) // 3 + 1
        assert SEASON_QUARTERS[season] == (month_to - 1) // 3 + 1


# C. MySQL QUARTER() 公式与 _item_quarter 日历算法对齐


@pytest.mark.parametrize("month", range(1, 13))
def test_mysql_quarter_formula_matches_vocabulary(month):
    season = next(s for s, (m1, m2) in EXPECTED_MONTH_RANGES.items() if m1 <= month <= m2)
    assert (month - 1) // 3 + 1 == SEASON_QUARTERS[season]


@pytest.mark.parametrize(
    ("air_date", "season"),
    [
        ("2026-01-15", "winter"),
        ("2026-04-15", "spring"),
        ("2026-07-15", "summer"),
        ("2026-10-15", "autumn"),
    ],
)
def test_item_quarter_calendar_formula_stays_aligned(air_date, season):
    assert _item_quarter({"airDate": air_date}) == SEASON_QUARTERS[season]


@pytest.mark.parametrize(("season", "quarter"), sorted(EXPECTED_QUARTERS.items()))
def test_item_quarter_string_label_uses_canonical_mapping(season, quarter):
    assert _item_quarter({"quarter": season}) == quarter


# D. 六个消费方对同一标签落到同一季度/月份段


@pytest.mark.parametrize(("season", "quarter"), sorted(EXPECTED_QUARTERS.items()))
def test_vector_filter_uses_canonical_quarter(season, quarter):
    expression = _vector_filter(RetrievalQuery(semantic_query="测试", quarter=season))
    assert f".quarter == {quarter}" in expression


@pytest.mark.parametrize(("season", "quarter"), sorted(EXPECTED_QUARTERS.items()))
def test_redisearch_expression_uses_canonical_quarter(season, quarter):
    service = RagRetrievalService(
        index=None,
        embeddings=None,
        authority_lookup=lambda *args, **kwargs: [],
        business_search=lambda *args, **kwargs: [],
    )
    expression = service._build_expression(RetrievalQuery(semantic_query="测试", quarter=season))
    assert f"@quarter:[{quarter} {quarter}]" in expression


@pytest.mark.parametrize("season", sorted(EXPECTED_QUARTERS))
def test_evidence_filter_accepts_only_dates_inside_season(season):
    month_from, _month_to = season_month_range(season)
    outside_month = 10 if month_from == 1 else 1
    query = RetrievalQuery(semantic_query="测试", quarter=season)
    assert RagRetrievalService._matches_query_filters({"airDate": f"2026-{month_from:02d}-15"}, query) is True
    assert RagRetrievalService._matches_query_filters({"airDate": f"2026-{outside_month:02d}-15"}, query) is False


@pytest.mark.parametrize("season", sorted(EXPECTED_QUARTERS))
def test_shadow_sql_month_bounds_match_canonical_range(season):
    _sql, params = build_shadow_sql(RetrievalQuery.model_validate({"quarter": season}), index_version="v1")
    month_from, month_to = season_month_range(season)
    assert params["quarter_month_from"] == month_from
    assert params["quarter_month_to"] == month_to


@pytest.mark.parametrize("season", sorted(EXPECTED_QUARTERS))
def test_importer_season_key_scans_canonical_months(season):
    year, month_from, month_to = parse_season_key(f"2026-{season}")
    assert year == 2026
    assert (month_from, month_to) == season_month_range(season)


@pytest.mark.parametrize(
    ("text", "season"),
    [
        ("2026年Q1新番", "winter"),
        ("2026年第一季度新番", "winter"),
        ("一季度新番", "winter"),
        ("冬季新番", "winter"),
        ("2026年Q2新番", "spring"),
        ("第二季度新番", "spring"),
        ("春季新番", "spring"),
        ("春番", "spring"),
        ("2026年Q3新番", "summer"),
        ("第三季度新番", "summer"),
        ("夏季新番", "summer"),
        ("夏番", "summer"),
        ("2026年Q4新番", "autumn"),
        ("第四季度新番", "autumn"),
        ("秋季新番", "autumn"),
        ("秋番", "autumn"),
    ],
)
def test_planner_maps_quarter_hints_to_canonical_season(text, season):
    planned = plan_retrieval_query(RetrievalQuery(semantic_query=text))
    assert planned.quarter == season
