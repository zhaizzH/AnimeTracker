import fakeredis
import pytest

from app.db.redis_store import RedisStore


@pytest.fixture
def store():
    store = RedisStore("redis://localhost:6379/0")
    store._r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return store
