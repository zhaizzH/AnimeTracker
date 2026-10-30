"""图后路由边：intent 为空直连 END；三个 Domain agent 的 intent 都能到达 emitter；admin 不经 emitter。

用真实 `build_graph` + 真实 `graph.astream` 跑短路径（含嵌套图回传），不 mock 节点。
"""
import json

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.agent.dependencies import AgentDependencies
from app.agent.graph import build_graph
from app.agent.ports import AgentChatModelSlot
from app.chat.event_sink import reset_event_sink, set_event_sink
from app.chat.events import AgentEvent, AgentEventType
from app.chat.user import UserInfo

_NAVIGATION_ARGS = {"action": "open_profile"}

class _ScriptedModel(BaseChatModel):
    """respond= 路由 JSON；否则按「是否有 ToolMessage」决定调工具还是给答案。"""

    respond: dict | None = None
    tool_calls: list | None = None

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001, ANN201 - 测试替身
        assert tools, "Domain agent 必须带上工具"
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        if self.respond is not None:
            reply = AIMessage(content=json.dumps(self.respond))
        elif self.tool_calls and not any(isinstance(m, ToolMessage) for m in messages):
            reply = AIMessage(content="", tool_calls=self.tool_calls)
        else:
            reply = AIMessage(content="好了")
        return ChatResult(generations=[ChatGeneration(message=reply)])

class _LlmFactory:
    provider = "fake"

    def __init__(self, *, route_target: str | None) -> None:
        self.route_target = route_target

    def create(self, slot, *, temperature=None):  # noqa: ANN001, ANN201 - 测试替身
        if slot is AgentChatModelSlot.CLIENT_ROUTE:
            return _ScriptedModel(respond={"route_target": self.route_target or "search_agent"})
        if self.route_target is None:
            return _ScriptedModel()
        return _ScriptedModel(tool_calls=[{
            "name": "request_navigation",
            "args": _NAVIGATION_ARGS,
            "id": "call_1",
        }])

class _Business:
    def request(self, method, path, *, params=None, token=None, json_body=None):  # noqa: ANN001, ANN201
        return {"id": 84, "name": "测试番"}

class _PromptRepository:
    def get(self, key, path):  # noqa: ANN001, ANN201
        return "你是测试助手"

def _dependencies(*, route_target: str | None) -> AgentDependencies:
    return AgentDependencies(
        business=_Business(),
        retrieval=object(),
        llm_factory=_LlmFactory(route_target=route_target),
        prompt_repository=_PromptRepository(),
        import_service=object(),
    )

class _Collector:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def emit(self, event: AgentEvent) -> None:
        self.events.append(event)

async def _run(*, route_target: str | None, role: str = "USER") -> tuple[dict, list[AgentEvent]]:
    sink = _Collector()
    token = set_event_sink(sink)
    try:
        graph = build_graph(_dependencies(route_target=route_target))
        initial = {
            "user": UserInfo(user_id=2, username="t", role=role, token="tok"),
            "history_messages": [HumanMessage(content="打开个人中心")],
            "current_question": "打开个人中心",
            "routing": None,
            "result": "",
            "session_id": "s",
            "pending_action": None,
            "pending_preview_id": None,
            "write_confirmed": False,
            "navigation_intent": None,
        }
        final: dict = {}
        async for mode, chunk in graph.astream(initial, stream_mode=["values"]):
            if mode == "values" and isinstance(chunk, dict):
                final = chunk
    finally:
        reset_event_sink(token)
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
