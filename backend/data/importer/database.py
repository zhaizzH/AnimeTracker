"""
数据库引擎与会话管理。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models import Base


def create_db_url(settings) -> str:
    """从 ImporterSettings 构建 MySQL 连接 URL。"""
    return (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        "?charset=utf8mb4"
    )


engine = create_engine(
    create_db_url(settings),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

SessionFactory = sessionmaker(bind=engine, class_=Session)
