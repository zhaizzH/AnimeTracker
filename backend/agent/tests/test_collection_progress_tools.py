import pytest

from app.agent.client import collections
from app.core.pending_action import (
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.schemas.auth import UserInfo


@pytest.fixture
def user():
    return UserInfo(user_id=7, username="u", role="USER", token="tok")


@pytest.fixture
def pending_collector():
    token = set_pending_action_collector()
    yield
    reset_pending_action_collector(token)


def _preview_data(preview_id):
    return {
        "previewId": preview_id,
        "state": "PENDING",
        "expiresAt": "2026-08-15T12:10:00+08:00",
        "items": [{"subjectId": 1, "subjectName": "A", "currentEpStatus": 3, "targetEpStatus": 5}],
    }


def _changed_data(preview_id):
    return {"state": "PREVIEW_CHANGED", "preview": _preview_data(preview_id)}


def test_preview_calls_business_and_sets_pending_action(monkeypatch, user, pending_collector):
    monkeypatch.setattr(collections, "call_api", lambda *a, **k: _preview_data("p1"))
    result = collections.preview_weekly_collection_progress.func(user=user)
    assert result["previewId"] == "p1"
    event = get_pending_action_event()
    assert event is not None and event.operation == "SET"


def test_execute_changed_preview_replaces_pending_action(monkeypatch, user, pending_collector):
    monkeypatch.setattr(collections, "call_api", lambda *a, **k: _changed_data("p2"))
    result = collections.execute_weekly_collection_progress.func(preview_id="p1", user=user)
    assert result["state"] == "PREVIEW_CHANGED"
    event = get_pending_action_event()
    assert event is not None and event.operation == "REPLACE"
    assert event.action.preview_id == "p2"


def test_execute_completed_clears_pending_action(monkeypatch, user, pending_collector):
    monkeypatch.setattr(collections, "call_api", lambda *a, **k: {"state": "COMPLETED"})
    collections.execute_weekly_collection_progress.func(preview_id="p1", user=user)
    event = get_pending_action_event()
    assert event is not None and event.operation == "CLEAR"


def test_cancel_clears_without_calling_business(monkeypatch, pending_collector):
    monkeypatch.setattr(collections, "call_api", lambda *a, **k: pytest.fail("must not call business"))
    assert collections.cancel_weekly_collection_progress.func() == {"cancelled": True}
    event = get_pending_action_event()
    assert event is not None and event.operation == "CLEAR"
