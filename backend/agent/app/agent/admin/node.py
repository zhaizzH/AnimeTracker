from typing import Any

from langchain_core.messages import AIMessage

from app.agent.state import AgentState

_DENIED_MESSAGE = "管理功能正在开发中，请直接在管理后台操作。"


def admin_denied(state: AgentState) -> dict[str, Any]:
    user = state.get("user")
    username = user.username if user is not None else ""
    message = _DENIED_MESSAGE if not username else f"{username}，{_DENIED_MESSAGE}"
    return {"result": message, "messages": [AIMessage(content=message)]}
