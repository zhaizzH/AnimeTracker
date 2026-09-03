"""检索评测 runner：加载 golden cases，调用检索函数，聚合指标。

runner 不直接依赖 Redis 或 Business API；它接受一个可注入的 retrieve 函数，
便于在基线测试中使用 mock，在集成测试中使用真实服务。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from tests.evals.metrics import (
    all_must_contain_hit,
    dcg_at_k,
    ideal_dcg_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from tests.evals.schemas import CaseResult, EvalReport, GoldenCase


class RetrieveFn(Protocol):
    """检索函数协议：接受 query dict，返回按分数降序排列的 subject_id 列表。"""

    def __call__(self, query: dict[str, Any]) -> list[int]: ...


@dataclass(frozen=True)
class EvalConfig:
    """评测运行参数。"""

    k: int = 20
    mrr_k: int = 10
    ndcg_k: int = 10


def load_golden_cases(path: Path | str | None = None) -> list[GoldenCase]:
    """从 JSON 文件加载 golden cases；默认路径为本目录下的 golden_cases.json。"""
    if path is None:
        path = Path(__file__).parent / "golden_cases.json"
    else:
        path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [GoldenCase.model_validate(item) for item in raw]


def evaluate_case(
    case: GoldenCase,
    retrieve: RetrieveFn,
    *,
    config: EvalConfig | None = None,
) -> CaseResult:
    """对单条 golden case 运行检索并计算指标。"""
    cfg = config or EvalConfig()
    retrieved_ids = retrieve(case.query)

    expected_ids = case.expectation.expected_subject_ids
    must_contain = case.expectation.must_contain_all

    hit_ids = [sid for sid in retrieved_ids if sid in set(expected_ids)]
    prec = precision_at_k(retrieved_ids, expected_ids, k=cfg.k)
    rec = recall_at_k(retrieved_ids, expected_ids, k=cfg.k)
    gain = dcg_at_k(retrieved_ids, expected_ids, k=cfg.ndcg_k)
    ideal = ideal_dcg_at_k(expected_ids, k=cfg.ndcg_k)
    ndcg = ndcg_at_k(retrieved_ids, expected_ids, k=cfg.ndcg_k)
    rr = reciprocal_rank(retrieved_ids[: cfg.mrr_k], expected_ids)
    must_hit = all_must_contain_hit(retrieved_ids, must_contain)

    return CaseResult(
        case_id=case.id,
        category=case.category,
        retrieved_ids=retrieved_ids,
        expected_ids=expected_ids,
        hit_ids=hit_ids,
        precision=prec,
        recall=rec,
        dcg=gain,
        ideal_dcg=ideal,
        ndcg=ndcg,
        rr=rr,
        all_must_contain_hit=must_hit,
    )


def aggregate_report(
    case_results: list[CaseResult],
    *,
    config: EvalConfig | None = None,
) -> EvalReport:
    """聚合多条 case 结果为整体评测报告。"""
    cfg = config or EvalConfig()
    if not case_results:
        return EvalReport(
            total_cases=0,
            recall_at_k=0.0,
            mrr_at_k=0.0,
            ndcg_at_k=0.0,
            hard_filter_accuracy=0.0,
            per_category={},
            case_results=[],
        )

    total = len(case_results)
    avg_recall = sum(r.recall for r in case_results) / total
    avg_mrr = sum(r.rr for r in case_results) / total
    avg_ndcg = sum(r.ndcg for r in case_results) / total
    hard_correct = sum(1 for r in case_results if r.all_must_contain_hit) / total

    per_category: dict[str, dict[str, float]] = {}
    for result in case_results:
        cat = result.category
        if cat not in per_category:
            per_category[cat] = {"count": 0, "recall": 0.0, "mrr": 0.0, "ndcg": 0.0, "hard_accuracy": 0.0}
        bucket = per_category[cat]
        bucket["count"] += 1
        bucket["recall"] += result.recall
        bucket["mrr"] += result.rr
        bucket["ndcg"] += result.ndcg
        bucket["hard_accuracy"] += 1.0 if result.all_must_contain_hit else 0.0

    for bucket in per_category.values():
        count = bucket["count"]
        bucket["recall"] /= count
        bucket["mrr"] /= count
        bucket["ndcg"] /= count
        bucket["hard_accuracy"] /= count

    return EvalReport(
        total_cases=total,
        recall_at_k=avg_recall,
        mrr_at_k=avg_mrr,
        ndcg_at_k=avg_ndcg,
        hard_filter_accuracy=hard_correct,
        per_category=per_category,
        case_results=case_results,
    )


def run_eval(
    retrieve: RetrieveFn,
    *,
    cases: list[GoldenCase] | None = None,
    config: EvalConfig | None = None,
) -> EvalReport:
    """完整评测流程：加载 cases → 逐条评测 → 聚合报告。"""
    if cases is None:
        cases = load_golden_cases()
    cfg = config or EvalConfig()
    results = [evaluate_case(case, retrieve, config=cfg) for case in cases]
    return aggregate_report(results, config=cfg)
