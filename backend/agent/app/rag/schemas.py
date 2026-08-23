from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SubjectProfileSource(BaseModel):
    """构建向量档案所需的条目资料；动态字段仅供调用方携带。"""

    model_config = ConfigDict(frozen=True)

    title: str
    aliases: tuple[str, ...] = ()
    summary: str = ""
    meta_tags: tuple[str, ...] = ()
    trusted_tags: tuple[str, ...] = ()
    credits: tuple[str, ...] = ()
    relations: tuple[str, ...] = ()
    score: float | None = None
    air_date: str | None = None
    air_weekday: int | None = None
    eps: int | None = None


class SubjectProfile(BaseModel):
    """可嵌入的稳定档案及其内容版本。"""

    model_config = ConfigDict(frozen=True)

    text: str
    content_hash: str = Field(min_length=64, max_length=64)
    schema_version: str
