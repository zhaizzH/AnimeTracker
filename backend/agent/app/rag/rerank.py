"""RRF 融合、重排与候选解析纯函数（从 retrieval.py 拆出，move-only）。"""
from __future__ import annotations

from array import array
from dataclasses import replace
from datetime import date
import math
from typing import Any, Mapping, Sequence

from app.rag.schemas import RetrievalQuery
from app.rag.user_profile import UserPreference

def reciprocal_rank_fusion(
    lexical: Sequence[Any], semantic: Sequence[Any], *, k: int = 60
) -> list[Any]:
    """按固定 RRF 公式融合，平分时保持最早出现的候选顺序。"""
    scores: dict[int, float] = {}
    reasons: dict[int, set[str]] = {}
    originals: dict[int, Any] = {}
    order: dict[int, int] = {}
    for source, label in ((lexical, "lexical"), (semantic, "semantic")):
        for rank, candidate in enumerate(source, start=1):
            sid = candidate.subject_id
            order.setdefault(sid, len(order))
            originals.setdefault(sid, candidate)
            scores[sid] = scores.get(sid, 0.0) + 1.0 / (k + rank)
            reasons.setdefault(sid, set()).add(label)
    return [
        replace(originals[sid], retrieval_score=scores[sid], retrieval_reason="+".join(sorted(reasons[sid])))
        for sid in sorted(scores, key=lambda value: (-scores[value], order[value]))
    ]

def filter_entity_subjects(
    candidates: Sequence[Any],
    allowed_subject_ids: list[int] | None,
) -> list[Any]:
    if allowed_subject_ids is None:
        return list(candidates)
    allowed = set(allowed_subject_ids)
    return [
        replace(candidate, retrieval_reason=f"{candidate.retrieval_reason}+entity")
        for candidate in candidates
        if candidate.subject_id in allowed
    ]

def as_candidates(response: Any, reason: str, candidate_type: type) -> list[Any]:
    rows = _raw_items(response)
    candidates: list[Any] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        # 业务侧词法候选用公开字段 ``subjectId``，
        # 而 Redis/旧适配器使用 ``subject_id`` 或 ``id``。
        # 在此边界统一三者，避免有效的 FULLTEXT 响应
        # 在 RRF 前被静默丢弃。
        raw_id = item.get("subject_id", item.get("subjectId", item.get("id")))
        if isinstance(raw_id, bool):
            continue
        try:
            subject_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        if subject_id <= 0:
            continue
        vector = item.get("vector")
        raw_score = item.get(
            "score",
            item.get("lexicalScore", item.get("vector_score", item.get("similarity", 0.0))),
        )
        try:
            retrieval_score = float(raw_score)
        except (TypeError, ValueError):
            retrieval_score = 0.0
        candidates.append(
            candidate_type(
                subject_id,
                retrieval_score,
                reason,
                str(item.get("title") or item.get("nameCn") or item.get("name") or ""),
                vector=vector if isinstance(vector, Sequence) and not isinstance(vector, (str, bytes)) else None,
            )
        )
    return candidates

def rerank(
    candidates: Sequence[Any],
    query: RetrievalQuery,
    preference: Mapping[int | str, float] | UserPreference | None,
) -> list[Any]:
    maximum = max((candidate.retrieval_score for candidate in candidates), default=1.0) or 1.0
    today = date.today()

    def score(candidate: Any) -> float:
        details = candidate.details or {}
        rating = min(max(float(details.get("ratingTotal") or 0) / 1000.0, 0.0), 1.0)
        popularity = min(max(float(details.get("collectionTotal") or 0) / 10000.0, 0.0), 1.0)
        freshness_value = freshness(details.get("airDate"), today)
        preferred = preference_score(candidate, preference)
        result = 0.55 * (candidate.retrieval_score / maximum) + 0.15 * rating + 0.10 * popularity + 0.10 * freshness_value + 0.10 * preferred
        title = str(details.get("nameCn") or details.get("name") or candidate.title)
        exact_terms = [query.semantic_query, *query.keywords]
        if any(term and title.casefold() == term.casefold() for term in exact_terms):
            result += 0.30
        evidence = candidate.evidence or {}
        raw_tags = evidence.get("metaTags") or evidence.get("meta_tags") or evidence.get("tags")
        if query.semantic_query and isinstance(raw_tags, (list, tuple, set)):
            semantic_text = query.semantic_query.strip().casefold()
            if any(str(tag).strip().casefold() == semantic_text for tag in raw_tags):
                # 元标签是语义标签用例的权威证据；
                # 在有界结果集中保留精确标签匹配。
                result += 0.35
        return min(result, 1.0)

    return sorted(candidates, key=lambda item: (-score(item), item.subject_id))

def has_textual_intent(query: RetrievalQuery) -> bool:
    """是否允许排序对结构化结果集重新排序。"""
    return bool(query.semantic_query or query.keywords)

def freshness(value: Any, today: date) -> float:
    try:
        year = date.fromisoformat(str(value)).year
    except (TypeError, ValueError):
        return 0.0
    return min(max(1.0 - (today.year - year) / 10.0, 0.0), 1.0)

def preference_score(candidate: Any, preference: Mapping[int | str, float] | UserPreference | None) -> float:
    if preference is None:
        return 0.0
    if isinstance(preference, Mapping):
        return min(
            max(float(preference.get(candidate.subject_id, preference.get(str(candidate.subject_id), 0.0))), 0.0),
            1.0,
        )
    profile_vector = getattr(preference, "vector", None)
    candidate_vector = candidate.vector
    if not isinstance(profile_vector, Sequence) or not isinstance(candidate_vector, Sequence):
        return 0.0
    if len(profile_vector) != len(candidate_vector) or not profile_vector:
        return 0.0
    try:
        dot = sum(float(left) * float(right) for left, right in zip(profile_vector, candidate_vector))
        profile_size = math.sqrt(sum(float(value) ** 2 for value in profile_vector))
        candidate_size = math.sqrt(sum(float(value) ** 2 for value in candidate_vector))
    except (TypeError, ValueError, OverflowError):
        return 0.0
    if not all(math.isfinite(value) for value in (dot, profile_size, candidate_size)) or not profile_size or not candidate_size:
        return 0.0
    return min(max((dot / (profile_size * candidate_size) + 1.0) / 2.0, 0.0), 1.0)

def _raw_items(response: Any) -> list[Any]:
    if isinstance(response, Mapping):
        if isinstance(response.get("items"), list):
            return response["items"]
        if isinstance(response.get("candidates"), list):
            return response["candidates"]
        if isinstance(response.get("content"), list):
            return response["content"]
        return []
    if isinstance(response, list):
        if response and isinstance(response[0], int):
            rows: list[dict[str, Any]] = []
            for offset in range(1, len(response), 2):
                if offset + 1 >= len(response) or not isinstance(response[offset + 1], (list, tuple)):
                    continue
                fields = response[offset + 1]
                row = {
                    _text(fields[i]): _decode_subject_vector(fields[i + 1]) if _text(fields[i]) == "vector" else _text(fields[i + 1])
                    for i in range(0, len(fields) - 1, 2)
                }
                row.setdefault("subject_id", _text(response[offset]).rsplit(":", 1)[-1])
                rows.append(row)
            return rows
        return response
    return []

def _decode_subject_vector(value: Any) -> list[float] | None:
    if not isinstance(value, bytes) or len(value) != 1024 * 4:
        return None
    decoded = array("f")
    decoded.frombytes(value)
    return list(decoded) if all(math.isfinite(number) for number in decoded) else None

def _text(value: Any) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)
