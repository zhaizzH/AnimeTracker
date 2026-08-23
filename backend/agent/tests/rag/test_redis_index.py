from __future__ import annotations

import math

import pytest

from app.rag.redis_index import RedisSubjectIndex, SubjectIndexDocument, vector_bytes
from app.rag.schemas import SubjectProfile


class FakeRedis:
    """只记录 RediSearch 命令；不连接任何 Redis 服务。"""

    def __init__(self) -> None:
        self.commands: list[tuple[object, ...]] = []
        self.deleted_keys: list[str] = []
        self.alias_updates: list[tuple[str, str]] = []

    def execute_command(self, *command: object) -> str:
        self.commands.append(command)
        if command[:1] == ("FT.ALIASUPDATE",):
            self.alias_updates.append((str(command[1]), str(command[2])))
        return "OK"

    def hset(self, key: str, *, mapping: dict[str, object]) -> int:
        self.commands.append(("HSET", key, mapping))
        return len(mapping)

    def delete(self, *keys: str) -> int:
        self.deleted_keys.extend(keys)
        return len(keys)

    def first(self, operation: str) -> tuple[object, ...]:
        return next(command for command in self.commands if command[0] == operation)


def adjacent_pairs(values: tuple[object, ...]) -> set[tuple[str, str]]:
    return {(str(left), str(right)) for left, right in zip(values, values[1:])}


def document() -> SubjectIndexDocument:
    return SubjectIndexDocument(
        subject_id=7,
        index_version="v1",
        profile=SubjectProfile(
            text="标题：测试动画",
            content_hash="a" * 64,
            schema_version="subject-profile-v1",
        ),
        vector=[0.25] * 1024,
        title="测试动画",
        aliases=("Test Anime",),
        summary="用于验证索引写入。",
        meta_tags=("TV",),
        trusted_tags=("治愈",),
        credits=("导演：甲",),
        year=2024,
        quarter=4,
        score=8.5,
        rating_total=100,
        collection_total=200,
        air_status="airing",
        type=2,
        nsfw=False,
    )


def test_index_definition_is_fixed():
    """索引必须固定为 1024 维 FLAT FLOAT32 cosine HASH。"""
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    assert index.ensure_version("v1") == "idx:test:rag:subject:v1"

    command = fake_redis.first("FT.CREATE")
    assert ("ON", "HASH") in adjacent_pairs(command)
    assert command.index("FLAT") < command.index("FLOAT32")
    assert ("DIM", "1024") in adjacent_pairs(command)
    assert ("DISTANCE_METRIC", "COSINE") in adjacent_pairs(command)
    assert "title" in command
    assert "year" in command


def test_write_uses_versioned_hash_key_and_validated_float32_vector():
    """错误键前缀、错误维度和非有限值都不得写入索引。"""
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    index.write(document())

    operation, key, mapping = fake_redis.first("HSET")
    assert operation == "HSET"
    assert key == "test:rag:subject:v1:7"
    assert mapping["profile"] == "标题：测试动画"
    assert mapping["vector"] == vector_bytes([0.25] * 1024)
    with pytest.raises(ValueError, match="1024"):
        vector_bytes([0.0] * 3)
    with pytest.raises(ValueError, match="有限"):
        vector_bytes([math.nan] * 1024)
    with pytest.raises(ValueError, match="有限"):
        vector_bytes([1e100] * 1024)


def test_write_accepts_only_non_nsfw_anime_documents():
    """RAG 索引只接纳 type=2 且非 NSFW 的动画条目。"""
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    index.write(document())

    assert fake_redis.first("HSET")[2]["type"] == 2
    for unsafe_document in (
        document().__class__(**{**document().__dict__, "type": 1}),
        document().__class__(**{**document().__dict__, "nsfw": True}),
    ):
        with pytest.raises(ValueError, match="type=2.*NSFW"):
            index.write(unsafe_document)
    assert len([command for command in fake_redis.commands if command[0] == "HSET"]) == 1


def test_write_omits_missing_numeric_filters_instead_of_writing_invalid_empty_values():
    """RediSearch NUMERIC 字段缺失时应省略，不能写入空字符串。"""
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    index.write(
        document().__class__(
            **{
                **document().__dict__,
                "year": None,
                "quarter": None,
                "score": None,
                "rating_total": None,
                "collection_total": None,
            }
        )
    )

    mapping = fake_redis.first("HSET")[2]
    assert not {"year", "quarter", "score", "rating_total", "collection_total"} & mapping.keys()


def test_search_uses_active_alias_knn_and_returns_redis_result():
    """搜索走别名并把 KNN 向量作为二进制参数交给 RediSearch。"""
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    result = index.search("@air_status:{airing}", [0.0] * 1024, limit=3)

    assert result == "OK"
    command = fake_redis.first("FT.SEARCH")
    assert command[1] == "idx:test:rag:subject:active"
    assert "KNN" in command[2]
    assert "@type:[2 2]" in command[2]
    assert "@nsfw:{false}" in command[2]
    assert ("PARAMS", "2") in adjacent_pairs(command)
    assert command[command.index("vector") + 1] == vector_bytes([0.0] * 1024)
    assert ("RETURN", "18") in adjacent_pairs(command)
    return_start = command.index("RETURN")
    assert "vector" not in command[return_start + 2 : return_start + 20]


def test_semantic_search_enforces_non_nsfw_anime_filters_without_caller_help():
    """Removing the index boundary guard would let a direct KNN caller bypass RAG safety."""
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    index.semantic_search("@year:[2024 2024]", [0.0] * 1024, limit=3)

    query = fake_redis.first("FT.SEARCH")[2]
    assert query == "((@year:[2024 2024]) @type:[2 2] @nsfw:{false})=>[KNN 3 @vector $vector AS vector_score]"


def test_semantic_search_without_a_primary_query_still_filters_before_knn():
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    index.semantic_search("", [0.0] * 1024, limit=3)

    assert fake_redis.first("FT.SEARCH")[2] == "(@type:[2 2] @nsfw:{false})=>[KNN 3 @vector $vector AS vector_score]"


def test_meta_tags_are_tag_values_with_a_separator_that_preserves_commas():
    """The default comma separator would split a single comma-containing tag during indexing."""
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    index.ensure_version("v1")
    index.write(document().__class__(**{**document().__dict__, "meta_tags": ("TV", "科幻,太空", "校园|日常")}))

    create = fake_redis.first("FT.CREATE")
    assert ("meta_tags", "TAG") in adjacent_pairs(create)
    assert ("TAG", "SEPARATOR") in adjacent_pairs(create)
    assert ("SEPARATOR", "|") in adjacent_pairs(create)
    assert fake_redis.first("HSET")[2]["meta_tags"] == r"TV|科幻,太空|校园\|日常"


def test_activate_never_deletes_session_keys():
    """切换仅更新别名，绝不能清理任何键或会话键。"""
    fake_redis = FakeRedis()
    index = RedisSubjectIndex(fake_redis, key_prefix="test:rag:", index_prefix="idx:test:rag:")

    index.activate("v1")

    assert fake_redis.deleted_keys == []
    assert fake_redis.alias_updates == [("idx:test:rag:subject:active", "idx:test:rag:subject:v1")]
