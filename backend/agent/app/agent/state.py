from typing import Any, TypedDict

from langgraph.graph import MessagesState

from app.db.models import PendingAction
from app.schemas.auth import UserInfo


class RoutingState(TypedDict):
    route_target: str


class AgentState(MessagesState, total=False):
    user: UserInfo
    routing: RoutingState
    current_question: str
    history_messages: list[Any]
    result: str
    session_id: str
    pending_action: PendingAction | None
    pending_preview_id: str | None
