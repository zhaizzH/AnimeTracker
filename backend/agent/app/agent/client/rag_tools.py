from __future__ import annotations

from array import array
import math
from typing import Annotated, Any, Literal, Mapping, Sequence

import redis
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from pydantic import ValidationError

from app.agent.http import call_api
from app.config import settings
from app.core.middleware import tool_call_status
from app.rag.embeddings import DashScopeEmbeddingClient
from app.rag.redis_index import RedisSubjectIndex
from app.rag.retrieval import RagRetrievalService, RetrievalCandidate
from app.rag.schemas import RetrievalQuery
from app.rag.user_profile import CollectionItem, UserPreference, UserProfileService
from app.schemas.auth import UserInfo


_MAX_CANDIDATES = 15
_VECTOR_BYTES = 1024 * 4


class _UnavailableIndex:
    """关闭 RAG 时阻止 Redis 访问，并驱动检索服务走已有 Business 回退。"""

    @staticmethod
    def lexical_search(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("RAG index disabled")

    @staticmethod
    def semantic_search(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("RAG index disabled")


class _UnavailableEmbeddings:
    @staticmethod
    def embed_documents(*_args: Any, **_kwargs: Any) -> list[list[float]]:
        raise RuntimeError("RAG embeddings disabled")


def get_retrieval_service(mode: Literal["search", "discover", "recommend"]) -> RagRetrievalService:
    """按开关提供真实索引或无网络的 Business 回退服务。"""
    fallback = _business_fallback(mode)
    if not settings.rag_enabled:
        return RagRetrievalService(_UnavailableIndex(), _UnavailableEmbeddings(), business_search=fallback)
    client = redis.Redis.from_url(settings.effective_rag_redis_url)
    return RagRetrievalService(
        RedisSubjectIndex(client),
        DashScopeEmbeddingClient(settings.dashscope_api_key),
        business_search=fallback,
    )


def _business_fallback(mode: Literal["search", "discover", "recommend"]):
    def lookup(query: RetrievalQuery, *, token: str | None) -> dict | list:
        if mode == "search":
            text = query.semantic_query or " ".join(query.keywords)
            return call_api("GET", "/api/client/subjects/search", params={"q": text, "page": 1, "size": _MAX_CANDIDATES}, token=token)
        if mode == "discover" and query.year_from == query.year_to and query.year_from and query.quarter:
            return call_api(
                "GET",
                "/api/client/subjects/season",
                params={"year": query.year_from, "quarter": query.quarter, "page": 1, "size": _MAX_CANDIDATES},
                token=token,
            )
        return call_api(
            "GET",
            "/api/client/subjects",
            params={"sort": "collectionTotal", "order": "desc", "page": 1, "size": _MAX_CANDIDATES},
            token=token,
        )

    return lookup


def _run(
    query: RetrievalQuery,
    *,
    mode: Literal["search", "discover", "recommend"],
    user: UserInfo | None = None,
    include_preference: bool = False,
) -> list[dict[str, Any]]:
    preference: UserPreference | None = None
    personalization_missing = False
    if include_preference and user is not None and settings.rag_enabled:
        preference, personalization_missing = _load_preference(user)
        if preference is not None:
            query = query.model_copy(update={"exclude_subject_ids": list(preference.exclude_subject_ids)})
    try:
        result = get_retrieval_service(mode).retrieve(
            query,
            mode,
            token=user.token if user is not None else None,
            preference=preference,
            personalization_missing=personalization_missing,
        )
    except Exception:
        return []
    if not result.available:
        return []
    return [_compact(item) for item in result.items[:_MAX_CANDIDATES]]


@tool
@tool_call_status(display_name="RAG 搜索番剧")
def rag_search_subjects(
    semantic_query: str,
    user: Annotated[UserInfo | None, InjectedState("user")] = None,
) -> list[dict[str, Any]]:
    """按番名、别名和自然语言语义检索目录；返回带 subjectId 的权威候选。"""
    try:
        keyword = [semantic_query] if len(semantic_query.strip()) <= 48 else []
        query = RetrievalQuery(semantic_query=semantic_query, keywords=keyword)
    except (ValidationError, ValueError):
        return []
    return _run(query, mode="search", user=user)


@tool
@tool_call_status(display_name="RAG 发现番剧")
def rag_discover_subjects(
    semantic_query: str = "",
    year_from: int | None = None,
    year_to: int | None = None,
    quarter: Literal["spring", "summer", "autumn", "winter"] | None = None,
    score_min: float | None = None,
    rating_total_min: int | None = None,
    meta_tags: list[str] | None = None,
    air_status: Literal["UPCOMING", "AIRING", "FINISHED"] | None = None,
    user: Annotated[UserInfo | None, InjectedState("user")] = None,
) -> list[dict[str, Any]]:
    """优先按年份、季度、评分、标签和播出状态发现符合条件的目录番剧。"""
    try:
        query = RetrievalQuery(
            semantic_query=semantic_query,
            year_from=year_from,
            year_to=year_to,
            quarter=quarter,
            score_min=score_min,
            rating_total_min=rating_total_min,
            meta_tags=meta_tags or [],
            air_status=air_status,
        )
    except (ValidationError, ValueError):
        return []
    return _run(query, mode="discover", user=user)


@tool
@tool_call_status(display_name="RAG 个性化推荐")
def rag_recommend_subjects(
    semantic_query: str = "热门动画",
    meta_tags: list[str] | None = None,
    user: Annotated[UserInfo | None, InjectedState("user")] = None,
) -> list[dict[str, Any]]:
    """基于当前问题和已登录用户的收藏画像推荐未收藏的目录番剧。"""
    try:
        query = RetrievalQuery(semantic_query=semantic_query or "热门动画", meta_tags=meta_tags or [])
    except (ValidationError, ValueError):
        return []
    return _run(query, mode="recommend", user=user, include_preference=True)


def _load_preference(user: UserInfo) -> tuple[UserPreference | None, bool]:
    try:
        response = call_api("GET", "/api/client/collections", params={"page": 1, "size": 100}, token=user.token)
    except Exception:
        return None, False
    if isinstance(response, Mapping) and response.get("error"):
        return None, False
    items = _collection_items(response)
    if not items:
        return None, True
    try:
        client = redis.Redis.from_url(settings.effective_rag_redis_url)
        profile = UserProfileService(client, vector_lookup=_profile_vector).get_or_build(user, items)
    except Exception:
        return None, True
    return profile, profile is None


def _collection_items(response: Any) -> list[CollectionItem]:
    rows = response.get("content", response.get("items", [])) if isinstance(response, Mapping) else response
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    items: list[CollectionItem] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        subject = row.get("subject") if isinstance(row.get("subject"), Mapping) else {}
        subject_id = row.get("subjectId", subject.get("id"))
        try:
            items.append(CollectionItem(int(subject_id), int(row.get("type")), row.get("rate"), row.get("epStatus")))
        except (TypeError, ValueError):
            continue
    return items


def _profile_vector(subject_id: int) -> Sequence[float] | None:
    try:
        raw = redis.Redis.from_url(settings.effective_rag_redis_url).hget(
            f"rag:subject:{settings.rag_index_version}:{subject_id}", "vector"
        )
    except Exception:
        return None
    if not isinstance(raw, bytes) or len(raw) != _VECTOR_BYTES:
        return None
    vector = array("f")
    vector.frombytes(raw)
    return list(vector) if all(math.isfinite(value) for value in vector) else None


def _compact(candidate: RetrievalCandidate) -> dict[str, Any]:
    details = candidate.details if isinstance(candidate.details, Mapping) else {}
    return {
        "subjectId": candidate.subject_id,
        "name": str(details.get("nameCn") or details.get("name") or candidate.title),
        "score": _number(details.get("score")),
        "ratingTotal": _integer(details.get("ratingTotal")),
        "matchedTags": _evidence_values(details, "tags", "metaTags", "trustedTags"),
        "matchedCredits": _evidence_values(details, "credits", "staff", "persons"),
        "retrievalReason": candidate.retrieval_reason,
    }


def _evidence_values(details: Mapping[str, Any], *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        raw = details.get(key)
        if isinstance(raw, str):
            values.append(raw)
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            for item in raw:
                value = (item.get("name") or item.get("nameCn") or item.get("personName")) if isinstance(item, Mapping) else item
                if value is not None and str(value).strip():
                    values.append(str(value).strip())
    return list(dict.fromkeys(values))[:8]


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _integer(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None
