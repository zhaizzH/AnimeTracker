"""
数据导入器配置

支持从环境变量或 .env 文件读取数据库连接信息。
"""

from pydantic_settings import BaseSettings


class ImporterSettings(BaseSettings):
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "anime_tracker"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"

    # Bangumi API 基础地址
    BANGUMI_API_BASE: str = "https://api.bgm.tv"

    # 请求间隔（秒），避免触发频率限制
    REQUEST_INTERVAL: float = 0.5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = ImporterSettings()
