"""将明确的中文条件收敛到受控 ``RetrievalQuery`` 字段。

该模块不是通用 NLP 解析器：只接受带明确标记的年份、季度、播出状态、评分
和评分人数表达式。无法确定的内容保留在原始语义查询中，交给现有词法/语义
召回；任何推断都不能绕过 RetrievalQuery 的 Pydantic 边界。
"""

from __future__ import annotations

import re

from app.rag.schemas import RetrievalQuery


_YEAR = r"(?:18|19|20|21|22)\d{2}"
_YEAR_RANGE = re.compile(rf"(?<!\d)(?P<start>{_YEAR})\s*(?:年)?\s*(?:到|至|[-~])\s*(?P<end>{_YEAR})(?:年)?")
_YEAR_SINGLE = re.compile(rf"(?<!\d)(?P<year>{_YEAR})\s*(?:年|年度)")
_SCORE_MIN = re.compile(
    r"(?:评分|分数)\s*(?:(?P<operator>>=|>|至少|不低于|大于等于)|(?:为|是))?\s*"
    r"(?P<value>\d+(?:\.\d+)?)\s*(?:分)?\s*(?P<suffix>以上|及以上|起|或更高|\+|>=)?"
)
_RATING_TOTAL_MIN = re.compile(
    r"(?:评分人数|评价人数|投票数)\s*(?:(?P<operator>>=|>|至少|不低于|大于等于)|(?:为|是))?\s*"
    r"(?P<value>\d+)\s*(?:人|票)?\s*(?P<suffix>以上|及以上|起|或更多|\+|>=)?"
)

_QUARTERS = (
    ("spring", ("春季", "春番", "第一季度", "一季度", "Q1", "q1")),
    ("summer", ("夏季", "夏番", "第二季度", "二季度", "Q2", "q2")),
    ("autumn", ("秋季", "秋番", "第三季度", "三季度", "Q3", "q3")),
    ("winter", ("冬季", "冬番", "第四季度", "四季度", "Q4", "q4")),
)
_AIR_STATUS = (
    ("UPCOMING", ("即将播出", "未播", "待播")),
    ("AIRING", ("正在播出", "在播", "连载中")),
    ("FINISHED", ("已完结", "完结", "播完")),
)


def plan_retrieval_query(query: RetrievalQuery) -> RetrievalQuery:
    """只把明确的文本条件补到结构化字段，显式字段永远优先。"""

    text = query.semantic_query
    if not text:
        return query
    updates: dict[str, object] = {}

    if query.year_from is None and query.year_to is None:
        year_range = _YEAR_RANGE.search(text)
        if year_range:
            start = int(year_range.group("start"))
            end = int(year_range.group("end"))
            if start <= end:
                updates["year_from"] = start
                updates["year_to"] = end
        else:
            year_single = _YEAR_SINGLE.search(text)
            if year_single:
                year = int(year_single.group("year"))
                updates["year_from"] = year
                updates["year_to"] = year

    if query.quarter is None:
        quarter_matches = [quarter for quarter, markers in _QUARTERS if any(marker in text for marker in markers)]
        if len(quarter_matches) == 1:
            updates["quarter"] = quarter_matches[0]

    if query.air_status is None:
        status_matches = []
        for status, markers in _AIR_STATUS:
            if any(marker in text for marker in markers):
                if status == "FINISHED" and any(negative in text for negative in ("未完结", "尚未完结")):
                    continue
                status_matches.append(status)
        if len(status_matches) == 1:
            updates["air_status"] = status_matches[0]

    if query.score_min is None:
        score_match = _SCORE_MIN.search(text)
        if score_match and (score_match.group("operator") or score_match.group("suffix")):
            value = float(score_match.group("value"))
            if 0 <= value <= 10:
                updates["score_min"] = value

    if query.rating_total_min is None:
        rating_match = _RATING_TOTAL_MIN.search(text)
        if rating_match and (rating_match.group("operator") or rating_match.group("suffix")):
            updates["rating_total_min"] = int(rating_match.group("value"))

    return query.model_copy(update=updates) if updates else query
