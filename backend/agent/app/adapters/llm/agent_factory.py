import logging

from langchain_deepseek import ChatDeepSeek

from app.agent.ports import AgentChatModelSlot
from app.admin.ports import ModelConfigRepository
from app.config import ResolvedLlmProviderConfig, Settings, resolve_llm_provider

logger = logging.getLogger(__name__)

def create_llm(*, provider: str, model: str, temperature: float, api_key: str,
               max_tokens: int, base_url: str | None = None,
               reasoning_effort: str = "high"):
    """按已解析的 provider 创建供应商客户端。

    目前只有 DeepSeek（官方 OpenAI 兼容端点）。百炼对话模型已移除：百炼的
    ``enable_thinking`` / ``thinking_budget`` 是 qwen3 专有参数，DeepSeek 用
    ``reasoning_effort`` + ``extra_body.thinking``，两者不可互换。

    ``reasoning_content`` 由 ``ChatDeepSeek._convert_chunk_to_generation_chunk``
    自行写入 ``additional_kwargs``，无需额外补丁。
    """
    if provider != "deepseek":
        raise ValueError(f"不支持的 LLM provider: {provider!r}；仅支持 deepseek")
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
        reason_effort = runtime.get("reasoningEffort", resolved.reasoning_effort)
        return create_llm(
            provider=resolved.provider,
            model=model,
            temperature=resolved_temp,
            api_key=resolved.api_key.get_secret_value(),
            base_url=resolved.base_url,
            max_tokens=max_tokens,
            reasoning_effort=reason_effort,
        )
