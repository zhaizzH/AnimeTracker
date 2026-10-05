import json
import re
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.agent.dependencies import AgentDependencies
from app.agent.ports import AgentChatModelSlot
from app.agent.state import AgentState
from app.agent.time_tool import _build_current_time_info
from app.agent.runtime import agent_invoke, extract_text
from app.shared.observability import llm_model_name

_ALLOWED_TARGETS = ("search_agent", "discover_agent", "recommend_agent")

# 支持确定性强制路由到 recommend_agent 的待确认动作类型
RECOMMEND_PENDING_ACTION_TYPES = {"COLLECTION_PROGRESS_UPDATE", "ADD_TO_WISHLIST", "SET_COLLECTION_TYPE"}

# 候选选择状态：任何用户回合都确定性交给 recommend_agent 处理选择/取消，
# 但明确确认词只对写入类待确认动作（ADD_TO_WISHLIST / SET_COLLECTION_TYPE / 进度更新）生效，
# 选择状态下的“确认”只是选择意图，不能被当成写入确认。
SUBJECT_RESOLUTION_PENDING_TYPE = "SUBJECT_RESOLUTION"

# 保守的确认词表: 仅精确匹配的简短肯定,拒绝否定词与含糊长文本
_CONFIRMATION_PHRASES = {
    "确认", "确定", "是", "是的", "好", "好的", "可以", "行",
    "执行", "按这个更新", "确认更新", "确认执行", "没问题",
}
_NEGATION_MARKERS = ("不", "取消", "算了", "不要", "等等", "别", "否")

# 写入意图 = 写入动词 + 可选填充词 + 收藏类型名。自然语言常在动词与类型名之间插词
# （如“添加到我的追番”“把这部设为在看”），连续短语匹配会漏，因此用正则。
_WRITE_VERBS = (
    r"(?:添加到|添加进|添加|标记为|标记成|标记|设置为|设为|设成|改成|改为|加入|加到|放入)"
)
_WRITE_FILLER = r"(?:我的|咱的|到|为|成|进|它|他|她|这个|这部|这些|那部)?"
_WRITE_TARGETS = r"(?:追番|在看|看过|搁置|抛弃|想看|愿望单)"
_WRITE_INTENT_RE = re.compile(_WRITE_VERBS + _WRITE_FILLER + _WRITE_TARGETS)

# 无类型名但仍是写入意图的旧短语（多指代推荐结果批量收藏）
_LEGACY_WRITE_PHRASES = ("收藏这些", "帮我收藏", "添加收藏", "开始追番")

_WRITE_NEGATION_MARKERS = ("不要", "别", "取消", "不想", "不")


def _is_explicit_confirmation(text: str) -> bool:
    t = text.strip().rstrip("。.!！?？").strip()
    if not t:
        return False
    # 先匹配完整肯定短语，再检查子串否定；
    # otherwise “没问题” is rejected because it contains “没”.
    if t in _CONFIRMATION_PHRASES:
        return True
    if any(m in t for m in _NEGATION_MARKERS):
        return False
    return False


def _negated_before(normalized: str, start: int) -> bool:
    prefix = normalized[max(0, start - 4):start]
    return any(prefix.endswith(marker) for marker in _WRITE_NEGATION_MARKERS)


def _is_explicit_recommendation_request(text: str) -> bool:
    """识别“写入/修改收藏”的确定性意图，用于强制路由 recommend_agent。

    只匹配 动词+类型名 的复合写入短语；纯查询即使含“追番/在看/收藏”也不匹配。
    """
    normalized = " ".join((text or "").split())
    if not normalized:
        return False
    for match in _WRITE_INTENT_RE.finditer(normalized):
        if not _negated_before(normalized, match.start()):
            return True
    for phrase in _LEGACY_WRITE_PHRASES:
        start = normalized.find(phrase)
        if start >= 0 and not _negated_before(normalized, start):
            return True
    return False


def _resolve_forced_pending_route(state: AgentState) -> dict[str, str] | None:
    """存在支持的待确认动作且当前问题为明确确认时,确定性强制路由 recommend_agent。"""
    pending = state.get("pending_action")
    pending_type = getattr(pending, "type", None)
    if pending_type is None:
        return None
    # 候选选择状态：任何回合都交给 recommend_agent；确认词不会触发写入，
    # 因为 execute_add_to_wishlist 只接受 ADD_TO_WISHLIST 待确认动作。
    if pending_type == SUBJECT_RESOLUTION_PENDING_TYPE:
        return {"routing": {"route_target": "recommend_agent"}}
    if pending_type not in RECOMMEND_PENDING_ACTION_TYPES:
        return None
    if not _is_explicit_confirmation(state.get("current_question") or ""):
        return None
    return {"routing": {"route_target": "recommend_agent"}}

# 提示词含 JSON 示例花括号,不能走 str.format();仅替换占位符
def _build_gateway_prompt(state: AgentState, dependencies: AgentDependencies) -> str:
    template = dependencies.prompt_repository.get("client_gateway_prompt", "client/gateway_prompt.md")
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
        raise ValueError("gateway 载荷必须是映射")
    messages = raw_payload.get("messages") or []
    if not messages:
        raise ValueError("gateway 载荷 messages 不能为空")
    # 部分模型返回 content 块列表,用 extract_text 统一抽取文本
    content = extract_text(messages[-1])
    if not content.strip():
        raise ValueError("gateway 最后一条消息 content 为空")
    try:
        data = json.loads(content.strip())
    except json.JSONDecodeError as exc:
        raise ValueError("gateway 返回的 JSON 无效") from exc
    target = str((data or {}).get("route_target") or "").strip()
    if target not in _ALLOWED_TARGETS:
        raise ValueError(f"不支持的 route_target: {target}")
    return {"route_target": target}


def build_gateway_router(dependencies: AgentDependencies):
    def gateway_router(state: AgentState) -> dict[str, Any]:
        # 服务端确定性判定“当前回合是否明确确认写入”；模型无法通过工具参数改写此标志。
        confirmed = _is_explicit_confirmation(state.get("current_question") or "")
        forced = _resolve_forced_pending_route(state)
        if forced is not None:
            return {**forced, "write_confirmed": confirmed}
        if _is_explicit_recommendation_request(state.get("current_question") or ""):
            return {"routing": {"route_target": "recommend_agent"}, "write_confirmed": confirmed}
        llm = dependencies.llm_factory.create(slot=AgentChatModelSlot.CLIENT_ROUTE)
        model_name = llm_model_name(llm)
        agent = create_agent(
            model=llm,
            system_prompt=SystemMessage(content=_build_gateway_prompt(state, dependencies)),
        )
        result = agent_invoke(
            agent,
            list(state.get("history_messages") or []),
            slot=AgentChatModelSlot.CLIENT_ROUTE.value,
            provider=dependencies.llm_factory.provider,
            model=model_name,
        )
        return {"routing": _resolve_routing_result(result.payload), "write_confirmed": confirmed}

    return gateway_router
