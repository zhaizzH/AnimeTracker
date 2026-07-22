import pytest
from datetime import datetime
from app.schemas.auth import UserInfo, AuthResult
from app.schemas.chat import ChatRequest
from app.schemas.session import SessionInfo, MessageOut, SessionCreateRequest, SessionCreateResponse, DeleteResponse
from app.db.models import Session, Message


class TestAuthSchemas:
    def test_user_info(self):
        u = UserInfo(user_id=1, username="test", role="USER")
        assert u.model_dump() == {"user_id": 1, "username": "test", "role": "USER"}

    def test_user_info_invalid_role(self):
        with pytest.raises(ValueError):
            UserInfo(user_id=1, username="test", role="INVALID")

    def test_auth_result_ok(self):
        u = UserInfo(user_id=1, username="test", role="USER")
        r = AuthResult(ok=True, user=u)
        assert r.ok is True
        assert r.user is not None

    def test_auth_result_fail(self):
        r = AuthResult(ok=False, error="bad token")
        assert r.ok is False
        assert r.user is None


class TestChatSchemas:
    def test_chat_request_valid(self):
        r = ChatRequest(session_id="s1", content="hello")
        assert r.session_id == "s1"
        assert r.content == "hello"

    def test_chat_request_empty_content(self):
        with pytest.raises(ValueError):
            ChatRequest(session_id="s1", content="")


class TestSessionSchemas:
    def test_session_info(self):
        dt = datetime(2026, 1, 1)
        s = SessionInfo(session_id="s1", title="test", message_count=5, created_at=dt)
        assert s.session_id == "s1"

    def test_message_out(self):
        dt = datetime(2026, 1, 1)
        m = MessageOut(role="user", content="hi", tool_calls=["search"], created_at=dt)
        assert m.role == "user"


class TestDbModels:
    def test_session_defaults(self):
        s = Session(session_id="s1", user_id=1)
        assert s.title == "新对话"
        assert s.message_count == 0

    def test_message_defaults(self):
        m = Message(session_id="s1", role="user", content="hi")
        assert m.id is None
        assert m.tool_calls is None
