"""图后路由边：intent 为空直连 END；三个 Domain agent 的 intent 都能到达 emitter；admin 不经 emitter。

用真实 `build_graph` + 真实 `graph.astream` 跑短路径（含嵌套图回传），不 mock 节点。
"""
import json
from datetime import datetime, timedelta, timezone

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.agent.client.actions.turn_state import reset_turn_state, set_turn_state
from app.agent.dependencies import AgentDependencies
from app.agent.graph import build_graph
from app.agent.ports import AgentChatModelSlot
from app.chat.event_sink import reset_event_sink, set_event_sink
from app.chat.pending_action import WishlistPendingAction, WishlistPendingItem
from app.chat.events import AgentEvent, AgentEventType
from app.chat.user import UserInfo

_NAVIGATION_ARGS = {"action": "open_profile"}

class _ScriptedModel(BaseChatModel):
    """respond= 路由 JSON；否则按「是否有 ToolMessage」决定调工具还是给答案。"""

    respond: dict | None = None
    tool_calls: list | None = None
    # 多轮脚本：第 n 次生成用第 n 组 tool_calls（按已有 ToolMessage 计数）
    tool_calls_sequence: list[list] | None = None

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001, ANN201 - 测试替身
        assert tools, "Domain agent 必须带上工具"
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        if self.respond is not None:
            reply = AIMessage(content=json.dumps(self.respond))
        elif self.tool_calls_sequence is not None:
            done = sum(1 for m in messages if isinstance(m, ToolMessage))
            if done < len(self.tool_calls_sequence):
                reply = AIMessage(content="", tool_calls=self.tool_calls_sequence[done])
            else:
                reply = AIMessage(content="好了")
        elif self.tool_calls and not any(isinstance(m, ToolMessage) for m in messages):
            reply = AIMessage(content="", tool_calls=self.tool_calls)
        else:
            reply = AIMessage(content="好了")
        return ChatResult(generations=[ChatGeneration(message=reply)])

class _LlmFactory:
    provider = "fake"

    def __init__(self, *, route_target: str | None, sequence: list[list] | None = None) -> None:
        self.route_target = route_target
        self.sequence = sequence

    def create(self, slot, *, temperature=None):  # noqa: ANN001, ANN201 - 测试替身
        if slot is AgentChatModelSlot.CLIENT_ROUTE:
            return _ScriptedModel(respond={"route_target": self.route_target or "search_agent"})
        if self.route_target is None:
            return _ScriptedModel()
        if self.sequence is not None:
            return _ScriptedModel(tool_calls_sequence=self.sequence)
        return _ScriptedModel(tool_calls=[{
            "name": "request_navigation",
            "args": _NAVIGATION_ARGS,
            "id": "call_1",
        }])

class _Business:
    def request(self, method, path, *, params=None, token=None, json_body=None):  # noqa: ANN001, ANN201
        # 写入链路（/wishlist）与详情回查（/subjects/{id}）返回形态不同
        if method == "POST":
            return {"state": "ADDED"}
        return {"id": 84, "name": "测试番"}

class _PromptRepository:
    def get(self, key, path):  # noqa: ANN001, ANN201
        return "你是测试助手"

def _dependencies(
    *, route_target: str | None, sequence: list[list] | None = None
) -> AgentDependencies:
    return AgentDependencies(
        business=_Business(),
        retrieval=object(),
        llm_factory=_LlmFactory(route_target=route_target, sequence=sequence),
        prompt_repository=_PromptRepository(),
        import_service=object(),
    )

class _Collector:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def emit(self, event: AgentEvent) -> None:
        self.events.append(event)

async def _run(
    *,
    route_target: str | None,
    role: str = "USER",
    pending_action=None,  # noqa: ANN001 - PendingAction
    sequence: list[list] | None = None,
    question: str = "打开个人中心",
) -> tuple[dict, list[AgentEvent]]:
    sink = _Collector()
    token = set_event_sink(sink)
    # 镜像 ChatRunManager._drive：真实链路里 turn-bag 由 runner 安装，图内工具才有回合事实
    turn_token = set_turn_state()
    try:
        graph = build_graph(_dependencies(route_target=route_target, sequence=sequence))
        initial = {
            "user": UserInfo(user_id=2, username="t", role=role, token="tok"),
            "history_messages": [HumanMessage(content=question)],
            "current_question": question,
            "routing": None,
            "result": "",
            "session_id": "s",
            "pending_action": pending_action,
            "pending_preview_id": None,
            # write_confirmed 不能手塞：gateway_router 会用「当前问题是否明确确认」覆盖它，
            # 所以走写入链路时必须让 question 是确认词（见下面 execute 用例）。
            "write_confirmed": False,
            "navigation_intent": None,
        }
        final: dict = {}
        async for mode, chunk in graph.astream(initial, stream_mode=["values"]):
            if mode == "values" and isinstance(chunk, dict):
                final = chunk
    finally:
        reset_event_sink(token)
        reset_turn_state(turn_token)
    return final, sink.events

def _ui_actions(events: list[AgentEvent]) -> list[AgentEvent]:
    return [e for e in events if e.type is AgentEventType.UI_ACTION]

@pytest.mark.asyncio
async def test_no_intent_goes_straight_to_end() -> None:
    final, events = await _run(route_target=None)

    assert _ui_actions(events) == []
    assert final["navigation_intent"] is None

@pytest.mark.asyncio
@pytest.mark.parametrize("route_target", ["search_agent", "discover_agent", "recommend_agent"])
async def test_each_domain_agent_reaches_emitter(route_target: str) -> None:
    final, events = await _run(route_target=route_target)

    actions = _ui_actions(events)
    assert len(actions) == 1, f"{route_target} 的 navigation_intent 没有到达 emitter"
    assert actions[0].meta["path"] == "/profile"
    # emitter 执行后清空，下一轮不残留
    assert final["navigation_intent"] is None

@pytest.mark.asyncio
async def test_admin_path_never_touches_emitter() -> None:
    final, events = await _run(route_target="search_agent", role="ADMIN")

    assert _ui_actions(events) == []
    assert final["navigation_intent"] is None

# ---------------------------------------------------------------- 写入门控（design D1/D3）

_WRITE_PENDING = WishlistPendingAction(
    type="ADD_TO_WISHLIST",
    user_id=2,
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    items=[WishlistPendingItem(subject_id=84, subject_name="测试番")],
)

@pytest.mark.asyncio
async def test_recommend_agent_rejects_navigation_while_write_pending_unresolved() -> None:
    """预览阶段（pending 未结束且本回合无打标）模型误调导航必须被硬门控拦下。"""
    final, events = await _run(route_target="recommend_agent", pending_action=_WRITE_PENDING)

    assert _ui_actions(events) == [], "预览阶段的导航必须被硬门控拦下"
    assert final["navigation_intent"] is None

@pytest.mark.asyncio
async def test_recommend_agent_allows_navigation_after_cancel_marks_turn() -> None:
    """取消分支打标后，同一回合的导航必须放行（state 快照仍带 pending，锁 D1 修复）。"""
    final, events = await _run(
        route_target="recommend_agent",
        pending_action=_WRITE_PENDING,
        sequence=[
            [{"name": "cancel_add_to_wishlist", "args": {}, "id": "call_cancel"}],
            [{"name": "request_navigation", "args": _NAVIGATION_ARGS, "id": "call_nav"}],
        ],
    )

    actions = _ui_actions(events)
    assert len(actions) == 1, "打标后导航应放行"
    assert actions[0].meta["path"] == "/profile"

@pytest.mark.asyncio
async def test_recommend_agent_allows_navigation_after_execute_marks_turn() -> None:
    """写入执行成功的同一回合内导航必须放行（AC8 的图级断言，锁 D1 修复）。

    `state["pending_action"]` 全程是回合开始时的快照，仍是 ADD_TO_WISHLIST；
    放行完全依赖 execute 打通 `turn.pending_resolved`。
    """
    final, events = await _run(
        route_target="recommend_agent",
        pending_action=_WRITE_PENDING,
        # 「确认」既是写入硬门禁的来源（gateway 据此置 write_confirmed），
        # 也会确定性强制路由 recommend_agent（gateway 既有短路）
        question="确认",
        sequence=[
            [{"name": "execute_add_to_wishlist", "args": {}, "id": "call_exec"}],
            [{"name": "request_navigation", "args": _NAVIGATION_ARGS, "id": "call_nav"}],
        ],
    )

    actions = _ui_actions(events)
    assert len(actions) == 1, "写成功后的导航应放行，不能被 state 快照里的 pending 拦住"
    assert actions[0].meta["path"] == "/profile"
    assert final["navigation_intent"] is None
