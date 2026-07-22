from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class SessionInfo(BaseModel):
    session_id: str
    title: str
    message_count: int
    created_at: datetime


class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[str] | None = None
    created_at: datetime


class SessionCreateRequest(BaseModel):
    session_id: str | None = None


class SessionCreateResponse(BaseModel):
    session_id: str


class DeleteResponse(BaseModel):
    message: str = "deleted"
