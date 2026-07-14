import os
import tempfile
import pytest
from app.db.database import get_connection, init_db, DB_PATH
from app.db import models


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试使用独立的临时数据库"""
    test_db = os.path.join(tempfile.gettempdir(), "test_agent.db")
    original = DB_PATH
    import app.db.database as db_mod
    db_mod.DB_PATH = test_db
    init_db()
    yield
    db_mod.DB_PATH = original
    if os.path.exists(test_db):
        os.remove(test_db)


class TestDatabase:
    def test_init_creates_tables(self):
        conn = get_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        names = [r["name"] for r in tables]
        assert "sessions" in names
        assert "messages" in names
        conn.close()

    def test_create_and_list_sessions(self):
        models.create_session(1, "sess-1", "测试会话")
        sessions = models.get_user_sessions(1)
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "sess-1"
        assert sessions[0]["title"] == "测试会话"
        assert sessions[0]["message_count"] == 0

    def test_messages_belong_to_session(self):
        models.create_session(1, "sess-1")
        models.save_message("sess-1", "user", "Hello")
        models.save_message("sess-1", "assistant", "Hi!")
        msgs = models.get_session_messages("sess-1")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_delete_session_cascades(self):
        models.create_session(1, "sess-1")
        models.save_message("sess-1", "user", "Hello")
        models.delete_session("sess-1", 1)
        assert models.get_session_messages("sess-1") == []
        assert models.get_user_sessions(1) == []

    def test_session_ordering(self):
        models.create_session(1, "sess-old", "旧的")
        import time; time.sleep(0.01)
        models.create_session(1, "sess-new", "新的")
        sessions = models.get_user_sessions(1)
        assert sessions[0]["session_id"] == "sess-new"

    def test_other_user_not_visible(self):
        models.create_session(1, "sess-1")
        models.create_session(2, "sess-2")
        assert len(models.get_user_sessions(1)) == 1
