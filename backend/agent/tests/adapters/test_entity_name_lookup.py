"""Business-owned entity name resolver boundary tests."""

from __future__ import annotations

import pytest

from app.adapters.redis.entity_name_lookup import EntityNameMatch, RedisEntityNameLookup


def test_lookup_delegates_typed_name_without_building_redis_expression():
    calls = []

    def resolver(name, *, entity_kind, limit):
        calls.append((name, entity_kind, limit))
        return [{"entity_kind": "PERSON", "entity_id": 7}]

    result = RedisEntityNameLookup(index_version="v1", resolver=resolver).lookup("花泽香菜", entity_kind="PERSON")
    assert result == [EntityNameMatch("PERSON", 7)]
    assert calls == [("花泽香菜", "PERSON", 50)]


def test_vector_set_name_lookup_fails_closed_without_business_resolver():
    with pytest.raises(RuntimeError, match="Business typed resolver"):
        RedisEntityNameLookup(index_version="v1").lookup("A")


def test_invalid_resolver_response_fails_closed():
    lookup = RedisEntityNameLookup(resolver=lambda *_args, **_kwargs: {"items": []})
    with pytest.raises(RuntimeError, match="response invalid"):
        lookup.lookup("A")
