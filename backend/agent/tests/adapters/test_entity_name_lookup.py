"""通用实体索引名称解析的安全边界测试。"""

from __future__ import annotations

import pytest

from app.adapters.redis.entity_name_lookup import EntityNameMatch, RedisEntityNameLookup


class _Redis:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def execute_command(self, *args):
        self.calls.append(args)
        return self.response


def test_lookup_uses_escaped_text_and_returns_typed_entities():
    redis = _Redis([
        1,
        b"rag:entity:v1:PERSON:7",
        [b"entity_kind", b"PERSON", b"entity_id", b"7", b"name", b"A", b"aliases", b"A"],
    ])
    lookup = RedisEntityNameLookup(redis, index_version="v1")

    result = lookup.lookup('A" ) @entity_kind:{CHARACTER}', entity_kind="PERSON")

    assert result == [EntityNameMatch("PERSON", 7)]
    command = redis.calls[0]
    assert command[0:2] == ("FT.SEARCH", "idx:rag:entity:v1")
    expression = command[2]
    assert "@entity_kind:{PERSON}" in expression
    assert 'A\\"' in expression
    assert "CHARACTER}" not in expression


def test_actor_name_uses_person_documents_but_returns_actor_kind():
    redis = _Redis([
        1,
        b"rag:entity:v1:PERSON:9",
        [b"entity_kind", b"PERSON", b"entity_id", b"9", b"name", b"A", b"aliases", b"A"],
    ])
    result = RedisEntityNameLookup(redis, index_version="v1").lookup("A", entity_kind="ACTOR")

    assert result == [EntityNameMatch("ACTOR", 9)]
    assert "@entity_kind:{PERSON}" in redis.calls[0][2]


def test_relation_subject_name_uses_subject_documents_and_preserves_relation_kind():
    redis = _Redis([
        1,
        b"rag:entity:v1:SUBJECT:12",
        [b"entity_kind", b"SUBJECT", b"entity_id", b"12", b"name", b"A", b"aliases", b"A"],
    ])
    result = RedisEntityNameLookup(redis, index_version="v1").lookup(
        "A", entity_kind="RELATION_SUBJECT"
    )

    assert result == [EntityNameMatch("RELATION_SUBJECT", 12)]
    assert "@entity_kind:{SUBJECT}" in redis.calls[0][2]


def test_malformed_index_response_fails_closed_for_caller():
    redis = _Redis([1, b"key"])
    lookup = RedisEntityNameLookup(redis, index_version="v1")
    with pytest.raises(ValueError):
        lookup.lookup("A")


def test_unexpected_entity_kind_fails_closed_for_caller():
    redis = _Redis([
        1,
        b"rag:entity:v1:PERSON:7",
        [b"entity_kind", b"SUBJECT", b"entity_id", b"7"],
    ])
    with pytest.raises(ValueError):
        RedisEntityNameLookup(redis, index_version="v1").lookup("A")


@pytest.mark.parametrize("version", ["", "v:1", "v 1"])
def test_index_version_is_constrained(version):
    with pytest.raises(ValueError):
        RedisEntityNameLookup(_Redis([]), index_version=version)
