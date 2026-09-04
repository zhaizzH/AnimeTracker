"""结构化人物/角色/声优筛选必须先经过 Business 权威关系查询。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import ValidationError

from app.rag.retrieval import RagRetrievalService
from app.rag.schemas import RetrievalQuery
from app.agent.client.rag_tools import build_rag_tools


@dataclass
class _Index:
    rows: list[dict[str, Any]] | None = None
    failed: bool = False
    calls: int = 0

    def lexical_search(self, _expression: str, limit: int = 50):
        self.calls += 1
        if self.failed:
            raise ConnectionError("redis down")
        return (self.rows or [])[:limit]

    def semantic_search(self, _expression: str, _vector, limit: int = 50):
        return (self.rows or [])[:limit]


@dataclass
class _Embeddings:
    def embed_documents(self, texts):
        return [[0.0] * 1024 for _ in texts]


def _authority(ids, token=None, exclude_collected=False):
    return [
        {"id": subject_id, "name": f"Subject {subject_id}", "type": 2, "nsfw": False}
        for subject_id in ids
    ]


def _resolver(mapping):
    calls: list[tuple[str, list[int]]] = []

    def resolve(entity_type, entity_ids, token=None):
        calls.append((entity_type, list(entity_ids)))
        return [
            {"subjectId": subject_id, "type": 2, "nsfw": False, "active": True}
            for subject_id in mapping.get(entity_type, [])
        ]

    resolve.calls = calls
    return resolve


def _service(index, resolver=None, business_search=None):
    return RagRetrievalService(
        index=index,
        embeddings=_Embeddings(),
        authority_lookup=_authority,
        business_search=business_search or (lambda query, token=None: []),
        resolve_evidence_lookup=resolver,
    )


def test_entity_ids_are_strict_and_capped():
    query = RetrievalQuery(keywords=["test"], person_ids=[1, 2], actor_ids=[3])
    assert query.person_ids == [1, 2]
    with pytest.raises(ValidationError):
        RetrievalQuery(keywords=["test"], person_ids=["1"])
    with pytest.raises(ValidationError):
        RetrievalQuery(keywords=["test"], character_ids=[0])
    with pytest.raises(ValidationError):
        RetrievalQuery(keywords=["test"], actor_ids=list(range(1, 52)))


def test_rag_tool_schema_rejects_coercible_entity_ids():
    search_tool = build_rag_tools(None)[0]
    with pytest.raises(ValidationError):
        search_tool.args_schema.model_validate({"semantic_query": "test", "person_ids": ["1"]})
    with pytest.raises(ValidationError):
        search_tool.args_schema.model_validate({"semantic_query": "test", "person_ids": [True]})
    with pytest.raises(ValidationError):
        search_tool.args_schema.model_validate({"semantic_query": "test", "person_ids": list(range(1, 52))})


def test_entity_filter_resolves_before_redis_and_filters_candidates():
    index = _Index(rows=[{"subject_id": 1}, {"subject_id": 2}])
    resolver = _resolver({"PERSON": [1]})
    result = _service(index, resolver).retrieve(
        RetrievalQuery(keywords=["test"], person_ids=[17]), token="token"
    )

    assert result.available is True
    assert [item.subject_id for item in result.items] == [1]
    assert resolver.calls == [("PERSON", [17])]
    assert index.calls > 0


def test_multiple_entity_filters_intersect_business_subject_sets():
    index = _Index(rows=[{"subject_id": 1}, {"subject_id": 2}, {"subject_id": 3}])
    resolver = _resolver({"PERSON": [1, 2], "CHARACTER": [2, 3]})
    result = _service(index, resolver).retrieve(
        RetrievalQuery(keywords=["test"], person_ids=[7], character_ids=[8])
    )

    assert result.available is True
    assert [item.subject_id for item in result.items] == [2]
    assert resolver.calls == [("PERSON", [7]), ("CHARACTER", [8])]


def test_relation_subject_filter_uses_relation_expansion_type():
    index = _Index(rows=[{"subject_id": 3}])
    resolver = _resolver({"RELATION_SUBJECT": [3]})
    result = _service(index, resolver).retrieve(
        RetrievalQuery(keywords=["test"], relation_subject_ids=[10])
    )
    assert result.available is True
    assert [item.subject_id for item in result.items] == [3]
    assert resolver.calls == [("RELATION_SUBJECT", [10])]


def test_entity_resolution_failure_is_fail_closed_before_index_access():
    index = _Index(rows=[{"subject_id": 1}])

    def failing_resolver(entity_type, entity_ids, token=None):
        raise ConnectionError("business down")

    result = _service(index, failing_resolver).retrieve(
        RetrievalQuery(keywords=["test"], person_ids=[7])
    )
    assert result.available is False
    assert result.items == []
    assert result.reason == "entity_resolution_unavailable"
    assert index.calls == 0


def test_business_fallback_keeps_entity_allowlist():
    index = _Index(failed=True)
    resolver = _resolver({"ACTOR": [2]})

    def business_search(query, token=None):
        return [
            {"id": 1, "name": "not allowed"},
            {"id": 2, "name": "allowed"},
        ]

    result = _service(index, resolver, business_search).retrieve(
        RetrievalQuery(keywords=["test"], actor_ids=[9])
    )
    assert result.available is True
    assert [item.subject_id for item in result.items] == [2]


def test_entity_allowlist_is_not_limited_by_redis_top_fifty():
    index = _Index(rows=[{"subject_id": subject_id} for subject_id in range(1, 101)])
    resolver = _resolver({"PERSON": [100]})
    result = _service(index, resolver).retrieve(
        RetrievalQuery(keywords=["test"], person_ids=[9])
    )
    assert result.available is True
    assert [item.subject_id for item in result.items] == [100]


def test_missing_resolver_does_not_leak_unfiltered_candidates():
    index = _Index(rows=[{"subject_id": 1}])
    result = _service(index).retrieve(
        RetrievalQuery(keywords=["test"], relation_subject_ids=[1])
    )
    assert result.available is False
    assert result.items == []
    assert result.reason == "entity_resolution_unavailable"


def test_incomplete_resolver_rows_are_fail_closed():
    index = _Index(rows=[{"subject_id": 1}])
    result = _service(index, lambda entity_type, entity_ids, token=None: [
        {"subjectId": 1, "type": 2, "nsfw": False},
    ]).retrieve(RetrievalQuery(keywords=["test"], person_ids=[7]))
    assert result.available is False
    assert result.items == []
    assert result.reason == "entity_resolution_unavailable"


@pytest.mark.parametrize("malformed", [None, "not-a-list", {"message": "ok"}, {"items": "bad"}])
def test_malformed_resolver_root_is_fail_closed(malformed):
    index = _Index(rows=[{"subject_id": 1}])
    result = _service(index, lambda entity_type, entity_ids, token=None: malformed).retrieve(
        RetrievalQuery(keywords=["test"], person_ids=[7])
    )
    assert result.available is False
    assert result.items == []
    assert result.reason == "entity_resolution_unavailable"
