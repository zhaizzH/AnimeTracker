"""检索评测的确定性契约模型。

Golden case 描述一条"用户查询 → 期望命中"的确定性映射；
runner 负责把实际召回结果与期望对比，产出可复现的指标。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class GoldenExpectation(BaseModel):
    """单条 golden case 的期望命中集合。

    expected_subject_ids 按相关性从高到低排列，用于 nDCG 计算。
    must_contain_all 表示无论排序如何，这些 ID 必须全部出现在候选中。
    """

    model_config = ConfigDict(frozen=True)

    expected_subject_ids: list[int] = Field(default_factory=list)
    must_contain_all: list[int] = Field(default_factory=list)
    hard_filters: dict[str, Any] = Field(default_factory=dict)


class GoldenCase(BaseModel):
    """一条确定性检索评测用例。

    category 用于按场景聚合指标；description 只供人类阅读。
    """

    model_config = ConfigDict(frozen=True)

    id: str
    category: Literal[
        "title_alias",
        "structured_filter",
        "subjective_semantic",
        "person_character",
        "series_relation",
        "negation",
        "degradation",
    ]
    description: str
    query: dict[str, Any]
    expectation: GoldenExpectation


class CaseResult(BaseModel):
    """单条 golden case 的实际评测结果。"""

    case_id: str
    category: str
    retrieved_ids: list[int]
    expected_ids: list[int]
    hit_ids: list[int]
    precision: float
    recall: float
    dcg: float
    ideal_dcg: float
    ndcg: float
    rr: float
    all_must_contain_hit: bool


class EvalReport(BaseModel):
    """整批 golden cases 的聚合指标。"""

    total_cases: int
    recall_at_k: float
    mrr_at_k: float
    ndcg_at_k: float
    hard_filter_accuracy: float
    per_category: dict[str, dict[str, float]]
    case_results: list[CaseResult]
