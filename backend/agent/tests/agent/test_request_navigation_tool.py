"""``request_navigation`` 工具：参数校验 + 零 IO + 必须带 ToolMessage 的 Command（design D2/D3）。"""
import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.types import Command

from app.agent.client.actions.turn_state import (
    mark_pending_resolved,
    reset_turn_state,
    set_turn_state,
)
from app.agent.client.navigation import build_request_navigation_tool
from app.chat.pending_events import (
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)

def _call(**kwargs) -> Command:
    tool_obj = build_request_navigation_tool()
    return tool_obj.func(tool_call_id="call_1", **kwargs)

def _assert_rejected(result: Command) -> dict:
    assert isinstance(result, Command)
    assert "navigation_intent" not in result.update
    message = result.update["messages"][0]
    assert isinstance(message, ToolMessage)
    payload = json.loads(message.content)
    assert payload["error"] is True
    assert payload["message"]
    return payload

def test_valid_navigation_returns_command_with_intent_and_tool_message() -> None:
    result = _call(action="open_profile")

    assert result.update["navigation_intent"] == {"action": "open_profile", "params": {}}
    message = result.update["messages"][0]
    assert isinstance(message, ToolMessage)
    assert message.tool_call_id == "call_1"
    assert json.loads(message.content)["ok"] is True

def test_unknown_action_is_rejected_without_writing_state() -> None:
    _assert_rejected(_call(action="open_admin_panel"))

def test_open_subject_requires_subject_id() -> None:
    _assert_rejected(_call(action="open_subject", params={}))

def test_open_subject_rejects_non_positive_subject_id() -> None:
    _assert_rejected(_call(action="open_subject", params={"subjectId": 0}))

def test_year_out_of_range_is_rejected() -> None:
    _assert_rejected(_call(action="open_anime_index", params={"year": 1800}))

def test_sort_outside_enum_is_rejected() -> None:
    _assert_rejected(_call(action="open_anime_index", params={"sort": "popularity"}))

def test_weekday_out_of_range_is_rejected() -> None:
    _assert_rejected(_call(action="open_anime_index", params={"weekday": 7}))

def test_params_not_accepted_for_open_profile() -> None:
    _assert_rejected(_call(action="open_profile", params={"q": "x"}))

def test_valid_params_are_normalized_to_snake_case() -> None:
    result = _call(action="open_subject", params={"subjectId": 84})

    assert result.update["navigation_intent"] == {"action": "open_subject", "params": {"subject_id": 84}}

def test_tags_are_kept_as_list() -> None:
    result = _call(action="open_anime_index", params={"tags": ["科幻", "治愈"]})

    assert result.update["navigation_intent"]["params"] == {"tags": ["科幻", "治愈"]}

def test_tool_is_not_registered_for_tool_status_events() -> None:
    """design D2：导航工具不加 @tool_call_status，不在工具面板显示「正在调用」。"""
    from app.agent.middleware import _REGISTERED

    build_request_navigation_tool()

    assert "request_navigation" not in _REGISTERED

class _ToolCallingModel(BaseChatModel):
    """第一次输出 tool_call，第二次输出最终答案。"""

    @property
    def _llm_type(self) -> str:
        return "fake-tool-calling"

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001, ANN201 - 测试替身
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        has_tool_result = any(isinstance(m, ToolMessage) for m in messages)
        if has_tool_result:
            reply = AIMessage(content="已经帮你打开了")
        else:
            reply = AIMessage(
                content="",
                tool_calls=[{
                    "name": "request_navigation",
                    "args": {"action": "open_profile"},
                    "id": "call_1",
                }],
            )
        return ChatResult(generations=[ChatGeneration(message=reply)])

def test_tool_runs_inside_real_create_agent_without_value_error() -> None:
    """design D2：只写 intent 不带 ToolMessage 会在工具节点抛 ValueError，这里锁住不抛。"""
    from langchain.agents import create_agent

    from app.agent.state import AgentState

    agent = create_agent(
        model=_ToolCallingModel(),
        tools=[build_request_navigation_tool()],
        state_schema=AgentState,
    )
    result = agent.invoke({"messages": [HumanMessage(content="打开个人中心")], "navigation_intent": None})

    assert result["navigation_intent"] == {"action": "open_profile", "params": {}}
    assert isinstance(result["messages"][-1], AIMessage)

# ---------------------------------------------------------------- 写入门控（design D1/D2）

class _WritePending:
    type = "ADD_TO_WISHLIST"
    user_id = 2
    expires_at = None

def _gated_call(*, gated: bool, pending) -> Command:  # noqa: ANN001 - 测试替身
    tool_obj = build_request_navigation_tool(gated=gated)
    return tool_obj.func(action="open_collections", tool_call_id="call_1", pending_action=pending)

def test_gated_tool_rejects_navigation_while_write_pending_unresolved() -> None:
    token = set_turn_state()
    try:
        result = _gated_call(gated=True, pending=_WritePending())
    finally:
        reset_turn_state(token)

    _assert_rejected(result)

def test_gated_tool_allows_navigation_after_write_resolved() -> None:
    """D1 核心修复：写成功后 state 里 pending 仍在，门控必须放行。"""
    token = set_turn_state()
    try:
        mark_pending_resolved()
        result = _gated_call(gated=True, pending=_WritePending())
    finally:
        reset_turn_state(token)

    assert result.update["navigation_intent"] == {"action": "open_collections", "params": {}}

def test_ungated_tool_ignores_write_pending() -> None:
    """search / discover 无写工具，不挂门控。"""
    token = set_turn_state()
    try:
        result = _gated_call(gated=False, pending=_WritePending())
    finally:
        reset_turn_state(token)

    assert result.update["navigation_intent"]["action"] == "open_collections"

def test_gated_tool_allows_pure_navigation_without_pending() -> None:
    token = set_turn_state()
    try:
        result = _gated_call(gated=True, pending=None)
    finally:
        reset_turn_state(token)

    assert result.update["navigation_intent"]["action"] == "open_collections"

def test_gated_tool_does_not_write_intent_or_state_when_rejected() -> None:
    token = set_turn_state()
    pending_token = set_pending_action_collector()
    try:
        result = _gated_call(gated=True, pending=_WritePending())
        pending_event = get_pending_action_event()
    finally:
        reset_pending_action_collector(pending_token)
        reset_turn_state(token)

    assert set(result.update) == {"messages"}, "被拒绝时只回 ToolMessage"
    assert pending_event is None
