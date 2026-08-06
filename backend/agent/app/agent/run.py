from langchain.agents import create_agent
from langchain_core.messages import AIMessage, SystemMessage

from app.agent.state import AgentState
from app.config import AgentChatModelSlot, create_agent_chat_llm
from app.core.agent_runtime import agent_stream
from app.core.event_bus import emit_answer_delta, emit_thinking_delta
from app.core.middleware import build_tool_status_middleware
from app.core.prompt_sync import load_managed_prompt


def run_domain_agent(state, *, slot: AgentChatModelSlot, tools: list, prompt_key: str, prompt_path: str) -> dict:
    agent = create_agent(
        model=create_agent_chat_llm(slot=slot),
        tools=tools,
        system_prompt=SystemMessage(content=load_managed_prompt(prompt_key, prompt_path)),
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
