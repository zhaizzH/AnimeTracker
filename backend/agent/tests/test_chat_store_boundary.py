from pathlib import Path

from app.chat.ports import ChatStore


def test_redis_chat_store_implements_chat_store_protocol():
    from app.adapters.redis.chat_store import RedisChatStore

    assert isinstance(RedisChatStore("redis://localhost:6379/15"), ChatStore)


def test_api_module_does_not_import_concrete_redis_store():
    source = Path("app/api/chat.py").read_text(encoding="utf-8")

    assert "RedisStore" not in source
    assert "app.db" not in source
