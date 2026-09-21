from typing import Any, TypedDict

from langgraph.graph import MessagesState

from app.chat.user import UserInfo
from app.chat.pending_action import PendingAction


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
    # 服务端写入确认标志：仅由 gateway_router 依据当前用户消息是否明确确认设置，
    # 模型无法通过工具参数篡改；execute_* 写入工具以此为硬门禁。默认 False。
    write_confirmed: bool
