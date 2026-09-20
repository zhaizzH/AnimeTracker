from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _AliasCompatModel(BaseModel):
    """蛇形 Python 字段 + 驼峰别名：构造用字段名，序列化/解析兼容后端驼峰 JSON。"""

    model_config = ConfigDict(populate_by_name=True)


class CollectionProgressPendingItem(_AliasCompatModel):
    subject_id: int = Field(alias="subjectId")
    subject_name: str = Field(alias="subjectName")
    current_ep_status: int | None = Field(alias="currentEpStatus")
    target_ep_status: int | None = Field(alias="targetEpStatus")


class CollectionProgressPendingAction(_AliasCompatModel):
    type: Literal["COLLECTION_PROGRESS_UPDATE"]
    preview_id: str
    user_id: int
    expires_at: datetime
    # items 别名 summary，保持既有 Redis JSON 键名兼容（统一 by_alias 序列化）
    items: list[CollectionProgressPendingItem] = Field(default_factory=list, alias="summary")


class WishlistPendingItem(_AliasCompatModel):
    subject_id: int = Field(alias="subjectId")
    subject_name: str = Field(alias="subjectName")


class WishlistPendingAction(_AliasCompatModel):
    type: Literal["ADD_TO_WISHLIST"]
    user_id: int
    expires_at: datetime
    items: list[WishlistPendingItem] = Field(default_factory=list)


class SubjectResolutionCandidate(_AliasCompatModel):
    """按标题解析后经过权威校验的安全候选；只承载展示与来源绑定，不含写入参数。"""

    subject_id: int = Field(alias="subjectId")
    subject_name: str = Field(alias="subjectName")
    # 候选来源：BUSINESS（/subjects/search）或 RAG（rag_search_subjects 用例）
    match_source: str = Field(alias="matchSource")
    # 匹配类型：EXACT（唯一精确命中）或 CANDIDATE（安全候选，需用户选择）
    match_type: str = Field(alias="matchType")


class SubjectResolutionPendingAction(_AliasCompatModel):
    """多候选标题解析待选择状态：绑定用户、原始查询与权威候选，复用 600 秒 TTL。

    该状态只用于让用户在候选中选择，不代表任何写入确认；模型不能提交任意 subjectId。
    """

    type: Literal["SUBJECT_RESOLUTION"]
    user_id: int
    expires_at: datetime
    query: str = ""
    candidates: list[SubjectResolutionCandidate] = Field(default_factory=list)


PendingAction = Annotated[
    CollectionProgressPendingAction | WishlistPendingAction | SubjectResolutionPendingAction,
    Field(discriminator="type"),
]

_adapter = TypeAdapter(PendingAction)


def parse_pending_action_json(raw: str | bytes) -> PendingAction:
    """按 type 判别字段校验具体动作；未知/损坏数据抛 ValidationError，不交给模型猜测。"""
    return _adapter.validate_json(raw)
