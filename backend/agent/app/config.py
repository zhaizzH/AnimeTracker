from enum import Enum
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.llm.models import create_llm


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM
    dashscope_api_key: str = ""
    llm_model: str = "qwen-plus"
    llm_model_route: str = "qwen-plus"
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


class AgentChatModelSlot(str, Enum):
    CLIENT_ROUTE = "client_route"
    CLIENT_SEARCH = "client_search"
    CLIENT_DISCOVER = "client_discover"
    CLIENT_RECOMMEND = "client_recommend"


# None 表示继承 settings.llm_temperature
# model 覆盖:gateway 只做路由分类,无需思考模型,用快速模型显著降低首段等待
_SLOT_DEFAULTS: dict[AgentChatModelSlot, dict[str, Any]] = {
    AgentChatModelSlot.CLIENT_ROUTE: {"temperature": 0.0, "model": settings.llm_model_route},
    AgentChatModelSlot.CLIENT_SEARCH: {},
    AgentChatModelSlot.CLIENT_DISCOVER: {},
    AgentChatModelSlot.CLIENT_RECOMMEND: {},
}


def create_agent_chat_llm(slot: AgentChatModelSlot, *, temperature: float | None = None):
    cfg = _SLOT_DEFAULTS[slot]
    resolved_temp = temperature if temperature is not None else cfg.get("temperature", settings.llm_temperature)
    return create_llm(
        model=cfg.get("model", settings.llm_model),
        temperature=resolved_temp,
        api_key=settings.dashscope_api_key,
        max_tokens=settings.llm_max_tokens,
        thinking_budget=settings.llm_thinking_budget,
    )
