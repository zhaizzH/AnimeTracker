"""evals schema / runner / live provider 解析单元测试。"""

from pathlib import Path

import pytest
import yaml
from pydantic import SecretStr, ValidationError

from evals.runner import main, resolve_eval_provider
from evals.schema import EvalCase, load_cases
from app.config import settings


def write_yaml(tmp_path: Path, docs) -> Path:
    path = tmp_path / "cases.yaml"
    path.write_text(yaml.safe_dump(docs, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def test_duplicate_case_ids_are_rejected(tmp_path):
    path = write_yaml(tmp_path, [{"id": "same", "input": "a", "expect": {}},
                                 {"id": "same", "input": "b", "expect": {}}])
    with pytest.raises(ValueError, match="same"):
        load_cases([path])


def test_arbitrary_assertion_code_is_forbidden(tmp_path):
    with pytest.raises(ValidationError):
        EvalCase.model_validate({"id": "x", "input": "x", "expect": {"python": "os.remove"}})


def test_schema_rejects_unknown_top_level_field(tmp_path):
    with pytest.raises(ValidationError):
        EvalCase.model_validate({"id": "x", "input": "x", "expect": {}, "extraField": 1})


def test_load_cases_roundtrip(tmp_path):
    path = write_yaml(tmp_path, [{
        "id": "c1", "category": "routing", "input": "搜索", "required": True,
        "state": {"user": {"user_id": 1, "role": "USER"}},
        "expect": {"routeTarget": "search_agent"},
    }])
    cases = load_cases([path])
    assert len(cases) == 1
    assert cases[0].id == "c1"
    assert cases[0].expect.routeTarget == "search_agent"


def test_main_exit_zero_on_pass(tmp_path, capsys):
    path = write_yaml(tmp_path, [{"id": "ok-1", "category": "routing", "input": "搜索番剧",
                                  "expect": {"routeTarget": "search_agent"}}])
    assert main(["--cases", str(path)]) == 0
    out = capsys.readouterr().out
    assert "[PASS] ok-1" in out
    assert "1/1 passed" in out


def test_main_exit_one_on_assertion_failure(tmp_path, capsys):
    path = write_yaml(tmp_path, [{"id": "fail-1", "category": "routing", "input": "搜索番剧",
                                  "expect": {"errorCategory": "INTERNAL_ERROR"}}])
    assert main(["--cases", str(path)]) == 1
    out = capsys.readouterr().out
    assert "[FAIL] fail-1" in out


def test_main_exit_two_on_dataset_error(tmp_path, capsys):
    path = write_yaml(tmp_path, [{"id": "dup", "input": "a", "expect": {}},
                                 {"id": "dup", "input": "b", "expect": {}}])
    assert main(["--cases", str(path)]) == 2
    assert "dataset error" in capsys.readouterr().out


def test_resolve_eval_provider_deepseek_only(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "dk-secret-1")
    monkeypatch.setattr(settings, "dashscope_api_key", "")
    cfg = resolve_eval_provider(None)
    assert cfg.provider == "deepseek"
    assert isinstance(cfg.api_key, SecretStr)
    assert cfg.api_key.get_secret_value() == "dk-secret-1"


def test_resolve_eval_provider_dashscope_only(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    monkeypatch.setattr(settings, "dashscope_api_key", "qs-secret-2")
    cfg = resolve_eval_provider(None)
    assert cfg.provider == "dashscope"
    assert cfg.api_key.get_secret_value() == "qs-secret-2"


def test_resolve_eval_provider_prefers_deepseek(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "dk-secret-3")
    monkeypatch.setattr(settings, "dashscope_api_key", "qs-secret-3")
    assert resolve_eval_provider(None).provider == "deepseek"


def test_resolve_eval_provider_missing_keys_fail_without_leaking(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    monkeypatch.setattr(settings, "dashscope_api_key", "")
    with pytest.raises(ValueError) as exc:
        resolve_eval_provider(None)
    msg = str(exc.value)
    assert "LLM API Key" in msg
    assert "secret" not in msg  # 错误信息不含 Key 值


def test_provider_override_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    monkeypatch.setattr(settings, "dashscope_api_key", "qs-secret-4")
    with pytest.raises(ValueError, match="DeepSeek API Key"):
        resolve_eval_provider("deepseek")
    cfg = resolve_eval_provider("dashscope")
    assert cfg.provider == "dashscope"

    monkeypatch.setattr(settings, "deepseek_api_key", "dk-secret-4")
    monkeypatch.setattr(settings, "dashscope_api_key", "")
    with pytest.raises(ValueError, match="DashScope API Key"):
        resolve_eval_provider("dashscope")
    assert resolve_eval_provider("deepseek").provider == "deepseek"
