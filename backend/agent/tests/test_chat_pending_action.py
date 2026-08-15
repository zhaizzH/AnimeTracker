import asyncio
from datetime import datetime, timedelta

from app.core.pending_action import emit_pending_action_clear
from app.db.models import PendingAction
from app.service.chat import ChatService


class FakeStore:
    def __init__(self, pending_action=None):
        self.pending_action = pending_action
        self.messages = []
        self.saved_pending = []
        self.deleted_pending = []

    async def save_message(self, session_id, role, content, tool_calls=None):
        self.messages.append((session_id, role, content, tool_calls))

    async def get_messages(self, session_id):
        return []

    async def update_session_title(self, session_id, title):
        pass

    async def get_pending_action(self, session_id, user_id):
        if self.pending_action is not None and self.pending_action.user_id == user_id:
            return self.pending_action
        return None

    async def save_pending_action(self, session_id, action, ttl_seconds=600):
        self.saved_pending.append((session_id, action, ttl_seconds))

    async def delete_pending_action(self, session_id, user_id):
        self.deleted_pending.append((session_id, user_id))


class CapturingGraph:
    def __init__(self):
        self.state = None

    async def astream(self, state, stream_mode=None):
        self.state = state
        yield ("values", {"result": "ok"})


class ClearEmittingGraph:
    async def astream(self, state, stream_mode=None):
        emit_pending_action_clear()
        yield ("values", {"result": "ok"})


def _run_stream(resp):
    async def _consume():
        parts = []
        async for item in resp.body_iterator:
            parts.append(item)
        return parts

    asyncio.run(_consume())


def _pending(user_id=7, preview_id="p1"):
    return PendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id=preview_id,
        user_id=user_id,
        expires_at=datetime.now() + timedelta(minutes=10),
    )


def test_build_initial_state_injects_session_id_and_pending_action():
    store = FakeStore(pending_action=_pending())
    graph = CapturingGraph()
    svc = ChatService(store=store, graph=graph, settings=None)
    resp = asyncio.run(svc.stream_chat("s1", "确认", 7, "USER"))
    _run_stream(resp)
    assert graph.state["session_id"] == "s1"
    assert graph.state["pending_action"].preview_id == "p1"
    assert graph.state["pending_preview_id"] == "p1"


def test_clear_event_deletes_pending_action_after_stream():
    store = FakeStore(pending_action=_pending())
    svc = ChatService(store=store, graph=ClearEmittingGraph(), settings=None)
    resp = asyncio.run(svc.stream_chat("s1", "取消", 7, "USER"))
    _run_stream(resp)
    assert store.deleted_pending == [("s1", 7)]
