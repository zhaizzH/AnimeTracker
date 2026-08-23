from __future__ import annotations

import math


def reciprocal_rank(expected: set[int], ranked: list[int], k: int = 10) -> float:
    return next((1.0 / rank for rank, sid in enumerate(ranked[:k], 1) if sid in expected), 0.0)


def recall_at_k(expected: set[int], ranked: list[int], k: int = 20) -> float:
    return len(expected.intersection(ranked[:k])) / len(expected) if expected else 1.0


def ndcg_at_k(expected: set[int], ranked: list[int], k: int = 10) -> float:
    if not expected:
        return 1.0
    dcg = sum(1.0 / math.log2(rank + 1) for rank, sid in enumerate(ranked[:k], 1) if sid in expected)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(k, len(expected)) + 1))
    return dcg / ideal if ideal else 0.0
