from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.runtime_config import get_runtime_model_config
from app.llm.models import create_llm


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="forbid")

    # LLM — DashScope 百炼
    dashscope_api_key: str = ""
    dashscope_model: str = "qwen3.7-plus"
    dashscope_model_route: str = "qwen3.7-plus"

    # LLM — DeepSeek 官方直连
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_model_route: str = "deepseek-chat"

    # LLM — 供应商显式选择（deepseek/dashscope；空则回退按 key 判断）
    llm_provider: str = ""
    # LLM — DeepSeek 思考强度（仅 deepseek 生效；low/high/max，默认 high）
    llm_reasoning_effort: str = "high"

    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096
    llm_thinking_budget: int = 2048

    # Server
    agent_host: str = "0.0.0.0"
    agent_port: int = 8090

    # Backend API
    backend_base_url: str = "http://localhost:8080"

    # JWT — 与 Spring Boot 共享签名秘钥,agent 本地验签,不回调业务后端
    jwt_secret: str = "dev-secret-key-not-for-production-use-change-it"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS (开发环境)
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()


@dataclass(frozen=True)
class ResolvedLlmProviderConfig:
    """最终选定的 LLM 供应商配置；由 LLM_PROVIDER 显式决定，未配置时按 key 兜底。"""
    provider: Literal["deepseek", "dashscope"]
    api_key: SecretStr
    model: str
    route_model: str
    reasoning_effort: str = "high"
    base_url: str | None = None


def _resolve_by_key(s: Settings) -> ResolvedLlmProviderConfig:
    """旧行为：按 API Key 存在与否选择（DeepSeek 优先）。用于 LLM_PROVIDER 未配置时兜底。"""
    if s.deepseek_api_key:
        return ResolvedLlmProviderConfig(
            provider="deepseek", api_key=SecretStr(s.deepseek_api_key),
            model=s.deepseek_model, route_model=s.deepseek_model_route,
            reasoning_effort=s.llm_reasoning_effort, base_url=s.deepseek_base_url,
        )
    if s.dashscope_api_key:
        return ResolvedLlmProviderConfig(
            provider="dashscope", api_key=SecretStr(s.dashscope_api_key),
            model=s.dashscope_model, route_model=s.dashscope_model_route,
            reasoning_effort=s.llm_reasoning_effort,
        )
    raise ValueError("LLM API Key 未配置: 请设置 DEEPSEEK_API_KEY 或 DASHSCOPE_API_KEY，或设置 LLM_PROVIDER")


def resolve_llm_provider(s: Settings) -> ResolvedLlmProviderConfig:
    provider = s.llm_provider.strip().lower()
    use = {"deepseek", "dashscope"}
    if provider:
        if provider not in use:
            raise ValueError(f"无效的 LLM_PROVIDER={s.llm_provider!r}；仅支持 deepseek|dashscope")
        if provider == "deepseek":
            if not s.deepseek_api_key:
                raise ValueError("LLM_PROVIDER=deepseek 但未配置 DEEPSEEK_API_KEY")
            return ResolvedLlmProviderConfig(
                provider="deepseek", api_key=SecretStr(s.deepseek_api_key),
                model=s.deepseek_model, route_model=s.deepseek_model,
                reasoning_effort=s.llm_reasoning_effort, base_url=s.deepseek_base_url,
            )
        # provider == "dashscope"
        if not s.dashscope_api_key:
            raise ValueError("LLM_PROVIDER=dashscope 但未配置 DASHSCOPE_API_KEY")
        return ResolvedLlmProviderConfig(
            provider="dashscope", api_key=SecretStr(s.dashscope_api_key),
            model=s.dashscope_model, route_model=s.dashscope_model,
            reasoning_effort=s.llm_reasoning_effort,
        )
    # LLM_PROVIDER 未配置 → 回退旧 key 判断，打 warning 提示迁移
    import logging
    logging.getLogger("app.config").warning(
        "LLM_PROVIDER 未配置，回退按 API Key 选择供应商；建议在 .env 显式设置 LLM_PROVIDER=deepseek|dashscope")
    return _resolve_by_key(s)


class AgentChatModelSlot(str, Enum):
    CLIENT_ROUTE = "client_route"
    CLIENT_SEARCH = "client_search"
    CLIENT_DISCOVER = "client_discover"
    CLIENT_RECOMMEND = "client_recommend"
    ADMIN_NODE = "admin_node"


# None 表示继承 settings.llm_temperature
# model 覆盖:gateway 只做路由分类,无需思考模型,用快速模型显著降低首段等待
_SLOT_DEFAULTS: dict[AgentChatModelSlot, dict[str, Any]] = {
    AgentChatModelSlot.CLIENT_ROUTE: {"temperature": 0.0},
    AgentChatModelSlot.CLIENT_SEARCH: {},
    AgentChatModelSlot.CLIENT_DISCOVER: {},
    AgentChatModelSlot.CLIENT_RECOMMEND: {},
    AgentChatModelSlot.ADMIN_NODE: {},
}


def create_agent_chat_llm(
        slot: AgentChatModelSlot,
        *,
        temperature: float | None = None,
        provider_config: ResolvedLlmProviderConfig | None = None,
):
    cfg = _SLOT_DEFAULTS[slot]
    rc = get_runtime_model_config() or {}
    resolved = provider_config or resolve_llm_provider(settings)
    if slot is AgentChatModelSlot.CLIENT_ROUTE:
        model = rc.get("modelRoute") or cfg.get("model") or resolved.route_model
    else:
        model = rc.get("model") or cfg.get("model") or resolved.model
    resolved_temp = temperature if temperature is not None else rc.get("temperature", cfg.get("temperature", settings.llm_temperature))
    max_tokens = rc.get("maxTokens") or settings.llm_max_tokens
    budget = rc.get("thinkingBudget", settings.llm_thinking_budget)
    return create_llm(
        provider=resolved.provider,
        model=model,
        temperature=resolved_temp,
        api_key=resolved.api_key.get_secret_value(),
        base_url=resolved.base_url,
        max_tokens=max_tokens,
        thinking_budget=budget,
    )
