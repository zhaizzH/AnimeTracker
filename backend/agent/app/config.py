from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM
    dashscope_api_key: str = ""
    llm_model: str = "qwen3.7-max"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096

    # Server
    agent_host: str = "0.0.0.0"
    agent_port: int = 8090

    # Backend API — 去掉路径后缀，工具调用时自行拼接完整路径
    backend_base_url: str = "http://localhost:8080"

    # Database
    database_url: str = "sqlite:///agent.db"

    # Agent Runtime
    agent_max_iterations: int = 5

    # CORS (开发环境)
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
