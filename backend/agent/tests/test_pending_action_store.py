from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.pending_action import (
    CollectionProgressPendingAction,
    WishlistPendingAction,
    WishlistPendingItem,
    parse_pending_action_json,
)

expiry = datetime.now() + timedelta(minutes=10)


def action(user_id: int, preview_id: str = "p1") -> CollectionProgressPendingAction:
    return CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id=preview_id,
        user_id=user_id,
        expires_at=expiry,
    )


def test_wishlist_pending_action_round_trip():
    action = WishlistPendingAction(
        type="ADD_TO_WISHLIST", user_id=7, expires_at=expiry,
        items=[WishlistPendingItem(subject_id=1, subject_name="A")],
    )
    assert parse_pending_action_json(action.model_dump_json(by_alias=True)).type == "ADD_TO_WISHLIST"


def test_progress_pending_action_round_trip_preserves_camel_case_items():
    action = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p1",
        user_id=7,
        expires_at=expiry,
        items=[{"subjectId": 1, "subjectName": "A", "currentEpStatus": 3, "targetEpStatus": 5}],
    )
    parsed = parse_pending_action_json(action.model_dump_json(by_alias=True))
    assert parsed.type == "COLLECTION_PROGRESS_UPDATE"
    assert parsed.items[0].subject_id == 1
    assert parsed.items[0].target_ep_status == 5


def test_unknown_pending_action_type_is_rejected():
    with pytest.raises(ValidationError):
        parse_pending_action_json('{"type":"UNKNOWN"}')


@pytest.mark.asyncio
async def test_pending_action_is_scoped_to_session_and_user(store):
    await store.save_pending_action("s1", action(user_id=7), ttl_seconds=600)
    assert (await store.get_pending_action("s1", 7)).preview_id == "p1"
    assert await store.get_pending_action("s1", 8) is None


@pytest.mark.asyncio
async def test_pending_action_uses_expected_key_and_ttl(store):
    await store.save_pending_action("s1", action(user_id=7), ttl_seconds=600)
    ttl = await store._r.ttl("agent:pending-action:s1")
    assert 0 < ttl <= 600


@pytest.mark.asyncio
async def test_delete_pending_action_removes_key(store):
    await store.save_pending_action("s1", action(user_id=7), ttl_seconds=600)
    await store.delete_pending_action("s1", 7)
    assert await store.get_pending_action("s1", 7) is None


@pytest.mark.asyncio
async def test_delete_session_cleans_pending_action(store):
    await store.create_session(7, "s1")
    await store.save_pending_action("s1", action(user_id=7), ttl_seconds=600)
    await store.delete_session("s1", 7)
    assert await store.get_pending_action("s1", 7) is None


@pytest.mark.asyncio
async def test_unknown_type_pending_action_is_logged_and_cleared(store, caplog):
    await store._r.set("agent:pending-action:s1", '{"type":"UNKNOWN"}')
    assert await store.get_pending_action("s1", 7) is None
    assert await store._r.get("agent:pending-action:s1") is None
    assert any("待确认动作数据损坏或类型未知" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_malformed_pending_action_json_is_logged_and_cleared(store, caplog):
    raw = "{corrupt-json-with-private-title"
    await store._r.set("agent:pending-action:s1", raw)
    assert await store.get_pending_action("s1", 7) is None
    assert await store._r.get("agent:pending-action:s1") is None
    assert any("待确认动作数据损坏或类型未知" in r.message for r in caplog.records)
    assert raw not in caplog.text
    assert "rawLength=32" in caplog.text
    assert "session=s1" not in caplog.text


@pytest.mark.asyncio
async def test_delete_pending_action_on_corrupt_data_clears_without_raise(store):
    await store._r.set("agent:pending-action:s1", '{"type":"UNKNOWN"}')
    await store.delete_pending_action("s1", 7)  # 不得抛出
    assert await store._r.get("agent:pending-action:s1") is None
