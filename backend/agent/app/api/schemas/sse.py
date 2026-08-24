import json
import time
from enum import Enum

from pydantic import BaseModel, Field


class Content(BaseModel):
    text: str | None = None
    node: str | None = None
    parent_node: str | None = None
    state: str | None = None
    message: str | None = None
    result: str | None = None
    name: str | None = None
    arguments: str | None = None


class MessageType(str, Enum):
    ANSWER = "answer"
    THINKING = "thinking"
    FUNCTION_CALL = "function_call"
    STATUS = "status"


class AssistantResponse(BaseModel):
    content: Content = Field(default_factory=Content)
    type: MessageType = Field(default=MessageType.ANSWER)
    meta: dict | None = None
    is_end: bool = False
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))


def serialize_sse(payload: AssistantResponse) -> str:
    return (
        f"data: {json.dumps(payload.model_dump(mode='json', exclude_none=True), ensure_ascii=False)}\n\n"
    )
