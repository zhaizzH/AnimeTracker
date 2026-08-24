from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentEventType(str, Enum):
    ANSWER = "answer"
    THINKING = "thinking"
    FUNCTION_CALL = "function_call"
    STATUS = "status"
    END = "end"


@dataclass(frozen=True)
class AgentEvent:
    type: AgentEventType
    text: str | None = None
    state: str | None = None
    message: str | None = None
    name: str | None = None
    node: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
