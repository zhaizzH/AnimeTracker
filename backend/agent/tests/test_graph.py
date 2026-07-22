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
