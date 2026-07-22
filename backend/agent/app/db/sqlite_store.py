import sqlite3
import re
from datetime import datetime

from app.db.base import ChatStore
from app.db.models import Session, Message


class SQLiteStore(ChatStore):
    def __init__(self, database_url: str):
        m = re.match(r"sqlite:///(.+)", database_url)
        self.db_path = m.group(1) if m else database_url

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT DEFAULT '新对话',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated_at);
            """)

    def create_session(self, user_id: int, session_id: str, title: str = "新对话"):
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, user_id, title, now, now),
            )

    def get_user_sessions(self, user_id: int) -> list[Session]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
            ).fetchall()
        return [Session(**dict(r)) for r in rows]

    def get_messages(self, session_id: str) -> list[Message]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at", (session_id,)
            ).fetchall()
        return [Message(**dict(r)) for r in rows]

    def save_message(self, session_id: str, role: str, content: str, tool_calls: str | None = None):
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, tool_calls, now),
            )
            if role == "user":
                conn.execute(
                    "UPDATE sessions SET message_count = message_count + 1, updated_at = ? WHERE session_id = ?",
                    (now, session_id),
                )
            else:
                conn.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    (now, session_id),
                )

    def delete_session(self, session_id: str, user_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, user_id))

    def update_session_title(self, session_id: str, title: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ?",
                (title, datetime.now().isoformat(), session_id),
            )
