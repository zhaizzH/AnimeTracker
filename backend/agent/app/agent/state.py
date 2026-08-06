from typing import Any, TypedDict

from langgraph.graph import MessagesState

from app.schemas.auth import UserInfo


class RoutingState(TypedDict):
    route_target: str


class AgentState(MessagesState, total=False):
    user: UserInfo
    routing: RoutingState
    current_question: str
    history_messages: list[Any]
    result: str
