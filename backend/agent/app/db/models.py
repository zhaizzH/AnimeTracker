from datetime import datetime

from pydantic import BaseModel, Field


class Session(BaseModel):
    session_id: str
    user_id: int
    title: str = "新对话"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    message_count: int = 0


class Message(BaseModel):
    id: int | None = None
    session_id: str
    role: str  # "user" | "assistant"
    content: str
    tool_calls: str | None = None  # JSON string
    created_at: datetime = Field(default_factory=datetime.now)
