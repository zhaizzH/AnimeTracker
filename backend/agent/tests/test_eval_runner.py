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


def test_live_mode_captures_called_tools(monkeypatch):
    """live 模式必须捕获 calledTools：带 calledTools 期望的 case 应离线断言通过。"""
    import os
    from unittest import mock

    from evals.adapters import EvalFakeChatModel, build_domain_responses, build_route_responses
    from evals.runner import run_live
    from evals import runner

    monkeypatch.setenv("ALLOW_LIVE_AGENT_EVAL", "true")
    monkeypatch.setattr(settings, "deepseek_api_key", "eval-key")
    monkeypatch.setattr(settings, "dashscope_api_key", "")

    case = EvalCase.model_validate({
        "id": "live-called-tools",
        "category": "recommendation",
        "input": "根据我的观看画像推荐几部番",
        "expect": {"routeTarget": "recommend_agent",
                   "calledTools": ["get_my_watch_profile"]},
    })

    def fake_llm(slot, **kwargs):
        if getattr(slot, "value", None) == "client_route":
            return EvalFakeChatModel(responses=build_route_responses(case.expect))
        return EvalFakeChatModel(responses=build_domain_responses(case.expect))

    with mock.patch.object(runner, "create_agent_chat_llm", fake_llm):
        report = run_live([case], sample=1)
    assert report.failed == 0
    assert report.total == 1


def test_live_mode_injects_explicit_provider_into_model_factory(monkeypatch):
    from unittest import mock

    from evals.adapters import EvalFakeChatModel, build_domain_responses, build_route_responses
    from evals import runner

    monkeypatch.setenv("ALLOW_LIVE_AGENT_EVAL", "true")
    monkeypatch.setattr(settings, "deepseek_api_key", "deepseek-key")
    monkeypatch.setattr(settings, "dashscope_api_key", "dashscope-key")
    case = EvalCase.model_validate({
        "id": "live-provider-override",
        "category": "recommendation",
        "input": "根据我的观看画像推荐几部番",
        "expect": {"routeTarget": "recommend_agent", "calledTools": ["get_my_watch_profile"]},
    })
    providers = []

    def fake_factory(slot, **kwargs):
        providers.append(kwargs["provider_config"].provider)
        if getattr(slot, "value", None) == "client_route":
            return EvalFakeChatModel(responses=build_route_responses(case.expect))
        return EvalFakeChatModel(responses=build_domain_responses(case.expect))

    with mock.patch.object(runner, "create_agent_chat_llm", fake_factory):
        report = runner.run_live([case], sample=1, provider_override="dashscope")

    assert report.failed == 0
    assert providers and set(providers) == {"dashscope"}


def test_live_mode_captures_pending_action_and_business_calls(monkeypatch):
    """live 模式必须捕获 pendingAction 与 businessCalls：进度预览 case 全断言通过。"""
    from unittest import mock

    from evals.adapters import EvalFakeChatModel, build_domain_responses, build_route_responses
    from evals.runner import run_live
    from evals import runner

    monkeypatch.setenv("ALLOW_LIVE_AGENT_EVAL", "true")
    monkeypatch.setattr(settings, "deepseek_api_key", "eval-key")
    monkeypatch.setattr(settings, "dashscope_api_key", "")

    case = EvalCase.model_validate({
        "id": "live-pending-action",
        "category": "collection_progress",
        "input": "本周截至昨日在看的都看完了",
        "expect": {
            "routeTarget": "recommend_agent",
            "calledTools": ["preview_weekly_collection_progress"],
            "pendingActionType": "COLLECTION_PROGRESS_UPDATE",
            "pendingActionOperation": "SET",
            "pendingSubjectIds": [101],
            "businessCalls": [["POST", "/api/client/collections/progress-preview"]],
        },
    })

    def fake_llm(slot, **kwargs):
        if getattr(slot, "value", None) == "client_route":
            return EvalFakeChatModel(responses=build_route_responses(case.expect))
        return EvalFakeChatModel(responses=build_domain_responses(case.expect))

    with mock.patch.object(runner, "create_agent_chat_llm", fake_llm):
        report = run_live([case], sample=1)
    assert report.failed == 0
