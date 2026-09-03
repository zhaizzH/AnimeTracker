"""确定性检索评测指标计算。

所有函数均为纯函数，不依赖外部服务；输入为已排序的 retrieved_ids
与期望的 expected_ids，输出为 0~1 之间的浮点指标。
"""

from __future__ import annotations

import math


def precision_at_k(retrieved_ids: list[int], expected_ids: list[int], *, k: int) -> float:
    """在前 k 个召回结果中，命中的比例。"""
    if k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    expected_set = set(expected_ids)
    hits = sum(1 for sid in top_k if sid in expected_set)
    return hits / len(top_k)


def recall_at_k(retrieved_ids: list[int], expected_ids: list[int], *, k: int) -> float:
    """在期望命中的全部 ID 中，前 k 个召回覆盖了多少。"""
    if not expected_ids:
        return 1.0
    top_k = retrieved_ids[:k]
    expected_set = set(expected_ids)
    hits = sum(1 for sid in top_k if sid in expected_set)
    return hits / len(expected_set)


def reciprocal_rank(retrieved_ids: list[int], expected_ids: list[int]) -> float:
    """第一个命中出现的位置倒数；未命中为 0。"""
    if not expected_ids or not retrieved_ids:
        return 0.0
    expected_set = set(expected_ids)
    for rank, sid in enumerate(retrieved_ids, start=1):
        if sid in expected_set:
            return 1.0 / rank
    return 0.0


def dcg_at_k(retrieved_ids: list[int], expected_ids: list[int], *, k: int) -> float:
    """Discounted Cumulative Gain；expected_ids 的顺序代表相关性等级。

    使用线性相关性：命中位置 i 的 expected_ids[j] 得分为 len(expected_ids) - j。
    """
    if not expected_ids or not retrieved_ids or k <= 0:
        return 0.0
    relevance = {sid: max(1, len(expected_ids) - idx) for idx, sid in enumerate(expected_ids)}
    top_k = retrieved_ids[:k]
    result = 0.0
    for i, sid in enumerate(top_k, start=1):
        rel = relevance.get(sid, 0)
        if rel > 0:
            result += rel / math.log2(i + 1)
    return result


def ideal_dcg_at_k(expected_ids: list[int], *, k: int) -> float:
    """在完美排序下的 DCG 上界。"""
    if not expected_ids or k <= 0:
        return 0.0
    top_k = min(k, len(expected_ids))
    result = 0.0
    for i in range(1, top_k + 1):
        rel = len(expected_ids) - (i - 1)
        result += rel / math.log2(i + 1)
    return result


def ndcg_at_k(retrieved_ids: list[int], expected_ids: list[int], *, k: int) -> float:
    """Normalized DCG；IDCG 为 0 时返回 0。"""
    gain = dcg_at_k(retrieved_ids, expected_ids, k=k)
    ideal = ideal_dcg_at_k(expected_ids, k=k)
    if ideal <= 0:
        return 0.0
    return gain / ideal


def all_must_contain_hit(retrieved_ids: list[int], must_contain: list[int]) -> bool:
    """检查 must_contain 中的所有 ID 是否都出现在召回结果中。"""
    if not must_contain:
        return True
    retrieved_set = set(retrieved_ids)
    return all(sid in retrieved_set for sid in must_contain)
