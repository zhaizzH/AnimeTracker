from pathlib import Path
import json

from app.chat.pending_action import CollectionProgressPendingAction, CollectionProgressPendingItem

from app.chat.ports import ChatStore


def test_redis_chat_store_implements_chat_store_protocol():
    from app.adapters.redis.chat_store import RedisChatStore

    assert isinstance(RedisChatStore("redis://localhost:6379/15"), ChatStore)


def test_api_module_does_not_import_concrete_redis_store():
    source = Path("app/api/chat.py").read_text(encoding="utf-8")

    assert "RedisStore" not in source
    assert "app.db" not in source


class FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.lists = {}
        self.sets = {}
        self.values = {}
        self.expirations = {}

    async def hset(self, key, field=None, value=None, *, mapping=None):
        values = self.hashes.setdefault(key, {})
        if mapping is not None:
            values.update(mapping)
        else:
            values[field] = value

    async def sadd(self, key, member):
        self.sets.setdefault(key, set()).add(member)

    async def smembers(self, key):
        return self.sets.get(key, set())

    async def hgetall(self, key):
        return self.hashes.get(key, {})

    async def rpush(self, key, value):
        self.lists.setdefault(key, []).append(value)

    async def lrange(self, key, _start, _end):
        return self.lists.get(key, [])

    async def hincrby(self, key, field, amount):
        values = self.hashes.setdefault(key, {})
        values[field] = int(values.get(field, 0)) + amount

    def pipeline(self):
        return FakePipeline(self)

    async def set(self, key, value, *, ex):
        self.values[key] = value
        self.expirations[key] = ex

    async def get(self, key):
        return self.values.get(key)

    async def delete(self, *keys):
        for key in keys:
            self.hashes.pop(key, None)
            self.lists.pop(key, None)
            self.values.pop(key, None)
        return len(keys)

    async def srem(self, key, member):
        self.sets.get(key, set()).discard(member)


class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.operations = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def hset(self, *args, **kwargs):
        self.operations.append(("hset", args, kwargs))

    def hincrby(self, *args, **kwargs):
        self.operations.append(("hincrby", args, kwargs))

    async def execute(self):
        for operation, args, kwargs in self.operations:
            await getattr(self.redis, operation)(*args, **kwargs)


async def test_redis_chat_store_preserves_keys_json_ttl_and_ordering(monkeypatch):
    from app.adapters.redis import chat_store

    redis = FakeRedis()
    monkeypatch.setattr(chat_store.redis.asyncio, "from_url", lambda *_args, **_kwargs: redis)
    store = chat_store.RedisChatStore("redis://contract")

    await store.create_session(7, "new", "新会话")
    await store.create_session(7, "old", "旧会话")
    await store.save_message("old", "user", "第一条")
    await store.save_message("old", "assistant", "第二条", '{"tool":"Search"}')
    await store.save_pending_action(
        "old",
        CollectionProgressPendingAction(
            type="COLLECTION_PROGRESS_UPDATE",
            preview_id="preview-1",
            user_id=7,
            expires_at="2026-08-25T00:00:00",
            items=[CollectionProgressPendingItem(subject_id=42, subject_name="EVA", current_ep_status=1, target_ep_status=2)],
        ),
    )

    assert set(redis.hashes) == {"agent:session:new", "agent:session:old"}
    assert redis.sets == {"agent:user_sessions:7": {"new", "old"}}
    messages = [json.loads(row) for row in redis.lists["agent:messages:old"]]
    assert [(message["role"], message["content"], message["tool_calls"]) for message in messages] == [
        ("user", "第一条", None),
        ("assistant", "第二条", '{"tool":"Search"}'),
    ]
    assert all(set(message) == {"role", "content", "tool_calls", "created_at"} for message in messages)
    assert all(message["created_at"] for message in messages)
    assert redis.hashes["agent:session:old"]["message_count"] == 1
    assert [session.session_id for session in await store.get_user_sessions(7)] == ["old", "new"]
    assert [message.content for message in await store.get_messages("old")] == ["第一条", "第二条"]

    pending_key = "agent:pending-action:old"
    assert redis.expirations[pending_key] == 600
    assert json.loads(redis.values[pending_key]) == {
        "type": "COLLECTION_PROGRESS_UPDATE",
        "preview_id": "preview-1",
        "user_id": 7,
        "expires_at": "2026-08-25T00:00:00",
        "summary": [{"subjectId": 42, "subjectName": "EVA", "currentEpStatus": 1, "targetEpStatus": 2}],
    }
    assert (await store.get_pending_action("old", 7)).preview_id == "preview-1"
