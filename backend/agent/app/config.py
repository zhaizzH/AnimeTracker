from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.runtime_config import get_runtime_model_config
from app.llm.models import create_llm


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM — DashScope 百炼
    dashscope_api_key: str = ""
    dashscope_model: str = "qwen3.7-plus"
    dashscope_model_route: str = "qwen3.7-plus"

    # LLM — DeepSeek 官方直连
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_model_route: str = "deepseek-chat"

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
    """最终选定的 LLM 供应商配置，由 config.py 解析并下发，禁止从模型名前缀推断。"""
    provider: Literal["deepseek", "dashscope"]
    api_key: SecretStr
    model: str
    route_model: str
    base_url: str | None = None


def resolve_llm_provider(s: Settings) -> ResolvedLlmProviderConfig:
    """按确定优先级选择 LLM 供应商：DeepSeek 优先，其次 DashScope；都不配置时抛错。"""
    if s.deepseek_api_key:
        return ResolvedLlmProviderConfig(
            provider="deepseek",
            api_key=SecretStr(s.deepseek_api_key),
            model=s.deepseek_model,
            route_model=s.deepseek_model_route,
            base_url=s.deepseek_base_url,
        )
    if s.dashscope_api_key:
        return ResolvedLlmProviderConfig(
            provider="dashscope",
            api_key=SecretStr(s.dashscope_api_key),
            model=s.dashscope_model,
            route_model=s.dashscope_model_route,
        )
    raise ValueError("LLM API Key 未配置: 请设置 DEEPSEEK_API_KEY 或 DASHSCOPE_API_KEY")


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
