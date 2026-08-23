from __future__ import annotations

import math

from pathlib import Path
import pytest
from pydantic import ValidationError

from evals import runner
from evals.adapters import FakeEmbedding
from evals.schema import EvalCase, EvalReport


def test_eval_case_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        EvalCase.model_validate({
            "id": "strict", "category": "semantic", "query": "动画 1", "required": True,
            "unexpected": "not accepted",
        })


def test_fake_embedding_has_a_normalized_1024_dimension_vector():
    vector = FakeEmbedding().embed("科幻 治愈 动画")

    assert len(vector) == 1024
    assert math.isclose(sum(value * value for value in vector), 1.0)


def test_cli_returns_one_for_a_quality_gate_failure(monkeypatch):
    report = EvalReport(required_total=1, required_passed=0, mrr_at_10=0, recall_at_20=0, ndcg_at_10=0, valid_subject_id_ratio=1)
    monkeypatch.setattr(runner, "run_offline", lambda: report)
    monkeypatch.setattr(Path, "write_text", lambda *_args, **_kwargs: 0)

    assert runner.main(["--mode", "offline", "--output", "ignored.json", "--index-version", "v1"]) == 1


def test_cli_returns_two_for_invalid_dataset(monkeypatch):
    monkeypatch.setattr(runner, "run_offline", lambda: (_ for _ in ()).throw(runner.DatasetError("bad yaml")))

    assert runner.main(["--mode", "offline", "--output", "ignored.json", "--index-version", "v1"]) == 2
