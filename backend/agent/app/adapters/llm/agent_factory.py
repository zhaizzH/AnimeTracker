import logging
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessageChunk
from langchain_deepseek import ChatDeepSeek

from app.agent.ports import AgentChatModelSlot
from app.admin.ports import ModelConfigRepository
from app.config import ResolvedLlmProviderConfig, Settings, resolve_llm_provider

logger = logging.getLogger(__name__)


def _patch_chat_openai_reasoning():
    """langchain-openai 丢弃 OpenAI 兼容流式响应里的 reasoning_content,补丁把它存入 additional_kwargs。"""
    from langchain_openai.chat_models import base as _lc_base

    _orig = _lc_base._convert_delta_to_message_chunk

    def _patched(delta, default_class):
        chunk = _orig(delta, default_class)
        reasoning = delta.get("reasoning_content")
        if reasoning and isinstance(chunk, AIMessageChunk):
            ak = dict(chunk.additional_kwargs or {})
            ak["reasoning_content"] = reasoning
            chunk.additional_kwargs = ak
        return chunk

    _patched.__name__ = "patched_convert_delta_to_message_chunk"
    _lc_base._convert_delta_to_message_chunk = _patched
    logger.info("已应用 reasoning_content 增量捕获补丁（DeepSeek 与百炼共用此通道）")


_patch_chat_openai_reasoning()


def create_llm(*, provider: Literal["deepseek", "dashscope"], model: str, temperature: float,
               api_key: str, max_tokens: int, base_url: str | None = None,
               thinking_budget: int = 2048, reasoning_effort: str = "high"):
    """按已解析的 provider 创建对应供应商客户端。DeepSeek 与百炼均显式开启思考；百炼走 OpenAI 兼容端点。"""
    if provider == "deepseek":
        deepseek_kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "api_key": api_key,
            "reasoning_effort": reasoning_effort,
            "extra_body": {"thinking": {"type": "enabled"}},
        }
        if base_url:
            deepseek_kwargs["base_url"] = base_url
        return ChatDeepSeek(**deepseek_kwargs)
    # 百炼走 OpenAI 兼容端点：enable_thinking/thinking_budget 是非标准参数，
    # 必须经 extra_body 嵌套透传（摊平到顶层会被供应商忽略）。
    extra_body: dict = {}
    if model.startswith("qwen3"):
        extra_body["enable_thinking"] = True
        if thinking_budget:
            extra_body["thinking_budget"] = thinking_budget
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        streaming=True,
        # 显式设了 base_url 时 langchain-openai 不再自动开 stream_usage，
        # 不传则 usage_metadata 恒 None、token 日志退回全 None。
        stream_usage=True,
        temperature=temperature,
        max_tokens=max_tokens,
        extra_body=extra_body or None,
    )


class AgentLlmFactory:
    def __init__(self, settings: Settings, model_configs: ModelConfigRepository):
        self._settings = settings
        self._model_configs = model_configs

    @property
    def provider(self) -> str:
        return resolve_llm_provider(self._settings).provider

    def create(
        self,
        slot: AgentChatModelSlot,
        *,
        temperature: float | None = None,
        provider_config: ResolvedLlmProviderConfig | None = None,
    ):
        runtime = self._model_configs.get() or {}
        resolved = provider_config or resolve_llm_provider(self._settings)
        if slot is AgentChatModelSlot.CLIENT_ROUTE:
            model = runtime.get("modelRoute") or resolved.route_model
        else:
            model = runtime.get("model") or resolved.model
        resolved_temp = temperature if temperature is not None else runtime.get(
            "temperature", self._settings.llm_temperature
        )
        max_tokens = runtime.get("maxTokens") or self._settings.llm_max_tokens
        budget = runtime.get("thinkingBudget", self._settings.llm_thinking_budget)
        reason_effort = runtime.get("reasoningEffort", resolved.reasoning_effort)
        return create_llm(
            provider=resolved.provider,
            model=model,
            temperature=resolved_temp,
            api_key=resolved.api_key.get_secret_value(),
            base_url=resolved.base_url,
            max_tokens=max_tokens,
            thinking_budget=budget,
            reasoning_effort=reason_effort,
        )
