from datetime import datetime, timedelta

import pytest

from app.db.models import PendingAction


def action(user_id: int, preview_id: str = "p1") -> PendingAction:
    return PendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id=preview_id,
        user_id=user_id,
        expires_at=datetime.now() + timedelta(minutes=10),
    )


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
