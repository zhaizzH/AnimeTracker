"""LLM 工厂的构造契约（不触网）。

`ChatTongyi` 随 `langchain-community` sunset 迁到百炼 OpenAI 兼容端点后，
工厂产出的请求体形态变了三处，本文件把它们钉住：

1. `max_tokens` 被 `langchain-openai` 改名为 `max_completion_tokens`（供应商
   2026-04-20 起的新字段），不是笔误，不得「修」回旧名；
2. `enable_thinking` / `thinking_budget` 是非 OpenAI 标准参数，只能经
   `extra_body` 嵌套透传，摊平到顶层会被忽略；
3. `stream_usage=True` 必须显式传——显式设 `base_url` 后 langchain 不再自动开，
   漏了会让 token 日志从有值退回全 None。

另钉住迁移本身：导入工厂不得把已 sunset 的包拉回进程。
"""

from __future__ import annotations

import sys

import pytest
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

from app.adapters.llm.agent_factory import create_llm

_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def _dashscope(**overrides):
    kwargs = dict(
        provider="dashscope",
        model="qwen3.7-plus",
        temperature=0.3,
        api_key="test-key",
        max_tokens=4096,
        base_url=_BASE_URL,
        thinking_budget=2048,
    )
    kwargs.update(overrides)
    return create_llm(**kwargs)

class TestDashScopeClient:
    def test_creates_openai_compatible_client(self):
        llm = _dashscope()
        assert isinstance(llm, ChatOpenAI)
        assert llm.openai_api_base == _BASE_URL

    def test_qwen3_enables_thinking_in_extra_body(self):
        """思考开关必须落在 extra_body：顶层摊平会被供应商当作未知参数忽略。"""
        llm = _dashscope()
        assert llm.extra_body == {"enable_thinking": True, "thinking_budget": 2048}

    def test_non_qwen3_has_no_thinking(self):
        llm = _dashscope(model="qwen-max")
        assert llm.extra_body is None

    def test_zero_thinking_budget_omits_budget(self):
        llm = _dashscope(thinking_budget=0)
        assert llm.extra_body == {"enable_thinking": True}

    def test_stream_usage_enabled(self):
        llm = _dashscope()
        assert llm.streaming is True
        assert llm.stream_usage is True

    def test_missing_base_url_falls_back_to_compatible_endpoint(self):
        llm = _dashscope(base_url=None)
        assert llm.openai_api_base == _BASE_URL

class TestRequestPayload:
    def test_max_tokens_sent_as_max_completion_tokens(self):
        """百炼 2026-04-20 起改用新字段名；旧名已被标记废弃。"""
        payload = _dashscope()._get_request_payload("hi")
        assert payload["max_completion_tokens"] == 4096
        assert "max_tokens" not in payload

    def test_extra_body_survives_bind_tools(self):
        """思考开关与工具调用共存：绑工具后的 payload 仍须带 extra_body。

        注意 `bind_tools` 返回的 Runnable 不会把 kwargs 合成进 `_get_request_payload`；
        真实调用路径是 LangChain 把 bound kwargs 合并传入，此处按该路径构造。
        """
        @tool
        def ping(x: int) -> int:
            """ping"""
            return x

        bound = _dashscope().bind_tools([ping])
        payload = bound._get_request_payload("hi", **bound.kwargs)
        assert payload["extra_body"] == {"enable_thinking": True, "thinking_budget": 2048}
        assert payload["tools"][0]["function"]["name"] == "ping"

class TestDeepSeekBranch:
    def test_still_uses_deepseek_client(self):
        llm = create_llm(
            provider="deepseek",
            model="deepseek-v4-flash",
            temperature=0.3,
            api_key="test-key",
            max_tokens=4096,
            base_url="https://api.deepseek.com",
            reasoning_effort="high",
        )
        assert isinstance(llm, ChatDeepSeek)
        # DeepSeek 官方端点仍用旧字段名；只有百炼换了新名。
        assert llm._get_request_payload("hi")["max_tokens"] == 4096

class TestNoSunsetDependency:
    def test_import_does_not_load_community(self):
        """迁移的可执行断言：已 sunset 的包不得被工厂拉回进程。"""
        assert "langchain_community" not in sys.modules
        assert "langchain_classic" not in sys.modules
