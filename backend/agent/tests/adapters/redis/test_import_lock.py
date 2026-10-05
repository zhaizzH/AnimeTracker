"""Redis 单飞导入锁适配器的测试。"""

from __future__ import annotations

import fakeredis
import pytest

from app.adapters.redis import import_lock


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


def test_second_acquire_fails(redis_client):
    assert import_lock.acquire(redis_client, "token-a") is True
    assert import_lock.acquire(redis_client, "token-b") is False
    assert redis_client.get(import_lock.IMPORT_LOCK_KEY) == "token-a"


def test_release_then_reacquire(redis_client):
    assert import_lock.acquire(redis_client, "token-a") is True
    assert import_lock.release(redis_client, "token-a") is True
    assert redis_client.get(import_lock.IMPORT_LOCK_KEY) is None
    assert import_lock.acquire(redis_client, "token-b") is True


def test_release_with_wrong_token_keeps_lock(redis_client):
    assert import_lock.acquire(redis_client, "token-a") is True
    assert import_lock.release(redis_client, "token-b") is False
    assert redis_client.get(import_lock.IMPORT_LOCK_KEY) == "token-a"


def test_release_without_lock_returns_false(redis_client):
    assert import_lock.release(redis_client, "token-a") is False


def test_acquire_sets_ttl(redis_client):
    assert import_lock.acquire(redis_client, "token-a") is True
    ttl = redis_client.ttl(import_lock.IMPORT_LOCK_KEY)
    assert 0 < ttl <= import_lock.IMPORT_LOCK_TTL_SECONDS


def test_renew_with_correct_token_extends_ttl(redis_client):
    assert import_lock.acquire(redis_client, "token-a") is True
    assert import_lock.renew(redis_client, "token-a", ttl_seconds=10) is True
    assert 0 < redis_client.ttl(import_lock.IMPORT_LOCK_KEY) <= 10


def test_renew_with_wrong_token_returns_false(redis_client):
    assert import_lock.acquire(redis_client, "token-a") is True
    assert import_lock.renew(redis_client, "token-b", ttl_seconds=10) is False
    assert redis_client.get(import_lock.IMPORT_LOCK_KEY) == "token-a"


def test_matches_handles_bytes_token():
    """decode_responses=False 时 GET 返回 bytes，需与 str token 匹配。"""
    assert import_lock._matches(b"token-a", "token-a") is True
    assert import_lock._matches(b"token-b", "token-a") is False
    assert import_lock._matches("\xff".encode("latin-1"), "token-a") is False
