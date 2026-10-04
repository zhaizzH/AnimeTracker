"""``collection_progress`` 三个工具的待确认动作生命周期。

本模块此前零测试。覆盖：预览生成动作、写入门禁拒绝、404/409 清理、
``COMPLETED`` 清理、``PREVIEW_CHANGED`` 替换、无 ``previewId`` 时不替换、取消清理。

待确认动作经 ``pending_events`` 的 ContextVar collector 观测（与
``test_wishlist.py`` 同一模式）；``BusinessGateway`` 用替身记录请求。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.agent.client.actions.collection_progress import build_collection_progress_tools
from app.chat.pending_action import CollectionProgressPendingAction
from app.chat.pending_events import (
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.chat.user import UserInfo

_USER = UserInfo(user_id=2, username="tester", role="USER", token="tok")

# 依赖"尚未过期"的用例必须用相对时间，写死日期会随日历推移变成过期分支。
_FUTURE_EXPIRES_AT = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()


def _preview_response(*, preview_id: str = "p-1") -> dict:
    return {
        "previewId": preview_id,
        "expiresAt": _FUTURE_EXPIRES_AT,
        "items": [
            {"subjectId": 84, "subjectName": "X", "currentEpStatus": 3, "targetEpStatus": 4}
        ],
    }

class _Business:
    """记录每次请求，按脚本返回响应。"""

    def __init__(self, responses: list[dict | None] | None = None) -> None:
        self.calls: list[tuple] = []
        self._responses = list(responses or [])

    def request(self, method, path, *, token=None, params=None, json_body=None):
        self.calls.append((method, path, token))
        return self._responses.pop(0) if self._responses else None

def _pending_action(*, user_id: int = 2, expires_at: str = _FUTURE_EXPIRES_AT):
    return CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-old",
        user_id=user_id,
        expires_at=expires_at,
    )

@pytest.fixture
def collector():
    token = set_pending_action_collector()
    try:
        yield get_pending_action_event
    finally:
        reset_pending_action_collector(token)

def _tools(business: _Business):
    preview, execute, cancel = build_collection_progress_tools(business)
    return preview, execute, cancel

# --------------------------------------------------------------------------- #
# preview_weekly_collection_progress
# --------------------------------------------------------------------------- #

def test_preview_emits_pending_action_set_when_preview_id_present(collector) -> None:
    business = _Business([_preview_response()])
    preview, _, _ = _tools(business)

    result = preview.func(user=_USER)

    assert result["previewId"] == "p-1"
    assert business.calls == [("POST", "/api/client/collections/progress-preview", "tok")]
    event = collector()
    assert event is not None and event.operation == "SET"
    assert isinstance(event.action, CollectionProgressPendingAction)
    assert event.action.preview_id == "p-1"
    assert event.action.user_id == 2
    assert [item.subject_id for item in event.action.items] == [84]

def test_preview_without_user_returns_error_and_does_not_call_business(collector) -> None:
    business = _Business([_preview_response()])
    preview, _, _ = _tools(business)

    result = preview.func(user=None)

    assert result == {"error": True, "message": "用户上下文不可用"}
    assert business.calls == []
    assert collector() is None

@pytest.mark.parametrize(
    "response",
    [
        {"error": True, "message": "boom"},
        {"items": []},                      # 无 previewId
        {"previewId": ""},                  # 空 previewId
    ],
)
def test_preview_without_usable_preview_id_emits_nothing(collector, response) -> None:
    business = _Business([response])
    preview, _, _ = _tools(business)

    preview.func(user=_USER)

    assert collector() is None

@pytest.mark.xfail(
    reason=(
        "已知缺陷：Business 成功但 data 为 null 时 ``request`` 返回 None"
        "（business_http.py:68），``data.get`` 抛 AttributeError。"
        "同目录其它 5 个模块均用 isinstance 守卫（见 T-collection-progress-none-guard）"
    ),
    raises=AttributeError,
    strict=True,
)
def test_preview_none_response_should_not_emit_and_not_crash(collector) -> None:
    """网关成功但无 data（``request`` 返回 None）时不得抛 AttributeError。"""
    business = _Business([None])
    preview, _, _ = _tools(business)

    result = preview.func(user=_USER)

    assert result is None
    assert collector() is None

@pytest.mark.xfail(
    reason="同 T-collection-progress-none-guard：``execute_weekly_collection_progress:65`` 同样缺 isinstance 守卫",
    raises=AttributeError,
    strict=True,
)
def test_execute_none_response_should_not_crash(collector) -> None:
    business = _Business([None])
    _, execute, _ = _tools(business)

    result = execute.func(
        preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True,
    )

    assert result is None
    assert collector() is None

# --------------------------------------------------------------------------- #
# execute_weekly_collection_progress：写入门禁
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"user": None}, "用户上下文不可用"),
        ({"user": _USER, "pending": None}, "没有待确认的动作"),
        ({"user": _USER, "pending": _pending_action(user_id=999)}, "不属于当前用户"),
        ({"user": _USER, "pending": _pending_action(expires_at="2020-01-01T00:00:00+00:00")}, "已过期"),
        ({"user": _USER, "pending": _pending_action(), "write_confirmed": False}, "需要用户明确确认"),
    ],
)
def test_execute_is_refused_by_write_guard_without_calling_business(
    collector, kwargs, expected: str
) -> None:
    business = _Business([{"state": "COMPLETED"}])
    _, execute, _ = _tools(business)
    params = {"preview_id": "p-old", **kwargs}

    result = execute.func(**params)

    assert result["error"] is True
    assert expected in result["message"]
    assert business.calls == []             # 非确认回合 Business 零调用
    assert collector() is None              # 未清理既有动作

def test_execute_passes_guard_and_calls_business_when_confirmed(collector) -> None:
    business = _Business([{"state": "COMPLETED"}])
    _, execute, _ = _tools(business)

    result = execute.func(
        preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True, 
    )

    assert result["state"] == "COMPLETED"
    assert business.calls == [
        ("POST", "/api/client/collections/progress-preview/p-old/execute", "tok")
    ]

# --------------------------------------------------------------------------- #
# execute：state 分支
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("code", [404, 409])
def test_execute_clears_pending_on_stale_preview_errors(collector, code: int) -> None:
    message = "预览已失效，请重新生成" if code == 409 else "not found"
    business = _Business([{"error": True, "code": code, "message": message}])
    _, execute, _ = _tools(business)

    result = execute.func(
        preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True,
    )

    assert result["error"] is True
    event = collector()
    assert event is not None and event.operation == "CLEAR"

def test_execute_keeps_pending_when_409_message_is_not_about_regeneration(collector) -> None:
    """409 只在提示「重新生成」时清理；其它 409 保留动作以免误清。"""
    business = _Business([{"error": True, "code": 409, "message": "并发冲突"}])
    _, execute, _ = _tools(business)

    execute.func(preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True)

    assert collector() is None

@pytest.mark.parametrize("code", [400, 500])
def test_execute_keeps_pending_on_other_errors(collector, code: int) -> None:
    """基础设施错误结果不确定 → 保留动作（spec 待确认动作矩阵）。"""
    business = _Business([{"error": True, "code": code, "message": "boom"}])
    _, execute, _ = _tools(business)

    execute.func(preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True)

    assert collector() is None

def test_execute_clears_pending_when_state_completed(collector) -> None:
    business = _Business([{"state": "COMPLETED"}])
    _, execute, _ = _tools(business)

    execute.func(preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True)

    event = collector()
    assert event is not None and event.operation == "CLEAR"

def test_execute_replaces_pending_when_preview_changed(collector) -> None:
    business = _Business([{"state": "PREVIEW_CHANGED", "preview": _preview_response(preview_id="p-2")}])
    _, execute, _ = _tools(business)

    execute.func(preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True)

    event = collector()
    assert event is not None and event.operation == "REPLACE"
    assert event.action is not None
    assert event.action.preview_id == "p-2"

@pytest.mark.parametrize(
    "preview",
    [None, {}, {"previewId": ""}],
)
def test_execute_keeps_pending_when_preview_changed_lacks_preview_id(collector, preview) -> None:
    business = _Business([{"state": "PREVIEW_CHANGED", "preview": preview}])
    _, execute, _ = _tools(business)

    execute.func(preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True)

    assert collector() is None

def test_execute_emits_nothing_on_unknown_state(collector) -> None:
    business = _Business([{"state": "PENDING"}])
    _, execute, _ = _tools(business)

    execute.func(preview_id="p-old", user=_USER, pending=_pending_action(), write_confirmed=True)

    assert collector() is None

# --------------------------------------------------------------------------- #
# cancel_weekly_collection_progress
# --------------------------------------------------------------------------- #

def test_cancel_clears_pending_and_never_touches_business(collector) -> None:
    business = _Business()
    _, _, cancel = _tools(business)

    result = cancel.func()

    assert result == {"cancelled": True}
    assert business.calls == []
    event = collector()
    assert event is not None and event.operation == "CLEAR"
    assert event.action is None

# --------------------------------------------------------------------------- #
# 工具集组成
# --------------------------------------------------------------------------- #

def test_build_returns_three_tools_in_stable_order() -> None:
    names = [tool.name for tool in build_collection_progress_tools(_Business())]
    assert names == [
        "preview_weekly_collection_progress",
        "execute_weekly_collection_progress",
        "cancel_weekly_collection_progress",
    ]
