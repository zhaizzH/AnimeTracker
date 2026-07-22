from abc import ABC, abstractmethod
from app.db.models import Session, Message


class ChatStore(ABC):
    """存储抽象接口 — 当前 SQLite 实现，后续可切换 MySQL"""

    @abstractmethod
    def init_db(self): ...

    @abstractmethod
    def create_session(self, user_id: int, session_id: str, title: str = "新对话"): ...

    @abstractmethod
    def get_user_sessions(self, user_id: int) -> list[Session]: ...

    @abstractmethod
    def get_messages(self, session_id: str) -> list[Message]: ...

    @abstractmethod
    def save_message(self, session_id: str, role: str, content: str, tool_calls: str | None = None): ...

    @abstractmethod
    def delete_session(self, session_id: str, user_id: int): ...

    @abstractmethod
    def update_session_title(self, session_id: str, title: str): ...
