from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _AliasCompatModel(BaseModel):
    """蛇形 Python 字段 + 驼峰别名：构造用字段名，序列化/解析兼容后端驼峰 JSON。"""

    model_config = ConfigDict(populate_by_name=True)


class CollectionProgressPendingItem(_AliasCompatModel):
    subject_id: int = Field(alias="subjectId")
    subject_name: str = Field(alias="subjectName")
    current_ep_status: int = Field(alias="currentEpStatus")
    target_ep_status: int = Field(alias="targetEpStatus")


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


class WishlistPendingAction(BaseModel):
    type: Literal["ADD_TO_WISHLIST"]
    user_id: int
    expires_at: datetime
    items: list[WishlistPendingItem] = Field(default_factory=list)


PendingAction = Annotated[
    CollectionProgressPendingAction | WishlistPendingAction,
    Field(discriminator="type"),
]

_adapter = TypeAdapter(PendingAction)


def parse_pending_action_json(raw: str | bytes) -> PendingAction:
    """按 type 判别字段校验具体动作；未知/损坏数据抛 ValidationError，不交给模型猜测。"""
    return _adapter.validate_json(raw)
