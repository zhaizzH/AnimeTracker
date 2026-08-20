import pytest
from pydantic import ValidationError
from app.config import resolve_llm_provider, Settings


def test_default_provider_empty():
    s = Settings(_env_file=None)
    assert s.llm_provider == ""
    assert s.llm_reasoning_effort == "high"


def test_extra_forbid_rejects_unknown_env():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{"LLM_NONEXISTENT": "x"})


def test_provider_deepseek_wins_over_dashscope_key():
    s = Settings(_env_file=None,
                 llm_provider="deepseek", deepseek_model="deepseek-v4-flash",
                 deepseek_api_key="k-ds", dashscope_api_key="k-dsx")
    r = resolve_llm_provider(s)
    assert r.provider == "deepseek"
    assert r.model == "deepseek-v4-flash"
    assert r.reasoning_effort == "high"


def test_provider_dashscope_wins_even_if_deepseek_key_present():
    s = Settings(_env_file=None,
                 llm_provider="dashscope", dashscope_model="qwen3.7-plus",
                 deepseek_api_key="k-ds", dashscope_api_key="k-dsx")
    r = resolve_llm_provider(s)
    assert r.provider == "dashscope"


def test_empty_provider_falls_back_to_key():
    s = Settings(_env_file=None, llm_provider="", deepseek_api_key="k")
    r = resolve_llm_provider(s)
    assert r.provider == "deepseek"


def test_invalid_provider_raises():
    s = Settings(_env_file=None, llm_provider="aliyun", deepseek_api_key="k", dashscope_api_key="k2")
    try:
        resolve_llm_provider(s)
        assert False, "应抛出异常"
    except ValueError as e:
        assert "LLM_PROVIDER" in str(e)


def test_no_provider_no_key_raises():
    s = Settings(_env_file=None)
    try:
        resolve_llm_provider(s)
        assert False
    except ValueError:
        pass
