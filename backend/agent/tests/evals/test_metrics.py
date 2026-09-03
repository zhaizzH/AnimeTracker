"""评测指标单元测试。"""

import pytest

from tests.evals.metrics import (
    all_must_contain_hit,
    dcg_at_k,
    ideal_dcg_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestPrecisionAtK:
    def test_all_hits(self):
        assert precision_at_k([1, 2, 3], [1, 2, 3], k=3) == 1.0

    def test_partial_hits(self):
        assert precision_at_k([1, 4, 3], [1, 2, 3], k=3) == pytest.approx(2 / 3)

    def test_no_hits(self):
        assert precision_at_k([4, 5, 6], [1, 2, 3], k=3) == 0.0

    def test_k_smaller_than_retrieved(self):
        assert precision_at_k([1, 4, 2, 5], [1, 2], k=2) == 0.5

    def test_empty_retrieved(self):
        assert precision_at_k([], [1, 2], k=5) == 0.0

    def test_k_zero(self):
        assert precision_at_k([1, 2], [1], k=0) == 0.0


class TestRecallAtK:
    def test_full_recall(self):
        assert recall_at_k([1, 2, 3], [1, 2], k=3) == 1.0

    def test_partial_recall(self):
        assert recall_at_k([1, 4], [1, 2], k=2) == 0.5

    def test_no_recall(self):
        assert recall_at_k([4, 5], [1, 2], k=2) == 0.0

    def test_empty_expected(self):
        assert recall_at_k([1, 2], [], k=5) == 1.0

    def test_empty_both(self):
        assert recall_at_k([], [], k=5) == 1.0


class TestReciprocalRank:
    def test_first_hit(self):
        assert reciprocal_rank([1, 2, 3], [1]) == 1.0

    def test_second_hit(self):
        assert reciprocal_rank([4, 1, 3], [1]) == 0.5

    def test_third_hit(self):
        assert reciprocal_rank([4, 5, 1], [1]) == pytest.approx(1 / 3)

    def test_no_hit(self):
        assert reciprocal_rank([4, 5, 6], [1]) == 0.0

    def test_empty_retrieved(self):
        assert reciprocal_rank([], [1]) == 0.0

    def test_empty_expected(self):
        assert reciprocal_rank([1, 2], []) == 0.0


class TestDCG:
    def test_perfect_order(self):
        retrieved = [1, 2, 3]
        expected = [1, 2, 3]
        gain = dcg_at_k(retrieved, expected, k=3)
        ideal = ideal_dcg_at_k(expected, k=3)
        assert gain == pytest.approx(ideal)

    def test_reversed_order(self):
        retrieved = [3, 2, 1]
        expected = [1, 2, 3]
        gain = dcg_at_k(retrieved, expected, k=3)
        ideal = ideal_dcg_at_k(expected, k=3)
        assert gain < ideal

    def test_no_hits(self):
        assert dcg_at_k([4, 5, 6], [1, 2, 3], k=3) == 0.0

    def test_empty(self):
        assert dcg_at_k([], [1, 2], k=5) == 0.0
        assert ideal_dcg_at_k([], k=5) == 0.0


class TestNDCG:
    def test_perfect_score(self):
        assert ndcg_at_k([1, 2, 3], [1, 2, 3], k=3) == 1.0

    def test_imperfect_score(self):
        score = ndcg_at_k([3, 1, 2], [1, 2, 3], k=3)
        assert 0.0 < score < 1.0

    def test_no_hits(self):
        assert ndcg_at_k([4, 5, 6], [1, 2, 3], k=3) == 0.0

    def test_empty_expected(self):
        assert ndcg_at_k([1, 2], [], k=5) == 0.0


class TestMustContain:
    def test_all_present(self):
        assert all_must_contain_hit([1, 2, 3, 4], [1, 3]) is True

    def test_missing_one(self):
        assert all_must_contain_hit([1, 2, 4], [1, 3]) is False

    def test_empty_must_contain(self):
        assert all_must_contain_hit([1, 2], []) is True

    def test_empty_retrieved(self):
        assert all_must_contain_hit([], [1]) is False
