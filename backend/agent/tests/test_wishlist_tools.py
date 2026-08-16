from datetime import datetime, timedelta

import pytest

from app.agent.client.actions import wishlist
from app.core.pending_action import (
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.schemas.auth import UserInfo
from app.schemas.pending_action import WishlistPendingAction, WishlistPendingItem


@pytest.fixture
def user():
    return UserInfo(user_id=7, username="u", role="USER", token="tok")


@pytest.fixture
def pending_collector():
    token = set_pending_action_collector()
    yield
    reset_pending_action_collector(token)


@pytest.fixture
def pending():
    return WishlistPendingAction(
        type="ADD_TO_WISHLIST",
        user_id=7,
        expires_at=datetime.now() + timedelta(minutes=10),
        items=[WishlistPendingItem(subject_id=1, subject_name="A")],
    )


def fake_collection_lookup(method, path, **kw):
    sid = int(path.rsplit("/", 1)[-1])
    if sid == 1:
        return None  # 未收藏
    return {"type": 3, "subjectId": 2}  # 已收藏（在看）


def test_preview_skips_existing_and_sets_only_missing(monkeypatch, user, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", fake_collection_lookup)
    result = wishlist.preview_add_to_wishlist.func([
        {"subjectId": 1, "subjectName": "A"}, {"subjectId": 2, "subjectName": "B"}
    ], user=user)
    assert [x["subjectId"] for x in result["pendingItems"]] == [1]
    assert [x["subjectId"] for x in result["skippedItems"]] == [2]
    event = get_pending_action_event()
    assert event is not None and event.operation == "SET"
    assert event.action.type == "ADD_TO_WISHLIST"


def test_execute_uses_pending_items_not_model_arguments(monkeypatch, user, pending):
    calls = []
    monkeypatch.setattr(wishlist, "call_api", lambda method, path, **kw: calls.append(path) or {"state": "ADDED"})
    wishlist.execute_add_to_wishlist.func(pending=pending, user=user)
    assert calls == ["/api/client/collections/1/wishlist"]


def test_preview_deduplicates_and_caps_at_ten(monkeypatch, user, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", lambda *a, **k: None)
    subjects = [{"subjectId": i, "subjectName": str(i)} for i in range(1, 15)]
    subjects.append({"subjectId": 3, "subjectName": "dup"})  # 重复的 3
    result = wishlist.preview_add_to_wishlist.func(subjects, user=user)
    assert len(result["pendingItems"]) == 10
    assert len({x["subjectId"] for x in result["pendingItems"]}) == 10


def test_preview_missing_subject_id_does_not_set_pending(monkeypatch, user, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", lambda *a, **k: None)
    result = wishlist.preview_add_to_wishlist.func([{"subjectName": "no-id"}], user=user)
    assert result["pendingItems"] == []
    assert get_pending_action_event() is None


def test_preview_all_existing_does_not_set_pending(monkeypatch, user, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", lambda *a, **k: {"type": 1, "subjectId": 5})
    result = wishlist.preview_add_to_wishlist.func([{"subjectId": 5, "subjectName": "A"}], user=user)
    assert result["pendingItems"] == []
    assert result["skippedItems"] == [{"subjectId": 5, "subjectName": "A", "existingType": 1}]
    assert get_pending_action_event() is None


def test_preview_non_404_error_is_real_error(monkeypatch, user, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", lambda *a, **k: {"error": True, "code": 500, "message": "boom"})
    result = wishlist.preview_add_to_wishlist.func([{"subjectId": 1, "subjectName": "A"}], user=user)
    assert result.get("error") is True
    assert get_pending_action_event() is None


def test_execute_classifies_succeeded_skipped_failed(monkeypatch, user):
    def fake(method, path, **kw):
        sid = int(path.split("/")[-2])  # /api/client/collections/{sid}/wishlist
        if sid == 1:
            return {"state": "ADDED"}
        if sid == 2:
            return {"state": "ALREADY_COLLECTED", "existingType": 3}
        return {"error": True, "code": 500, "message": "boom"}

    monkeypatch.setattr(wishlist, "call_api", fake)
    action = WishlistPendingAction(
        type="ADD_TO_WISHLIST", user_id=7,
        expires_at=datetime.now() + timedelta(minutes=10),
        items=[
            WishlistPendingItem(subject_id=1, subject_name="A"),
            WishlistPendingItem(subject_id=2, subject_name="B"),
            WishlistPendingItem(subject_id=3, subject_name="C"),
        ],
    )
    result = wishlist.execute_add_to_wishlist.func(pending=action, user=user)
    assert [x["subjectId"] for x in result["succeeded"]] == [1]
    assert [x["subjectId"] for x in result["skipped"]] == [2]
    assert [x["subjectId"] for x in result["failed"]] == [3]


def test_execute_clears_pending_after_completion(monkeypatch, user, pending, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", lambda *a, **k: {"state": "ADDED"})
    wishlist.execute_add_to_wishlist.func(pending=pending, user=user)
    event = get_pending_action_event()
    assert event is not None and event.operation == "CLEAR"


def test_execute_unexpected_state_is_failed_not_succeeded(monkeypatch, user, pending, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", lambda *a, **k: {"state": "PENDING"})
    result = wishlist.execute_add_to_wishlist.func(pending=pending, user=user)
    assert result["succeeded"] == []
    assert [x["subjectId"] for x in result["failed"]] == [1]
    event = get_pending_action_event()
    assert event is not None and event.operation == "CLEAR"


def test_execute_infrastructure_error_keeps_pending(monkeypatch, user, pending, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", lambda *a, **k: {"error": True, "message": "后端服务超时"})
    result = wishlist.execute_add_to_wishlist.func(pending=pending, user=user)
    assert result["failed"]
    assert get_pending_action_event() is None


def test_cancel_clears_without_calling_business(monkeypatch, pending_collector):
    monkeypatch.setattr(wishlist, "call_api", lambda *a, **k: pytest.fail("must not call business"))
    assert wishlist.cancel_add_to_wishlist.func() == {"cancelled": True}
    event = get_pending_action_event()
    assert event is not None and event.operation == "CLEAR"
