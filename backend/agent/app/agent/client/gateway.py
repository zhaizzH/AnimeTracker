import json
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent.time_tool import _build_current_time_info
from app.config import AgentChatModelSlot, create_agent_chat_llm, resolve_llm_provider, settings
from app.core.agent_runtime import agent_invoke, extract_text
from app.core.observability import llm_model_name
from app.core.prompt_sync import load_managed_prompt

_ALLOWED_TARGETS = ("search_agent", "discover_agent", "recommend_agent")

# 支持确定性强制路由到 recommend_agent 的待确认动作类型
RECOMMEND_PENDING_ACTION_TYPES = {"COLLECTION_PROGRESS_UPDATE", "ADD_TO_WISHLIST"}

# 保守的确认词表: 仅精确匹配的简短肯定,拒绝否定词与含糊长文本
_CONFIRMATION_PHRASES = {
    "确认", "确定", "是", "是的", "好", "好的", "可以", "行",
    "执行", "按这个更新", "确认更新", "确认执行", "没问题",
}
_NEGATION_MARKERS = ("不", "没", "取消", "算了", "不要", "等等", "别", "否", "？", "?")


def _is_explicit_confirmation(text: str) -> bool:
    t = text.strip().rstrip("。.!！?？").strip()
    if not t:
        return False
    if any(m in t for m in _NEGATION_MARKERS):
        return False
    return t in _CONFIRMATION_PHRASES


def _resolve_forced_pending_route(state: AgentState) -> dict[str, str] | None:
    """存在支持的待确认动作且当前问题为明确确认时,确定性强制路由 recommend_agent。"""
    pending = state.get("pending_action")
    if pending is None or getattr(pending, "type", None) not in RECOMMEND_PENDING_ACTION_TYPES:
        return None
    if not _is_explicit_confirmation(state.get("current_question") or ""):
        return None
    return {"routing": {"route_target": "recommend_agent"}}

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
    # 部分模型返回 content 块列表,用 extract_text 统一抽取文本
    content = extract_text(messages[-1])
    if not content.strip():
        raise ValueError("gateway last message content is empty")
    try:
        data = json.loads(content.strip())
    except json.JSONDecodeError as exc:
        raise ValueError("gateway returned invalid JSON") from exc
    target = str((data or {}).get("route_target") or "").strip()
    if target not in _ALLOWED_TARGETS:
        raise ValueError(f"unsupported route_target: {target}")
    return {"route_target": target}


def gateway_router(state: AgentState) -> dict[str, Any]:
    forced = _resolve_forced_pending_route(state)
    if forced is not None:
        return forced
    llm = create_agent_chat_llm(slot=AgentChatModelSlot.CLIENT_ROUTE)
    model_name = llm_model_name(llm)
    agent = create_agent(
        model=llm,
        system_prompt=SystemMessage(content=_build_gateway_prompt(state)),
    )
    result = agent_invoke(
        agent,
        list(state.get("history_messages") or []),
        slot=AgentChatModelSlot.CLIENT_ROUTE.value,
        provider=resolve_llm_provider(settings).provider,
        model=model_name,
    )
    return {"routing": _resolve_routing_result(result.payload)}
