"""权威回查与 Evidence enrich：数据进入 Agent 上下文前的最终权威边界（从 retrieval.py 拆出，move-only）。"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from app.shared.observability import log_event
from app.rag.air_status import infer_air_status
from app.rag.entity_resolution import is_error
from app.rag.schemas import RetrievalQuery
from app.rag.seasons import SEASON_QUARTERS

EvidenceLookup = Callable[..., dict | list]

def items_of(response: Any) -> list[Any]:
    if isinstance(response, Mapping):
        if isinstance(response.get("items"), list):
            return response["items"]
        if isinstance(response.get("candidates"), list):
            return response["candidates"]
        if isinstance(response.get("content"), list):
            return response["content"]
        return []
    if isinstance(response, list):
        return response
    return []

def index_version(response: Any) -> str | None:
    """从词法响应中提取业务侧发布指针。"""
    if not isinstance(response, Mapping):
        return None
    value = response.get("indexVersion", response.get("index_version"))
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if ":" in value or any(char.isspace() for char in value):
        return None
    return value

def enrich_evidence(
    candidates: list[Any],
    token: str | None,
    evidence_lookup: EvidenceLookup,
) -> tuple[list[Any], bool]:
    """批量回查 Evidence API；失败或部分结果时 fail-closed。"""
    from dataclasses import replace

    try:
        response = evidence_lookup([c.subject_id for c in candidates], token=token)
    except Exception:
        log_event("rag.evidence.enriched", success=False, errorType="exception")
        return [], False
    if is_error(response):
        log_event("rag.evidence.enriched", success=False, errorType="business_error")
        return [], False
    rows = response if isinstance(response, list) else []
    by_id: dict[int, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or row.get("subjectId") is None or isinstance(row.get("subjectId"), bool):
            return [], False
        try:
            subject_id = int(row["subjectId"])
        except (TypeError, ValueError, OverflowError):
            return [], False
        if subject_id <= 0:
            return [], False
        if subject_id in by_id:
            # 合法 ID 重复意味着业务侧对同一 Subject 返回了两行
            # 自相矛盾的数据。字典会静默保留最后一行，而下方的
            # 键集合校验仍会通过，因此在此拒绝整个批次。
            log_event(
                "rag.evidence.enriched",
                success=False,
                errorType="duplicate_subject_id",
                duplicateSubjectId=subject_id,
            )
            return [], False
        by_id[subject_id] = row
    expected_ids = {candidate.subject_id for candidate in candidates}
    if by_id.keys() != expected_ids:
        log_event(
            "rag.evidence.enriched",
            success=False,
            errorType="partial_response",
            expectedCount=len(expected_ids),
            actualCount=len(by_id),
        )
        return [], False
    enriched = []
    for candidate in candidates:
        ev = by_id.get(candidate.subject_id)
        if ev is None or not is_safe_evidence(ev, candidate.subject_id):
            log_event("rag.evidence.enriched", success=False, errorType="unsafe_response")
            return [], False
        candidate = replace(candidate, evidence=map_evidence(ev))
        enriched.append(candidate)
    log_event("rag.evidence.enriched", success=True, candidateCount=len(enriched))
    return enriched, True

def is_safe_evidence(item: Mapping[str, Any], subject_id: int) -> bool:
    """验证 EvidenceCandidateVO 的安全边界，避免错误数据进入上下文。"""
    try:
        return (
            int(item.get("subjectId")) == subject_id
            and int(item.get("type") or 0) == 2
            and item.get("nsfw") is False
            and item.get("active") is True
        )
    except (TypeError, ValueError):
        return False

def map_evidence(ev: Mapping[str, Any]) -> dict[str, Any]:
    """将 EvidenceCandidateVO 映射为 Agent 内部证据字典。"""
    summary = str(ev.get("summary") or "")
    return {
        "aliases": [str(a) for a in (ev.get("aliases") or [])],
        "metaTags": [str(t) for t in (ev.get("metaTags") or [])],
        "credits": [
            f"{str(c.get('personName', ''))}({str(c.get('relation', ''))})"
            for c in (ev.get("credits") or [])
            if isinstance(c, Mapping)
        ],
        "characters": [
            f"{str(c.get('characterName', ''))}({str(c.get('relation', ''))})"
            for c in (ev.get("characters") or [])
            if isinstance(c, Mapping)
        ],
        "relations": [
            f"{str(r.get('relatedSubjectNameCn') or r.get('relatedSubjectName', ''))}({str(r.get('relation', ''))})"
            for r in (ev.get("relations") or [])
            if isinstance(r, Mapping)
        ],
        "summaryExcerpt": summary[:200] if summary else "",
        "summarySource": "bangumi_official",
        "ratingTotal": ev.get("ratingTotal"),
        "collectionTotal": ev.get("collectionTotal"),
        "score": ev.get("score"),
        "airDate": ev.get("airDate"),
        "airStatus": ev.get("airStatus") or ev.get("air_status"),
        "sourceTime": ev.get("sourceTime"),
        "sourceFetchedAt": ev.get("sourceFetchedAt") or ev.get("sourceTime"),
        "active": ev.get("active"),
        "sourceId": ev.get("sourceId"),
        "sourceUrl": ev.get("sourceUrl"),
        "nameCn": ev.get("nameCn"),
        "name": ev.get("name"),
        "type": ev.get("type"),
        "nsfw": ev.get("nsfw"),
        "rank": ev.get("rank"),
    }

def is_safe_authority_detail(item: Mapping[str, Any], query: RetrievalQuery) -> bool:
    """只校验业务侧批量权威接口提供的字段。

    此阶段不得运行结构化过滤，因为批量接口
    不包含 ``metaTags`` 等 Evidence 字段。
    """
    try:
        if (
            int(item.get("type") or 0) != 2
            or item.get("nsfw") is not False
            or item.get("active") is not True
        ):
            return False
        if int(item.get("id") or -1) in query.exclude_subject_ids:
            return False
    except (TypeError, ValueError):
        return False
    return True

def matches_query_filters(item: Mapping[str, Any], query: RetrievalQuery) -> bool:
    """对实体兜底使用的精确业务行应用查询过滤。"""
    if query.score_min is not None:
        try:
            if float(item.get("score")) < query.score_min:
                return False
        except (TypeError, ValueError):
            return False
    if query.rating_total_min is not None:
        try:
            if int(item.get("ratingTotal")) < query.rating_total_min:
                return False
        except (TypeError, ValueError):
            return False

    year = item_year(item)
    if query.year_from is not None and (year is None or year < query.year_from):
        return False
    if query.year_to is not None and (year is None or year > query.year_to):
        return False
    if query.quarter is not None:
        quarter = item_quarter(item)
        if quarter != SEASON_QUARTERS[query.quarter]:
            return False

    if query.air_status is not None:
        status = str(item.get("airStatus") or item.get("air_status") or "").upper()
        if status not in {"UPCOMING", "AIRING", "FINISHED"}:
            # 只允许保守推断来填补缺失或非权威状态；
            # 显式的 ``UNKNOWN`` 不得被当作权威值。
            status = infer_air_status(item.get("airDate") or item.get("air_date"))
        if status != query.air_status:
            return False

    if query.meta_tags:
        raw_tags = item.get("metaTags") or item.get("meta_tags") or item.get("tags")
        tags: set[str] = set()
        if isinstance(raw_tags, (list, tuple, set)):
            for raw_tag in raw_tags:
                if isinstance(raw_tag, Mapping):
                    raw_tag = raw_tag.get("name") or raw_tag.get("title")
                if raw_tag is not None:
                    tags.add(str(raw_tag).casefold())
        if any(tag.casefold() not in tags for tag in query.meta_tags):
            return False
    return True

def item_year(item: Mapping[str, Any]) -> int | None:
    raw_year = item.get("year")
    if raw_year is not None:
        try:
            return int(raw_year)
        except (TypeError, ValueError):
            return None
    raw_date = item.get("airDate") or item.get("air_date")
    try:
        return int(str(raw_date)[:4])
    except (TypeError, ValueError):
        return None

def item_quarter(item: Mapping[str, Any]) -> int | None:
    raw_quarter = item.get("quarter")
    if raw_quarter is not None:
        if isinstance(raw_quarter, str):
            normalized = raw_quarter.casefold()
            if normalized in SEASON_QUARTERS:
                return SEASON_QUARTERS[normalized]
        try:
            quarter = int(raw_quarter)
            return quarter if quarter in {1, 2, 3, 4} else None
        except (TypeError, ValueError):
            return None
    raw_date = item.get("airDate") or item.get("air_date")
    try:
        month = int(str(raw_date)[5:7])
    except (TypeError, ValueError):
        return None
    return ((month - 1) // 3) + 1 if 1 <= month <= 12 else None
