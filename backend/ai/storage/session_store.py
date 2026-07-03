"""
会话存储 — 抽象基类与工厂

双实现策略：
- RedisSessionStore（主，TTL 7 天）
- SqliteSessionStore（回退，Redis 不可用时自动降级）

使用方式：
    store = await create_session_store()
    session_id = await store.create_session()
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class SessionStore(ABC):
    """会话存储抽象接口"""

    @abstractmethod
    async def create_session(self) -> str:
        ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict]:
        ...

    @abstractmethod
    async def add_message(self, session_id: str, role: str, content: str, tools_used: Optional[List[str]] = None):
        ...

    @abstractmethod
    async def get_messages(self, session_id: str) -> List[Dict]:
        ...

    @abstractmethod
    async def list_sessions(self) -> List[Dict]:
        ...

    @abstractmethod
    async def delete_session(self, session_id: str):
        ...

    @abstractmethod
    async def close(self):
        ...


async def create_session_store() -> SessionStore:
    """
    创建会话存储实例。
    优先尝试 Redis，不可用时静默回退 SQLite。
    """
    from config import settings

    if settings.SESSION_STORE == "redis":
        try:
            from storage.redis_store import RedisSessionStore
            store = RedisSessionStore()
            await store.initialize()
            return store
        except Exception:
            pass  # 回退到 SQLite

    from storage.sqlite_store import SqliteSessionStore
    store = SqliteSessionStore()
    await store.initialize()
    return store
