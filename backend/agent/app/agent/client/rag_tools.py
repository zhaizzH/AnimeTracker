from __future__ import annotations

from typing import Annotated, Any, Literal

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from pydantic import Field, StrictInt, ValidationError


StrictEntityIds = Annotated[list[Annotated[StrictInt, Field(gt=0)]], Field(max_length=50)]

from app.chat.user import UserInfo
from app.agent.middleware import tool_call_status
from app.rag.schemas import RetrievalQuery
from app.rag.use_case import RetrieveSubjectsUseCase


def _anonymous_user() -> UserInfo:
    return UserInfo(user_id=0, username="", role="USER", token="")


def build_rag_tools(use_case: RetrieveSubjectsUseCase) -> list[Any]:
    @tool
    @tool_call_status(display_name="RAG 搜索番剧")
    def rag_search_subjects(
        semantic_query: str,
        person_ids: StrictEntityIds | None = None,
        character_ids: StrictEntityIds | None = None,
        actor_ids: StrictEntityIds | None = None,
        relation_subject_ids: StrictEntityIds | None = None,
        user: Annotated[UserInfo | None, InjectedState("user")] = None,
    ) -> list[dict[str, Any]]:
        """按番名、别名、自然语言语义和可选人物/角色/声优/关联条目 ID 检索。"""
        try:
            keyword = [semantic_query] if len(semantic_query.strip()) <= 48 else []
            query = RetrievalQuery(
                semantic_query=semantic_query,
                keywords=keyword,
                person_ids=person_ids or [],
                character_ids=character_ids or [],
                actor_ids=actor_ids or [],
                relation_subject_ids=relation_subject_ids or [],
            )
        except (ValidationError, ValueError):
            return []
        return _items(use_case.execute(query, mode="search", user=user or _anonymous_user()))

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
        person_ids: StrictEntityIds | None = None,
        character_ids: StrictEntityIds | None = None,
        actor_ids: StrictEntityIds | None = None,
        relation_subject_ids: StrictEntityIds | None = None,
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
                person_ids=person_ids or [],
                character_ids=character_ids or [],
                actor_ids=actor_ids or [],
                relation_subject_ids=relation_subject_ids or [],
            )
        except (ValidationError, ValueError):
            return []
        return _items(use_case.execute(query, mode="discover", user=user or _anonymous_user()))

    @tool
    @tool_call_status(display_name="RAG 个性化推荐")
    def rag_recommend_subjects(
        semantic_query: str = "热门动画",
        meta_tags: list[str] | None = None,
        person_ids: StrictEntityIds | None = None,
        character_ids: StrictEntityIds | None = None,
        actor_ids: StrictEntityIds | None = None,
        relation_subject_ids: StrictEntityIds | None = None,
        user: Annotated[UserInfo | None, InjectedState("user")] = None,
    ) -> list[dict[str, Any]]:
        """基于当前问题和已登录用户的收藏画像推荐未收藏的目录番剧。"""
        try:
            query = RetrievalQuery(
                semantic_query=semantic_query or "热门动画",
                meta_tags=meta_tags or [],
                person_ids=person_ids or [],
                character_ids=character_ids or [],
                actor_ids=actor_ids or [],
                relation_subject_ids=relation_subject_ids or [],
            )
        except (ValidationError, ValueError):
            return []
        return _items(use_case.execute(query, mode="recommend", user=user or _anonymous_user()))

    return [rag_search_subjects, rag_discover_subjects, rag_recommend_subjects]


def _items(result: dict) -> list[dict[str, Any]]:
    if not result.get("available"):
        return []
    items = result.get("items", [])
    return items if isinstance(items, list) else []
