from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI

from app.config import settings
from app.llm.models import create_llm


def _set_key(monkeypatch):
    monkeypatch.setattr(settings, "opencode_api_key", "sk-test")


def test_opencode_prefix_routes_to_openai_compatible(monkeypatch):
    _set_key(monkeypatch)
    llm = create_llm(model="opencode-go/kimi-k3", temperature=0.3, api_key="dash", max_tokens=512)
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "kimi-k3"  # 前缀被剥离
    assert llm.openai_api_base == "https://opencode.ai/zen/go/v1"
    assert llm.use_responses_api is not True


def test_opencode_anthropic_endpoint_strips_v1(monkeypatch):
    _set_key(monkeypatch)
    llm = create_llm(model="opencode-go/qwen3.8-max", temperature=0.3, api_key="dash", max_tokens=512)
    assert isinstance(llm, ChatAnthropic)
    assert llm.model == "qwen3.8-max"
    assert llm.anthropic_api_url == "https://opencode.ai/zen/go"


def test_opencode_responses_model_enabled(monkeypatch):
    _set_key(monkeypatch)
    llm = create_llm(model="opencode-go/gpt-5.6-luna", temperature=0.0, api_key="dash", max_tokens=512)
    assert isinstance(llm, ChatOpenAI)
    assert llm.use_responses_api is True


def test_opencode_unknown_model_defaults_to_openai(monkeypatch):
    _set_key(monkeypatch)
    llm = create_llm(model="opencode-go/some-future-model", temperature=0.3, api_key="dash", max_tokens=512)
    assert isinstance(llm, ChatOpenAI)


def test_provider_first_qwen3_does_not_get_dashscope_kwargs(monkeypatch):
    # 雷:qwen3.8-max 开头是 qwen3,绝不能误带 DashScope 专用的 enable_thinking
    _set_key(monkeypatch)
    llm = create_llm(model="opencode-go/qwen3.8-max", temperature=0.3, api_key="dash", max_tokens=512)
    assert isinstance(llm, ChatAnthropic)
    assert "enable_thinking" not in llm.model_kwargs


def test_dashscope_path_untouched():
    llm = create_llm(model="qwen-plus", temperature=0.3, api_key="dash", max_tokens=512)
    assert isinstance(llm, ChatTongyi)
    llm3 = create_llm(model="qwen3-max", temperature=0.3, api_key="dash", max_tokens=512, thinking_budget=1024)
    assert isinstance(llm3, ChatTongyi)
    assert llm3.model_kwargs["enable_thinking"] is True


def test_reasoning_patch_captures_reasoning_content():
    # 补丁:langchain-openai 默认丢弃 reasoning_content,打补丁后存入 additional_kwargs
    from langchain_openai.chat_models import base as _lc_base
    chunk = _lc_base._convert_delta_to_message_chunk(
        {"role": "assistant", "content": "", "reasoning_content": "思考增量"}, AIMessageChunk
    )
    assert chunk.additional_kwargs.get("reasoning_content") == "思考增量"
