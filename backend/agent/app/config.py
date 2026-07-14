import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # LLM
    dashscope_api_key: str = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""))
    llm_model: str = os.getenv("LLM_MODEL", "qwen3.7-max")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    # Server
    agent_host: str = os.getenv("AGENT_HOST", "0.0.0.0")
    agent_port: int = int(os.getenv("AGENT_PORT", "8090"))

    # Backend
    backend_base_url: str = os.getenv("BACKEND_BASE_URL", "http://localhost:8080/api/user")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///agent.db")

    # Agent runtime
    agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
    ws_heartbeat_interval: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))


settings = Settings()
