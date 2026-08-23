from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Category = Literal["title_alias", "semantic", "filters", "personalization", "safety_failure"]


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    category: Category
    query: str
    expectedSubjectIds: tuple[int, ...] = Field(default_factory=tuple)
    forbiddenSubjectIds: tuple[int, ...] = Field(default_factory=tuple)
    required: bool
    expectedFallback: str | None = None
    expectedErrorType: str | None = None


class EvalReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_total: int
    required_passed: int
    mrr_at_10: float
    recall_at_20: float
    ndcg_at_10: float
    valid_subject_id_ratio: float
    failures: tuple[str, ...] = ()
