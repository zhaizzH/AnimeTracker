from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


SafeTerm = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=48, pattern=r"^[^\x00-\x1f]+$"),
]


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


class RetrievalQuery(BaseModel):
    """仅允许受控字段组成检索请求，不能携带原始 RediSearch 表达式。"""

    model_config = ConfigDict(extra="forbid")

    semantic_query: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=200, pattern=r"^[^\x00-\x1f]*$")
    ] = ""
    keywords: Annotated[list[SafeTerm], Field(max_length=8)] = Field(default_factory=list)
    year_from: int | None = Field(None, ge=1800, le=2200)
    year_to: int | None = Field(None, ge=1800, le=2200)
    quarter: Literal["spring", "summer", "autumn", "winter"] | None = None
    score_min: float | None = Field(None, ge=0, le=10)
    rating_total_min: int | None = Field(None, ge=0)
    meta_tags: Annotated[list[SafeTerm], Field(max_length=8)] = Field(default_factory=list)
    air_status: Literal["UPCOMING", "AIRING", "FINISHED"] | None = None
    exclude_subject_ids: Annotated[list[int], Field(max_length=100)] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_intent(self) -> "RetrievalQuery":
        has_filter = any(
            value is not None and value != []
            for value in (
                self.year_from,
                self.year_to,
                self.quarter,
                self.score_min,
                self.rating_total_min,
                self.meta_tags,
                self.air_status,
                self.exclude_subject_ids,
            )
        )
        if not (self.semantic_query or self.keywords or has_filter):
            raise ValueError("检索请求至少需要关键词、语义查询或结构化过滤条件")
        if self.year_from is not None and self.year_to is not None and self.year_to < self.year_from:
            raise ValueError("year_to 不能早于 year_from")
        return self
