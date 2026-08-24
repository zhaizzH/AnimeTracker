import json

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, SystemMessage

from app.admin.ports import PromptRepository
from app.agent.ports import AgentChatModelSlot, AgentLlmFactoryPort
from app.agent.state import AgentState
from app.agent.runtime import agent_stream
from app.chat.event_sink import emit_answer_delta, emit_thinking_delta
from app.core.middleware import build_tool_status_middleware
from app.shared.observability import llm_model_name
from app.chat.pending_action import PendingAction


def _build_pending_context(pending: PendingAction) -> str:
    if pending.type == "ADD_TO_WISHLIST":
        return (
            "\n\n【待确认动作】\n"
            "用户有待确认加入「想看」的番剧。执行必须使用系统注入的待确认条目,不得要求用户提供或自行编造:\n"
            f"- 类型: {pending.type}\n"
            f"- 过期时间: {pending.expires_at.isoformat()}\n"
            f"- 条目: {json.dumps([i.model_dump(by_alias=True) for i in pending.items], ensure_ascii=False)}\n"
        )
    preview_id = getattr(pending, "preview_id", None)
    items = getattr(pending, "items", [])
    return (
        "\n\n【待确认动作】\n"
        "用户有一个追番进度更新等待确认。写入必须使用以下 previewId,不得要求用户提供或自行编造:\n"
        f"- 类型: {pending.type}\n"
        f"- previewId: {preview_id}\n"
        f"- 过期时间: {pending.expires_at.isoformat()}\n"
        f"- 明细: {json.dumps([i.model_dump(by_alias=True) for i in items], ensure_ascii=False)}\n"
        "若执行返回 PREVIEW_CHANGED,必须先向用户展示新预览并再次询问确认,不得直接执行。"
    )


def run_domain_agent(
        state,
        *,
        slot: AgentChatModelSlot,
        tools: list,
        prompt_key: str,
        prompt_path: str,
        llm_factory: AgentLlmFactoryPort,
        prompt_repository: PromptRepository,
        include_pending_action: bool = False,
) -> dict:
    prompt = prompt_repository.get(prompt_key, prompt_path)
    pending = state.get("pending_action") if include_pending_action else None
    if pending is not None:
        prompt += _build_pending_context(pending)
    llm = llm_factory.create(slot=slot)
    model_name = llm_model_name(llm)
    agent = create_agent(
        model=llm,
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
        slot=slot.value,
        provider=llm_factory.provider,
        model=model_name,
    )
    text = stream["streamed_text"]
    return {"result": text, "messages": [AIMessage(content=text)]}
