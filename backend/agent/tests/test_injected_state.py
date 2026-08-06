from typing import Annotated, Any, Optional, TypedDict

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.schemas.auth import UserInfo
from tests.fake_models import ToolCallingFakeModel


class _State(TypedDict, total=False):
    messages: list[Any]
    user: UserInfo


_seen: dict = {}


@tool
def whoami(user: Annotated[Optional[UserInfo], InjectedState("user")] = None) -> dict:
    """test"""
    _seen["user"] = user
    return {"ok": True, "uid": user.user_id if user else None}


def test_injected_state_injects_user_from_graph_state():
    model = ToolCallingFakeModel(tool_name="whoami")
    agent = create_agent(model=model, tools=[whoami], state_schema=_State)
    agent.invoke({
        "messages": [HumanMessage(content="hi")],
        "user": UserInfo(user_id=42, username="", role="USER", token="tok123"),
    })
    assert _seen["user"] is not None
    assert _seen["user"].user_id == 42
    assert _seen["user"].token == "tok123"
