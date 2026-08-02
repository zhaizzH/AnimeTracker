from abc import ABC, abstractmethod

from app.db.models import Message, Session


class ChatStore(ABC):
    """存储抽象接口 — Redis 实现"""

    @abstractmethod
    async def init_db(self): ...

    @abstractmethod
    async def create_session(self, user_id: int, session_id: str, title: str = "新对话"): ...

    @abstractmethod
    async def get_user_sessions(self, user_id: int) -> list[Session]: ...

    @abstractmethod
    async def get_messages(self, session_id: str) -> list[Message]: ...

    @abstractmethod
    async def save_message(self, session_id: str, role: str, content: str, tool_calls: str | None = None): ...

    @abstractmethod
    async def delete_session(self, session_id: str, user_id: int): ...

    @abstractmethod
    async def update_session_title(self, session_id: str, title: str): ...
