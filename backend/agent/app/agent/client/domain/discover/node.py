from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, SystemMessage

from app.agent.client.domain.discover.tools import discover_tools
from app.agent.client.domain.user_collections_tools import user_collections_tools
from app.agent.client.state import AgentState
from app.agent.tools.time_tool import get_current_time
from app.config import AgentChatModelSlot, create_agent_chat_llm
from app.core.agent.agent_event_bus import emit_answer_delta, emit_thinking_delta
from app.core.agent.agent_runtime import agent_stream
from app.core.agent.middleware import build_tool_status_middleware
from app.core.prompt_sync import load_managed_prompt


def discover_agent(state: AgentState) -> dict[str, Any]:
    llm = create_agent_chat_llm(slot=AgentChatModelSlot.CLIENT_DISCOVER)
    agent = create_agent(
        model=llm,
        tools=[*discover_tools, *user_collections_tools, get_current_time],
        system_prompt=SystemMessage(
            content=load_managed_prompt("client_discover_agent_prompt", "client/discover_agent_prompt.md")
        ),
        state_schema=AgentState,
        middleware=[build_tool_status_middleware()],
    )
    stream = agent_stream(
        agent,
        list(state.get("history_messages") or []),
        initial_state=state,
        on_model_delta=emit_answer_delta,
        on_thinking_delta=emit_thinking_delta,
    )
    text = stream["streamed_text"]
    return {"result": text, "messages": [AIMessage(content=text)]}
