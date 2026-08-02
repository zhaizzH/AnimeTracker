import asyncio

from app.config import settings
from app.service.chat import ChatService


class FakeStore:
    def __init__(self):
        self.messages = []
        self.sessions = {}

    async def save_message(self, session_id, role, content, tool_calls=None):
        self.messages.append((session_id, role, content, tool_calls))

    async def get_messages(self, session_id):
        return [type("M", (), {"role": r, "content": c, "tool_calls": tc})() for _, r, c, tc in self.messages if _ == session_id]

    async def update_session_title(self, session_id, title):
        pass

    async def create_session(self, user_id, session_id, title="新对话"):
        pass

    async def get_user_sessions(self, user_id):
        return []

    async def delete_session(self, session_id, user_id):
        pass

    async def init_db(self):
        pass


class FakeGraph:
    async def astream(self, state, stream_mode=None):
        yield ("values", {"result": "ok"})


def test_stream_chat_returns_streaming_response():
    store = FakeStore()
    svc = ChatService(store=store, graph=FakeGraph(), settings=settings)
    resp = asyncio.run(svc.stream_chat("s1", "你好", 1, "USER"))
    assert resp.media_type == "text/event-stream"


def test_stream_chat_saves_user_message_first():
    store = FakeStore()
    svc = ChatService(store=store, graph=FakeGraph(), settings=settings)
    asyncio.run(svc.stream_chat("s1", "你好", 1, "USER"))
    assert store.messages[0][1] == "user"
    assert store.messages[0][2] == "你好"
