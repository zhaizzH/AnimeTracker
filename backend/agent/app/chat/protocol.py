from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SessionInfo:
    session_id: str
    title: Optional[str] = None
    message_count: int = 0
    created_at: str = ""


@dataclass
class ChatMessage:
    role: str  # 'user' | 'assistant'
    content: str
    tool_calls: Optional[str] = None  # JSON string
    created_at: Optional[str] = None


# Client → Server
@dataclass
class ClientMessage:
    type: str  # message | new_session | load_history | list_sessions | delete_session | pong
    session_id: Optional[str] = None
    content: Optional[str] = None


# Server → Client
@dataclass
class ServerToken:
    type: str = "token"
    session_id: Optional[str] = None
    content: str = ""

    def to_dict(self):
        return {"type": self.type, "session_id": self.session_id, "content": self.content}


@dataclass
class ServerDone:
    type: str = "done"
    session_id: Optional[str] = None
    full_content: str = ""
    tool_calls: list[str] = field(default_factory=list)

    def to_dict(self):
        return {"type": self.type, "session_id": self.session_id, "full_content": self.full_content, "tool_calls": self.tool_calls}


@dataclass
class ServerError:
    type: str = "error"
    session_id: Optional[str] = None
    message: str = ""

    def to_dict(self):
        return {"type": self.type, "session_id": self.session_id, "message": self.message}


@dataclass
class ServerSessionList:
    type: str = "session_list"
    sessions: list[dict] = field(default_factory=list)

    def to_dict(self):
        return {"type": self.type, "sessions": self.sessions}


@dataclass
class ServerHistory:
    type: str = "history"
    session_id: Optional[str] = None
    messages: list[dict] = field(default_factory=list)

    def to_dict(self):
        return {"type": self.type, "session_id": self.session_id, "messages": self.messages}


@dataclass
class ServerPing:
    type: str = "ping"

    def to_dict(self):
        return {"type": self.type}
