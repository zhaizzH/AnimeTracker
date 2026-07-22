import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel

from app.graph.state import AgentState, SubAgentState
from app.schemas.auth import UserInfo


class TestAgentState:
    def test_defaults(self):
        user = UserInfo(user_id=1, username="test", role="USER")
        state = AgentState(messages=[], user=user)
        assert state.next_agent is None
        assert state.final_output == ""
        assert state.used_tools == []


class TestSubAgentState:
    def test_defaults(self):
        state = SubAgentState(messages=[])
        assert state.is_done is False

    def test_with_messages(self):
        msgs = [HumanMessage(content="hi")]
        state = SubAgentState(messages=msgs)
        assert len(state.messages) == 1


class TestSubAgentFactory:
    @pytest.mark.asyncio
    async def test_create_sub_agent(self):
        from app.graph.sub_agent import create_sub_agent
        from langchain_core.tools import tool

        @tool
        def fake_tool(x: int) -> int:
            """fake"""
            return x + 1

        llm = MagicMock()
        llm.bind_tools = MagicMock(return_value=llm)

        graph = create_sub_agent(
            name="test",
            tools=[fake_tool],
            system_prompt="test",
            llm=llm,
            max_iterations=3,
        )
        assert graph is not None
        assert hasattr(graph, "ainvoke")


@pytest.mark.asyncio
async def test_router_graph_default():
    from app.graph.graph import create_router_graph
    from unittest.mock import MagicMock
    from langchain_core.messages import AIMessage, HumanMessage
    from app.schemas.auth import UserInfo

    llm = MagicMock()
    # Use a real AIMessage so Pydantic accepts it in sub-agent state,
    # and tool_calls=[] (falsy) so the sub-agent finishes without calling tools.
    llm.ainvoke = AsyncMock(return_value=AIMessage(content="search"))
    llm.bind_tools = MagicMock(return_value=llm)

    store = MagicMock()
    store.get_messages = MagicMock(return_value=[])

    graph = create_router_graph(llm, MagicMock(agent_max_iterations=5), store)
    state = await graph.ainvoke({
        "messages": [HumanMessage(content="查一下钢炼", additional_kwargs={"session_id": "s1"})],
        "user": UserInfo(user_id=1, username="test", role="USER"),
        "next_agent": None,
        "final_output": "",
        "used_tools": [],
    })
    # Should route to search agent (via user_router)
    assert "final_output" in state
