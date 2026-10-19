"""LLM 工厂的构造契约（不触网）。

对话模型现在只有 DeepSeek 一家。本文件钉住两件事：

1. **DeepSeek 的字段形态**：`max_tokens` 用旧名（DeepSeek 官方端点未换新字段）、
   思考经 `extra_body.thinking` 开启、`reasoning_effort` 透传。这些看着像笔误，
   但都是供应商契约，不得「修」。
2. **百炼对话模型确实已移除**：`provider="dashscope"` 必须明确报错，而不是静默
   回退到 DeepSeek——静默回退会让用户以为切到了百炼却在跑 DeepSeek。

另钉住 `reasoning_content` 的捕获路径：`ChatDeepSeek` 自己会在
`_convert_chunk_to_generation_chunk` 里写入 `additional_kwargs`，项目不需要
（也不再保留）额外的 monkey patch。
"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessageChunk
from langchain_deepseek import ChatDeepSeek

from app.adapters.llm.agent_factory import create_llm

def _deepseek(**overrides):
    kwargs = dict(
        provider="deepseek",
        model="deepseek-v4-flash",
        temperature=0.3,
        api_key="test-key",
        max_tokens=4096,
        base_url="https://api.deepseek.com",
        reasoning_effort="high",
    )
    kwargs.update(overrides)
    return create_llm(**kwargs)

class TestDeepSeekClient:
    def test_creates_deepseek_client(self):
        llm = _deepseek()
        assert isinstance(llm, ChatDeepSeek)
        assert llm.model_name == "deepseek-v4-flash"

    def test_thinking_enabled_via_extra_body(self):
        """思考走 `extra_body.thinking`，不是 `enable_thinking`（那是 qwen3 的参数）。"""
        llm = _deepseek()
        assert llm.extra_body == {"thinking": {"type": "enabled"}}

    def test_reasoning_effort_passed_through(self):
        assert _deepseek(reasoning_effort="max").reasoning_effort == "max"

    def test_base_url_omitted_when_not_configured(self):
        """未配 BASE_URL 时不得塞 `base_url=None`——交给 SDK 默认值。"""
        llm = _deepseek(base_url=None)
        assert llm.openai_api_base is None

class TestRequestPayload:
    def test_max_tokens_keeps_legacy_field_name(self):
        """DeepSeek 官方端点仍用 `max_tokens`；百炼才用 `max_completion_tokens`。

        两者不得统一——把这里改成 `max_completion_tokens` 会让 DeepSeek 收到未知字段。
        """
        payload = _deepseek()._get_request_payload("hi")
        assert payload["max_tokens"] == 4096
        assert "max_completion_tokens" not in payload

    def test_extra_body_survives_bind_tools(self):
        """思考开关与工具调用共存：绑工具后的 payload 仍须带 extra_body。

        `bind_tools` 返回的 Runnable 不会把 kwargs 合成进 `_get_request_payload`；
        真实调用路径是 LangChain 把 bound kwargs 合并传入，此处按该路径构造。
        """
        from langchain_core.tools import tool

        @tool
        def ping(x: int) -> int:
            """ping"""
            return x

        bound = _deepseek().bind_tools([ping])
        payload = bound._get_request_payload("hi", **bound.kwargs)
        assert payload["extra_body"] == {"thinking": {"type": "enabled"}}
        assert payload["tools"][0]["function"]["name"] == "ping"

class TestReasoningCapture:
    def test_deepseek_client_itself_captures_reasoning_content(self):
        """项目曾有一个 monkey patch 干这件事；实测 `ChatDeepSeek` 自己就会做。

        本用例是删除那个补丁的依据：不打任何补丁，reasoning 依然进 `additional_kwargs`。
        """
        llm = _deepseek()
        chunk = {
            "choices": [{"delta": {"reasoning_content": "思考中"}, "index": 0, "finish_reason": None}],
            "usage": None, "id": "x", "model": "deepseek-v4-flash", "created": 1,
            "object": "chat.completion.chunk",
        }
        generation = llm._convert_chunk_to_generation_chunk(chunk, AIMessageChunk, None)
        assert generation.message.additional_kwargs["reasoning_content"] == "思考中"

class TestDashScopeRemoved:
    def test_dashscope_provider_is_rejected(self):
        """百炼对话模型已移除：必须报错，不得静默回退到 DeepSeek。"""
        with pytest.raises(ValueError, match="仅支持 deepseek"):
            _deepseek(provider="dashscope")

    def test_dashscope_is_not_reachable_from_factory(self):
        """`DASHSCOPE_API_KEY` 仍存在，但只服务 RAG 嵌入，不再能创建对话模型。"""
        from app.config import Settings, resolve_llm_provider

        settings = Settings(
            _env_file=None,
            llm_provider="dashscope",
            dashscope_api_key="k",
            deepseek_api_key="k",
        )
        with pytest.raises(ValueError, match="仅支持 deepseek"):
            resolve_llm_provider(settings)
