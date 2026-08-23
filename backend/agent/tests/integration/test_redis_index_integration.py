from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest
import redis
from redis.exceptions import ResponseError

from app.rag.redis_index import RedisSubjectIndex, SubjectIndexDocument
from app.rag.schemas import SubjectProfile


pytestmark = pytest.mark.skipif(
    os.getenv("RAG_INTEGRATION_TESTS") != "true",
    reason="set RAG_INTEGRATION_TESTS=true to run RediSearch integration tests",
)


def _is_test_database(redis_url: str) -> bool:
    return urlparse(redis_url).path.strip("/") not in ("", "0")


@pytest.fixture
def isolated_index():
    redis_url = os.getenv("RAG_TEST_REDIS_URL", "")
    key_prefix = os.getenv("RAG_TEST_KEY_PREFIX", "test:rag:")
    index_prefix = os.getenv("RAG_TEST_INDEX_PREFIX", "idx:test:rag:")
    if not redis_url:
        pytest.fail("RAG_INTEGRATION_TESTS=true 时必须提供 RAG_TEST_REDIS_URL")
    if not key_prefix.startswith("test:rag:") or not index_prefix.startswith("idx:test:rag:"):
        pytest.fail("集成测试只能使用 test:rag: 键前缀和 idx:test:rag: 索引前缀")
    if not _is_test_database(redis_url) and not key_prefix.startswith("test:rag:"):
        pytest.fail("非测试 Redis DB 必须使用 test:rag: 键前缀")

    client = redis.Redis.from_url(redis_url, decode_responses=False)
    index = RedisSubjectIndex(client, key_prefix=key_prefix, index_prefix=index_prefix)
    version = "v1"
    name = index.ensure_version(version)
    try:
        yield index
    finally:
        try:
            client.execute_command("FT.ALIASDEL", index.active_alias)
        except ResponseError:
            pass
        try:
            client.execute_command("FT.DROPINDEX", name, "DD")
        except ResponseError:
            pass
        keys = list(client.scan_iter(match=f"{key_prefix}subject:*") )
        if keys:
            client.delete(*keys)
        indexes = client.execute_command("FT._LIST")
        assert not any(item.decode() == name for item in indexes)
        assert list(client.scan_iter(match=f"{key_prefix}subject:*")) == []


def _document(subject_id: int, title: str, air_status: str, vector: list[float]) -> SubjectIndexDocument:
    return SubjectIndexDocument(
        subject_id=subject_id,
        index_version="v1",
        profile=SubjectProfile(
            text=f"标题：{title}",
            content_hash=f"{subject_id:064x}",
            schema_version="subject-profile-v1",
        ),
        vector=vector,
        title=title,
        air_status=air_status,
        type=2,
    )


def test_redisearch_knn_fulltext_filter_and_alias_cleanup(isolated_index: RedisSubjectIndex):
    """真实 RediSearch 仅在显式测试资源上验证索引能力，并自行清理。"""
    first = [1.0] + [0.0] * 1023
    second = [0.0, 1.0] + [0.0] * 1022
    third = [0.0, 0.0, 1.0] + [0.0] * 1021
    isolated_index.write(_document(1, "alpha story", "airing", first))
    isolated_index.write(_document(2, "beta story", "airing", second))
    isolated_index.write(_document(3, "gamma story", "finished", third))
    isolated_index.activate("v1")

    alpha = isolated_index.search("@title:alpha", first, limit=3)
    airing = isolated_index.search("@air_status:{airing}", first, limit=3)

    assert alpha[0] == 1
    assert airing[0] == 2
