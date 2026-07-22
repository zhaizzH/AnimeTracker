import os
import tempfile
import pytest
from datetime import datetime

from app.db.base import ChatStore
from app.db.sqlite_store import SQLiteStore
from app.db.models import Session, Message


@pytest.fixture
def store():
    db_path = os.path.join(tempfile.gettempdir(), f"test_agent_{datetime.now().timestamp()}.db")
    s = SQLiteStore(f"sqlite:///{db_path}")
    s.init_db()
    yield s
    if os.path.exists(db_path):
        os.remove(db_path)


class TestSQLiteStore:
    def test_init_creates_tables(self, store):
        conn = store._conn()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        names = [r["name"] for r in tables]
        assert "sessions" in names
        assert "messages" in names
        conn.close()

    def test_create_and_list_sessions(self, store):
        store.create_session(1, "sess-1", "测试会话")
        sessions = store.get_user_sessions(1)
        assert len(sessions) == 1
        assert sessions[0].session_id == "sess-1"
        assert sessions[0].title == "测试会话"
        assert sessions[0].message_count == 0

    def test_messages_belong_to_session(self, store):
        store.create_session(1, "sess-1")
        store.save_message("sess-1", "user", "Hello")
        store.save_message("sess-1", "assistant", "Hi!")
        msgs = store.get_messages("sess-1")
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[1].role == "assistant"

    def test_delete_session_cascades(self, store):
        store.create_session(1, "sess-1")
        store.save_message("sess-1", "user", "Hello")
        store.delete_session("sess-1", 1)
        assert store.get_messages("sess-1") == []
        assert store.get_user_sessions(1) == []

    def test_session_ordering(self, store):
        store.create_session(1, "sess-old", "旧的")
        store.create_session(1, "sess-new", "新的")
        sessions = store.get_user_sessions(1)
        assert sessions[0].session_id == "sess-new"

    def test_other_user_not_visible(self, store):
        store.create_session(1, "sess-1")
        store.create_session(2, "sess-2")
        assert len(store.get_user_sessions(1)) == 1

    def test_save_message_updates_count(self, store):
        store.create_session(1, "sess-1")
        store.save_message("sess-1", "user", "Hi")
        sessions = store.get_user_sessions(1)
        assert sessions[0].message_count == 1

    def test_inherits_abc(self, store):
        assert isinstance(store, ChatStore)
