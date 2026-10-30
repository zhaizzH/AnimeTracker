"""turn-bag（本回合已发生的事实）与写入后导航门控。

design D1/D2：门控不能单独读 `state["pending_action"]`——那是回合开始时的 Redis 快照，
写成功后不更新。必须与 `TurnState.pending_resolved` 联合判断。
"""
import pytest

from app.agent.client.actions.previewable import (
    Clear,
    ClearAction,
    Keep,
    PreviewableAction,
    Replace,
)
from app.agent.client.navigation import _navigation_gate
from app.agent.client.actions.turn_state import (
    TurnState,
    get_turn_state,
    mark_pending_resolved,
    reset_turn_state,
    set_turn_state,
)
from app.chat.pending_events import (
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.chat.user import UserInfo

USER = UserInfo(user_id=2, username="tester", role="USER", token="token")

def test_turn_state_is_absent_outside_a_turn() -> None:
    assert get_turn_state() is None

def test_reset_restores_absent_state() -> None:
    token = set_turn_state()
    assert get_turn_state() == TurnState()
    reset_turn_state(token)

    assert get_turn_state() is None

def test_mark_pending_resolved_sets_flag_for_current_turn() -> None:
    token = set_turn_state()
    try:
        mark_pending_resolved()
        turn = get_turn_state()
    finally:
        reset_turn_state(token)

    assert turn is not None
    assert turn.pending_resolved is True

def test_mark_outside_turn_is_noop() -> None:
    mark_pending_resolved()  # 不抛异常

    assert get_turn_state() is None

# ---------------------------------------------------------------- 打标点

WRITE_RESPONSE = {"succeeded": [{"subjectId": 84}], "skipped": [], "failed": []}

class _Pending:
    type = "ADD_TO_WISHLIST"
    user_id = 2
    expires_at = None  # require_confirmed_write: None 表示不过期

class _StubAction(PreviewableAction):
    """三条写链路共用的骨架替身：只关心基类的打标时序，不关心业务分类。"""

    pending_type = "ADD_TO_WISHLIST"

    def __init__(self, action: ClearAction, response: dict) -> None:
        self._action = action
        self._response = response

    def do_execute(self, *, pending, user):  # noqa: ANN001, ANN201 - 测试替身
        return None

    def classify_result(self, *, result, pending, user):  # noqa: ANN001, ANN201 - 测试替身
        return self._action, self._response

def test_execute_with_clear_marks_pending_resolved_and_keeps_response() -> None:
    token = set_turn_state()
    collector_token = set_pending_action_collector()
    try:
        response = _StubAction(Clear(), dict(WRITE_RESPONSE)).execute(
            pending=_Pending(), user=USER, write_confirmed=True
        )
        turn = get_turn_state()
    finally:
        reset_pending_action_collector(collector_token)
        reset_turn_state(token)

    assert response == WRITE_RESPONSE, "打标不得改变三条链路对模型可见的返回 dict"
    assert turn is not None and turn.pending_resolved is True

def test_execute_with_keep_does_not_mark_pending_resolved() -> None:
    token = set_turn_state()
    collector_token = set_pending_action_collector()
    try:
        _StubAction(Keep(), {"error": True, "message": "写入失败"}).execute(
            pending=_Pending(), user=USER, write_confirmed=True
        )
        turn = get_turn_state()
    finally:
        reset_pending_action_collector(collector_token)
        reset_turn_state(token)

    assert turn is not None and turn.pending_resolved is False, "基础设施错误要保留 pending 供重试"

def test_execute_rejected_by_write_guard_does_not_mark() -> None:
    token = set_turn_state()
    collector_token = set_pending_action_collector()
    try:
        rejected = _StubAction(Clear(), dict(WRITE_RESPONSE)).execute(
            pending=_Pending(), user=USER, write_confirmed=False
        )
        turn = get_turn_state()
    finally:
        reset_pending_action_collector(collector_token)
        reset_turn_state(token)

    assert rejected["error"] is True
    assert turn is not None and turn.pending_resolved is False

def test_execute_with_replace_does_not_mark() -> None:
    token = set_turn_state()
    collector_token = set_pending_action_collector()
    try:
        _StubAction(Replace(new_pending=_Pending()), {"state": "PREVIEW_CHANGED"}).execute(
            pending=_Pending(), user=USER, write_confirmed=True
        )
        turn = get_turn_state()
    finally:
        reset_pending_action_collector(collector_token)
        reset_turn_state(token)

    assert turn is not None and turn.pending_resolved is False, "预览被替换后仍需再次确认"

def test_cancel_marks_pending_resolved() -> None:
    token = set_turn_state()
    collector_token = set_pending_action_collector()
    try:
        result = _StubAction(Clear(), {}).cancel()
        turn = get_turn_state()
    finally:
        reset_pending_action_collector(collector_token)
        reset_turn_state(token)

    assert result == {"cancelled": True}
    assert turn is not None and turn.pending_resolved is True

# ---------------------------------------------------------------- 门控纯函数

class _Typed:
    def __init__(self, ptype: str) -> None:
        self.type = ptype

RESOLVED = TurnState(pending_resolved=True)
UNRESOLVED = TurnState()

@pytest.mark.parametrize(
    ("ptype", "turn", "allowed"),
    [
        (None, UNRESOLVED, True),  # 纯导航，无 pending
        ("ADD_TO_WISHLIST", UNRESOLVED, False),
        ("ADD_TO_WISHLIST", RESOLVED, True),  # D1 核心：写成功后放行
        ("SET_COLLECTION_TYPE", UNRESOLVED, False),
        ("SET_COLLECTION_TYPE", RESOLVED, True),
        ("COLLECTION_PROGRESS_UPDATE", UNRESOLVED, False),
        ("COLLECTION_PROGRESS_UPDATE", RESOLVED, True),
        ("SUBJECT_RESOLUTION", UNRESOLVED, False),  # 多候选未选完
        ("SUBJECT_RESOLUTION", RESOLVED, True),  # 选完并确认后不堵死
        ("SOME_FUTURE_TYPE", UNRESOLVED, True),  # 非写入类 pending 不拦导航
    ],
)
def test_gate_allows_only_when_no_write_pending_or_turn_resolved(
    ptype: str | None, turn: TurnState, allowed: bool
) -> None:
    pending = None if ptype is None else _Typed(ptype)

    result = _navigation_gate(pending=pending, turn=turn)

    assert (result is None) is allowed
    if not allowed:
        assert result is not None and result["error"] is True and result["message"]

def test_gate_rejects_write_pending_when_turn_is_absent() -> None:
    """无回合上下文（直接单测工具）时对写入类 pending 保守拒绝。"""
    result = _navigation_gate(pending=_Typed("ADD_TO_WISHLIST"), turn=None)

    assert result is not None and result["error"] is True

def test_write_pending_types_match_gateway_recommend_set() -> None:
    """写入门控的拒绝集必须与 gateway 的「确认后强制路由 recommend」集合一致。

    两处字面相同是有意耦合：新增第 4 个写入类 pending 时，只改一处会静默开一个
    「写入未完成就能导航」的口子（gateway 会路由去执行，门控却不拦）。
    这条断言让漏改在 CI 就红。
    """
    from app.agent.client.gateway import RECOMMEND_PENDING_ACTION_TYPES
    from app.agent.client.navigation import WRITE_PENDING_TYPES

    assert WRITE_PENDING_TYPES == RECOMMEND_PENDING_ACTION_TYPES, (
        "写入类 pending 集合漂移：navigation.WRITE_PENDING_TYPES 与 "
        "gateway.RECOMMEND_PENDING_ACTION_TYPES 必须同步——不同步会留下"
        "「写入未完成仍可导航」的口子"
    )
