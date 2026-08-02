import asyncio

import fakeredis

from app.db.redis_store import RedisStore


def _make_store() -> RedisStore:
    store = RedisStore("redis://localhost:6379/0")
    store._r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return store


def test_session_and_message_roundtrip():
    store = _make_store()
    asyncio.run(store.init_db())
    asyncio.run(store.create_session(1, "s1"))
    asyncio.run(store.create_session(1, "s2", title="会话2"))

    # 先断言会话排序(此时尚未保存消息,s2 的 updated_at 最新)
    sessions = asyncio.run(store.get_user_sessions(1))
    assert {s.session_id for s in sessions} == {"s1", "s2"}
    assert sessions[0].title == "会话2"  # 按 updated_at 降序,后创建的在前

    asyncio.run(store.save_message("s1", "user", "你好"))
    asyncio.run(store.save_message("s1", "assistant", "回复", '["search_subjects"]'))

    msgs = asyncio.run(store.get_messages("s1"))
    assert [m.content for m in msgs] == ["你好", "回复"]
    assert msgs[1].tool_calls == '["search_subjects"]'


def test_delete_session_cleans_messages():
    store = _make_store()
    asyncio.run(store.create_session(1, "s1"))
    asyncio.run(store.save_message("s1", "user", "x"))
    asyncio.run(store.delete_session("s1", 1))
    assert asyncio.run(store.get_user_sessions(1)) == []
    assert asyncio.run(store.get_messages("s1")) == []
