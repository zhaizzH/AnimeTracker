import json

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, SystemMessage

from app.agent.state import AgentState
from app.config import AgentChatModelSlot, create_agent_chat_llm
from app.core.agent_runtime import agent_stream
from app.core.event_bus import emit_answer_delta, emit_thinking_delta
from app.core.middleware import build_tool_status_middleware
from app.core.prompt_sync import load_managed_prompt
from app.db.models import PendingAction


def _build_pending_context(pending: PendingAction) -> str:
    return (
        "\n\n【待确认动作】\n"
        "用户有一个追番进度更新等待确认。写入必须使用以下 previewId,不得要求用户提供或自行编造:\n"
        f"- 类型: {pending.type}\n"
        f"- previewId: {pending.preview_id}\n"
        f"- 过期时间: {pending.expires_at.isoformat()}\n"
        f"- 明细: {json.dumps(pending.summary, ensure_ascii=False)}\n"
        "若执行返回 PREVIEW_CHANGED,必须先向用户展示新预览并再次询问确认,不得直接执行。"
    )


def run_domain_agent(state, *, slot: AgentChatModelSlot, tools: list, prompt_key: str, prompt_path: str) -> dict:
    prompt = load_managed_prompt(prompt_key, prompt_path)
    pending = state.get("pending_action")
    if pending is not None:
        prompt += _build_pending_context(pending)
    agent = create_agent(
        model=create_agent_chat_llm(slot=slot),
        tools=tools,
        system_prompt=SystemMessage(content=prompt),
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
