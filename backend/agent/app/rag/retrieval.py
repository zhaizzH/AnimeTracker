from __future__ import annotations

from array import array
from dataclasses import dataclass, replace
from datetime import date
import math
import re
from typing import Any, Callable, Mapping, Sequence

from app.agent.http import call_api
from app.core.observability import log_event
from app.rag.embeddings import EmbeddingClient
from app.rag.schemas import RetrievalQuery
from app.rag.user_profile import UserPreference


_REDIS_RESERVED = re.compile(r'([,\.<>\{\}\[\}"\':;!@#$%^&*()\-+=~|\\/])')
_QUARTERS = {"spring": 1, "summer": 2, "autumn": 3, "winter": 4}
_MAX_RESULTS = 15
_REDIS_TAG_RESERVED = re.compile(r'([\.< >\{\}\[\}"\':;!@#$%^&*()\-+=~|\\/])')


def escape_redis_term(value: str, *, preserve_comma: bool = False) -> str:
    """唯一的 RediSearch 词元转义入口；调用方不能提供查询片段。"""
    return (_REDIS_TAG_RESERVED if preserve_comma else _REDIS_RESERVED).sub(r"\\\1", value)


@dataclass(frozen=True)
class RetrievalCandidate:
    subject_id: int
    retrieval_score: float
    retrieval_reason: str
    title: str = ""
    details: Mapping[str, Any] | None = None
    vector: Sequence[float] | None = None


@dataclass(frozen=True)
class RetrievalResult:
    available: bool
    items: list[RetrievalCandidate]
    reason: str = ""
    personalization_notice: str = ""


def reciprocal_rank_fusion(
    lexical: Sequence[RetrievalCandidate], semantic: Sequence[RetrievalCandidate], *, k: int = 60
) -> list[RetrievalCandidate]:
    """按固定 RRF 公式融合，平分时保持最早出现的候选顺序。"""
    scores: dict[int, float] = {}
    reasons: dict[int, set[str]] = {}
    originals: dict[int, RetrievalCandidate] = {}
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


AuthorityLookup = Callable[..., dict | list]


class RagRetrievalService:
    """混合召回只产生经过 Business 权威回查的安全候选。"""

    def __init__(
        self,
        index: Any,
        embeddings: EmbeddingClient,
        *,
        authority_lookup: AuthorityLookup | None = None,
        business_search: AuthorityLookup | None = None,
    ) -> None:
        self._index = index
        self._embeddings = embeddings
        self._authority_lookup = authority_lookup or self._batch_lookup
        self._business_search = business_search or self._fallback_search

    def retrieve(
        self,
        query: RetrievalQuery,
        mode: str,
        token: str | None = None,
        preference: Mapping[int | str, float] | UserPreference | None = None,
        personalization_missing: bool = False,
    ) -> RetrievalResult:
        del mode  # 召回策略固定，mode 仅供上层路由保留接口。
        lexical: list[RetrievalCandidate] = []
        semantic: list[RetrievalCandidate] = []
        redis_failed = False
        vector: list[float] | None = None
        if query.semantic_query:
            try:
                vector = self._embeddings.embed_documents([query.semantic_query])[0]
            except Exception:
                vector = None
        try:
            for expression in self._expressions(query):
                if self._lexical_terms(query) or vector is None:
                    lexical = self._as_candidates(self._index.lexical_search(expression, limit=50), "lexical")
                if vector is not None:
                    semantic = self._as_candidates(self._index.semantic_search(expression, vector, limit=50), "semantic")
                if not lexical and not semantic:
                    continue
                result = self._authoritative_result(reciprocal_rank_fusion(lexical, semantic), query, token, preference)
                if not result.available or result.items:
                    return self._complete(result, personalization_missing)
        except Exception:
            redis_failed = True
            lexical, semantic = [], []

        if redis_failed:
            return self._complete(self._business_fallback(query, token, preference), personalization_missing, "business")
        return self._complete(RetrievalResult(available=True, items=[], reason="no_results"), personalization_missing)

    @staticmethod
    def _complete(result: RetrievalResult, personalization_missing: bool, fallback_type: str | None = None) -> RetrievalResult:
        result = RagRetrievalService._with_personalization_notice(result, personalization_missing)
        log_event("rag.retrieval.completed", candidateCount=len(result.items), success=result.available)
        if fallback_type is not None:
            log_event("rag.fallback.used", fallbackType=fallback_type, success=result.available)
        return result

    def _expressions(self, query: RetrievalQuery) -> list[str]:
        attempts = [query]
        if query.score_min is not None or query.rating_total_min is not None:
            attempts.append(query.model_copy(update={"score_min": None, "rating_total_min": None}))
        if query.year_from is not None or query.year_to is not None:
            attempts.append(attempts[-1].model_copy(update={"year_from": None, "year_to": None}))
        if query.meta_tags:
            attempts.append(attempts[-1].model_copy(update={"meta_tags": []}))
        return [self._build_expression(attempt) for attempt in attempts[:4]]

    def _build_expression(self, query: RetrievalQuery) -> str:
        parts: list[str] = []
        terms = self._lexical_terms(query)
        if terms:
            words = " ".join(escape_redis_term(word) for word in terms)
            parts.append(f"(@title:({words})|@aliases:({words})|@summary:({words}))")
        if query.year_from is not None or query.year_to is not None:
            parts.append(f"@year:[{query.year_from if query.year_from is not None else '-inf'} {query.year_to if query.year_to is not None else '+inf'}]")
        if query.quarter:
            value = _QUARTERS[query.quarter]
            parts.append(f"@quarter:[{value} {value}]")
        if query.score_min is not None:
            parts.append(f"@score:[{query.score_min} +inf]")
        if query.rating_total_min is not None:
            parts.append(f"@rating_total:[{query.rating_total_min} +inf]")
        for tag in query.meta_tags:
            parts.append(f"@meta_tags:{{{escape_redis_term(tag, preserve_comma=True)}}}")
        if query.air_status:
            parts.append(f"@air_status:{{{escape_redis_term(query.air_status.lower())}}}")
        for subject_id in query.exclude_subject_ids:
            parts.append(f"-@subject_id:[{int(subject_id)} {int(subject_id)}]")
        return " ".join(parts) or "*"

    @staticmethod
    def _lexical_terms(query: RetrievalQuery) -> list[str]:
        if query.keywords:
            return list(query.keywords)
        if not query.semantic_query:
            return []
        terms: list[str] = []
        for token in query.semantic_query.split():
            terms.extend(token[offset : offset + 48] for offset in range(0, len(token), 48))
            if len(terms) >= 8:
                break
        return terms[:8]

    def _authoritative_result(
        self,
        candidates: Sequence[RetrievalCandidate],
        query: RetrievalQuery,
        token: str | None,
        preference: Mapping[int | str, float] | UserPreference | None,
    ) -> RetrievalResult:
        try:
            response = self._authority_lookup([item.subject_id for item in candidates[:50]], token=token, exclude_collected=True)
        except Exception:
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        if _is_error(response):
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        details_by_id = {int(item["id"]): item for item in _items(response) if isinstance(item, Mapping) and item.get("id") is not None}
        safe = [
            replace(candidate, details=details_by_id[candidate.subject_id])
            for candidate in candidates
            if candidate.subject_id in details_by_id and self._is_safe_detail(details_by_id[candidate.subject_id], query)
        ]
        return RetrievalResult(available=True, items=self._rerank(safe, query, preference)[:_MAX_RESULTS])

    def _business_fallback(
        self,
        query: RetrievalQuery,
        token: str | None,
        preference: Mapping[int | str, float] | UserPreference | None,
    ) -> RetrievalResult:
        try:
            response = self._business_search(query, token=token)
        except Exception:
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        if _is_error(response):
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        candidates = [
            RetrievalCandidate(int(item["id"]), 0.0, "business_fallback", str(item.get("nameCn") or item.get("name") or ""))
            for item in _items(response)
            if isinstance(item, Mapping) and item.get("id") is not None and int(item["id"]) not in query.exclude_subject_ids
        ]
        if not candidates:
            return RetrievalResult(available=True, items=[])
        return self._authoritative_result(candidates, query, token, preference)

    @staticmethod
    def _is_safe_detail(item: Mapping[str, Any], query: RetrievalQuery) -> bool:
        return int(item.get("type") or 0) == 2 and item.get("nsfw") is False and int(item.get("id") or -1) not in query.exclude_subject_ids

    @staticmethod
    def _as_candidates(response: Any, reason: str) -> list[RetrievalCandidate]:
        rows = _items(response)
        candidates: list[RetrievalCandidate] = []
        for item in rows:
            if not isinstance(item, Mapping):
                continue
            raw_id = item.get("subject_id", item.get("id"))
            try:
                subject_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            vector = item.get("vector")
            candidates.append(
                RetrievalCandidate(
                    subject_id,
                    0.0,
                    reason,
                    str(item.get("title") or ""),
                    vector=vector if isinstance(vector, Sequence) and not isinstance(vector, (str, bytes)) else None,
                )
            )
        return candidates

    @staticmethod
    def _rerank(
        candidates: Sequence[RetrievalCandidate],
        query: RetrievalQuery,
        preference: Mapping[int | str, float] | UserPreference | None,
    ) -> list[RetrievalCandidate]:
        maximum = max((candidate.retrieval_score for candidate in candidates), default=1.0) or 1.0
        today = date.today()

        def score(candidate: RetrievalCandidate) -> float:
            details = candidate.details or {}
            rating = min(max(float(details.get("ratingTotal") or 0) / 1000.0, 0.0), 1.0)
            popularity = min(max(float(details.get("collectionTotal") or 0) / 10000.0, 0.0), 1.0)
            freshness = _freshness(details.get("airDate"), today)
            preferred = _preference_score(candidate, preference)
            result = 0.55 * (candidate.retrieval_score / maximum) + 0.15 * rating + 0.10 * popularity + 0.10 * freshness + 0.10 * preferred
            title = str(details.get("nameCn") or details.get("name") or candidate.title)
            exact_terms = [query.semantic_query, *query.keywords]
            if any(term and title.casefold() == term.casefold() for term in exact_terms):
                result += 0.30
            return min(result, 1.0)

        return sorted(candidates, key=lambda item: (-score(item), item.subject_id))

    @staticmethod
    def _with_personalization_notice(result: RetrievalResult, missing: bool) -> RetrievalResult:
        if not missing:
            return result
        return replace(result, personalization_notice="基于你当前的收藏还不多，先给你看热门")

    @staticmethod
    def _batch_lookup(subject_ids: list[int], *, token: str | None, exclude_collected: bool) -> dict | list:
        return call_api(
            "POST",
            "/api/client/subjects/batch",
            token=token,
            json_body={"subjectIds": subject_ids, "excludeCollected": exclude_collected},
        )

    @staticmethod
    def _fallback_search(query: RetrievalQuery, *, token: str | None) -> dict | list:
        text = query.semantic_query or " ".join(query.keywords)
        return call_api("GET", "/api/client/subjects/search", params={"q": text, "page": 1, "size": _MAX_RESULTS}, token=token)


def _items(response: Any) -> list[Any]:
    if isinstance(response, Mapping):
        if isinstance(response.get("items"), list):
            return response["items"]
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


def _is_error(response: Any) -> bool:
    return isinstance(response, Mapping) and bool(response.get("error"))


def _freshness(value: Any, today: date) -> float:
    try:
        year = date.fromisoformat(str(value)).year
    except (TypeError, ValueError):
        return 0.0
    return min(max(1.0 - (today.year - year) / 10.0, 0.0), 1.0)


def _preference_score(candidate: RetrievalCandidate, preference: Mapping[int | str, float] | UserPreference | None) -> float:
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


def _decode_subject_vector(value: Any) -> list[float] | None:
    if not isinstance(value, bytes) or len(value) != 1024 * 4:
        return None
    decoded = array("f")
    decoded.frombytes(value)
    return list(decoded) if all(math.isfinite(number) for number in decoded) else None


def _text(value: Any) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)
