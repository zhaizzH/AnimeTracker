import json
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.agent.client.state import AgentState
from app.agent.time_tool import _build_current_time_info
from app.config import AgentChatModelSlot, create_agent_chat_llm
from app.core.agent_runtime import agent_invoke
from app.core.prompt_sync import load_managed_prompt

_ALLOWED_TARGETS = ("search_agent", "discover_agent", "recommend_agent")

# 提示词含 JSON 示例花括号,不能走 str.format();仅替换占位符
def _build_gateway_prompt(state: AgentState) -> str:
    template = load_managed_prompt("client_gateway_prompt", "client/gateway_prompt.md")
    history = list(state.get("history_messages") or [])
    history_text = "\n".join(
        f"{'用户' if str(getattr(m, 'type', '')).lower() == 'human' else '助手'}: {getattr(m, 'content', '')}"
        for m in history
    )
    question = state.get("current_question") or (getattr(history[-1], "content", "") if history else "")
    return (template
            .replace("{date}", _build_current_time_info()["date"])
            .replace("{history}", history_text or "(无)")
            .replace("{question}", question))


def _resolve_routing_result(raw_payload: Any) -> dict[str, str]:
    """解析 gateway 结构化路由结果;非法输入抛 ValueError。"""
    if not isinstance(raw_payload, dict):
        raise ValueError("gateway payload must be a mapping")
    messages = raw_payload.get("messages") or []
    if not messages:
        raise ValueError("gateway payload messages cannot be empty")
    content = getattr(messages[-1], "content", None)
    if not isinstance(content, str):
        raise ValueError("gateway last message content must be a string")
    try:
        data = json.loads(content.strip())
    except json.JSONDecodeError as exc:
        raise ValueError("gateway returned invalid JSON") from exc
    target = str((data or {}).get("route_target") or "").strip()
    if target not in _ALLOWED_TARGETS:
        raise ValueError(f"unsupported route_target: {target}")
    return {"route_target": target}


def gateway_router(state: AgentState) -> dict[str, Any]:
    llm = create_agent_chat_llm(slot=AgentChatModelSlot.CLIENT_ROUTE)
    agent = create_agent(
        model=llm,
        system_prompt=SystemMessage(content=_build_gateway_prompt(state)),
    )
    result = agent_invoke(agent, list(state.get("history_messages") or []))
    return {"routing": _resolve_routing_result(result.payload)}
