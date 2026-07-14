from app.db.database import get_connection


def create_session(user_id: int, session_id: str, title: str = ""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (session_id, user_id, title) VALUES (?, ?, ?)",
        (session_id, user_id, title),
    )
    conn.commit()
    conn.close()


def get_user_sessions(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.session_id, s.title, s.created_at, s.updated_at,
               (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.session_id) AS message_count
        FROM sessions s
        WHERE s.user_id = ?
        ORDER BY s.updated_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_messages(session_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, session_id, role, content, tool_calls, created_at FROM messages WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_message(session_id: str, role: str, content: str, tool_calls: str | None = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
        (session_id, role, content, tool_calls),
    )
    conn.commit()
    conn.close()


def update_session_title(session_id: str, title: str):
    conn = get_connection()
    conn.execute("UPDATE sessions SET title = ?, updated_at = datetime('now') WHERE session_id = ?", (title, session_id))
    conn.commit()
    conn.close()


def update_session_time(session_id: str):
    conn = get_connection()
    conn.execute("UPDATE sessions SET updated_at = datetime('now') WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def delete_session(session_id: str, user_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, user_id))
    conn.commit()
    conn.close()
