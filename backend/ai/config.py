"""
AnimeTracker AI Agent — 配置管理

从环境变量和 .env 文件读取配置。
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DashScope / LLM 配置
    DASHSCOPE_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen3.7-max"
    LLM_TEMPERATURE: float = 0.7

    # 后端 API 地址（Spring Boot）
    BACKEND_API_BASE: str = "http://localhost:8080"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # 会话存储类型: redis / sqlite
    SESSION_STORE: str = "redis"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
