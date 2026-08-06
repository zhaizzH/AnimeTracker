from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from app.agent.client.collections import get_my_collections
from app.agent.state import AgentState
from app.schemas.auth import UserInfo
from tests.fake_models import ToolCallingFakeModel


def test_full_turn_injects_user_and_calls_with_token(monkeypatch):
    captured = {}

    def fake_call(method, path, params=None, token=None):
        captured.update(method=method, path=path, params=params, token=token)
        return {"content": [{"id": 10, "subject": {"name": "我的番"}}], "total": 1}

    monkeypatch.setattr("app.agent.client.collections.call_api", fake_call)

    model = ToolCallingFakeModel(tool_name="get_my_collections")
    agent = create_agent(model=model, tools=[get_my_collections], state_schema=AgentState)
    agent.invoke({
        "messages": [HumanMessage(content="我的收藏")],
        "user": UserInfo(user_id=7, username="", role="USER", token="tok999"),
    })

    assert captured["token"] == "tok999"
    assert captured["path"] == "/api/user/collections"
