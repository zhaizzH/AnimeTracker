from app.chat.protocol import (
    ServerToken, ServerDone, ServerError,
    ServerSessionList, ServerHistory, ServerPing,
)


class TestProtocol:
    def test_token(self):
        d = ServerToken(session_id="s1", content="推荐").to_dict()
        assert d == {"type": "token", "session_id": "s1", "content": "推荐"}

    def test_done(self):
        d = ServerDone(session_id="s1", full_content="推荐完毕", tool_calls=["search"]).to_dict()
        assert d == {"type": "done", "session_id": "s1", "full_content": "推荐完毕", "tool_calls": ["search"]}

    def test_error(self):
        d = ServerError(session_id="s1", message="出错了").to_dict()
        assert d == {"type": "error", "session_id": "s1", "message": "出错了"}

    def test_session_list(self):
        d = ServerSessionList(sessions=[{"session_id": "s1", "title": "测试"}]).to_dict()
        assert d["type"] == "session_list"
        assert len(d["sessions"]) == 1

    def test_history(self):
        d = ServerHistory(session_id="s1", messages=[{"role": "user", "content": "hi"}]).to_dict()
        assert d["type"] == "history"
        assert len(d["messages"]) == 1

    def test_ping(self):
        d = ServerPing().to_dict()
        assert d == {"type": "ping"}
