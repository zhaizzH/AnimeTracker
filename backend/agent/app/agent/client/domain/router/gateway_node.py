import json
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.agent.client.state import AgentState
from app.config import AgentChatModelSlot, create_agent_chat_llm
from app.core.agent.agent_runtime import agent_invoke
from app.core.prompt_sync import load_managed_prompt

_ALLOWED_TARGETS = ("search_agent", "discover_agent", "recommend_agent")


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
        system_prompt=SystemMessage(
            content=load_managed_prompt("client_gateway_prompt", "client/gateway_prompt.md")
        ),
        response_format={"type": "json_object"},
    )
    result = agent_invoke(agent, list(state.get("history_messages") or []))
    return {"routing": _resolve_routing_result(result.payload)}
