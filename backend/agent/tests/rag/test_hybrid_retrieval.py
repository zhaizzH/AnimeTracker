from __future__ import annotations

from dataclasses import dataclass

from app.rag.embeddings import EmbeddingUnavailable
from app.rag.redis_index import vector_bytes
from app.rag.retrieval import RagRetrievalService, RetrievalCandidate, _items, reciprocal_rank_fusion
from app.rag.schemas import RetrievalQuery
from app.rag.user_profile import UserPreference


def candidate(subject_id: int) -> RetrievalCandidate:
    return RetrievalCandidate(subject_id=subject_id, retrieval_score=0.0, retrieval_reason="test")


def test_rrf_is_deterministic():
    """Changing rank fusion or ordering would make the same inputs unstable."""
    lexical = [candidate(1), candidate(2)]
    semantic = [candidate(2), candidate(3)]

    assert [item.subject_id for item in reciprocal_rank_fusion(lexical, semantic, k=60)] == [2, 1, 3]


@dataclass
class FakeIndex:
    lexical: list[dict]
    semantic: list[dict]
    fail: bool = False

    def lexical_search(self, _expression: str, *, limit: int = 50):
        if self.fail:
            raise RuntimeError("redis unavailable")
        return self.lexical[:limit]

    def semantic_search(self, _expression: str, _vector: list[float], *, limit: int = 50):
        if self.fail:
            raise RuntimeError("redis unavailable")
        return self.semantic[:limit]


class FailingEmbedding:
    def embed_documents(self, _texts):
        raise EmbeddingUnavailable("offline")


class CapturingIndex(FakeIndex):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.expressions: list[str] = []

    def lexical_search(self, expression: str, *, limit: int = 50):
        self.expressions.append(expression)
        return super().lexical_search(expression, limit=limit)


class VectorEmbedding:
    def embed_documents(self, _texts):
        return [[0.0] * 1024]


def _authority(subject_ids, **_kwargs):
    return {
        "items": [
            {
                "id": subject_id,
                "name": f"动画 {subject_id}",
                "nameCn": f"动画 {subject_id}",
                "score": 8.0,
                "ratingTotal": 100,
                "collectionTotal": 1000,
                "airDate": "2024-01-01",
                "type": 2,
                "nsfw": False,
            }
            for subject_id in subject_ids
        ]
    }


def test_embedding_failure_falls_back_to_authoritative_lexical_results():
    """Without fallback an embedding outage would discard a valid keyword search."""
    service = RagRetrievalService(
        FakeIndex(lexical=[{"subject_id": 7, "title": "动画 7"}], semantic=[]),
        FailingEmbedding(),
        authority_lookup=_authority,
    )

    result = service.retrieve(RetrievalQuery(semantic_query="治愈", keywords=["治愈"]), "search")

    assert result.available is True
    assert [item.subject_id for item in result.items] == [7]
    assert result.items[0].details["id"] == 7
    assert "lexical" in result.items[0].retrieval_reason


def test_semantic_embedding_failure_uses_escaped_text_not_a_wildcard_search():
    """An embedding outage must not broaden a semantic-only request to arbitrary indexed subjects."""
    index = CapturingIndex(lexical=[{"subject_id": 7, "title": "动画 7"}], semantic=[])
    service = RagRetrievalService(index, FailingEmbedding(), authority_lookup=_authority)

    result = service.retrieve(RetrievalQuery(semantic_query="*)|(@nsfw:{true}"), "search")

    assert [item.subject_id for item in result.items] == [7]
    assert index.expressions == [r"(@title:(\*\)\|\(\@nsfw\:\{true\})|@aliases:(\*\)\|\(\@nsfw\:\{true\})|@summary:(\*\)\|\(\@nsfw\:\{true\}))"]


def test_structured_query_without_semantics_uses_lexical_filter_search():
    """A valid structured-only query must not be discarded before it reaches RediSearch."""
    service = RagRetrievalService(
        FakeIndex(lexical=[{"subject_id": 7, "title": "动画 7"}], semantic=[]),
        VectorEmbedding(),
        authority_lookup=_authority,
    )

    result = service.retrieve(RetrievalQuery(year_from=2024), "search")

    assert result.available is True
    assert [item.subject_id for item in result.items] == [7]


def test_meta_tag_filter_uses_a_single_escaped_tag_clause():
    """Treating tag filters as free text would miss the TAG index semantics."""
    index = CapturingIndex(lexical=[{"subject_id": 7, "title": "动画 7"}], semantic=[])
    service = RagRetrievalService(index, VectorEmbedding(), authority_lookup=_authority)

    service.retrieve(RetrievalQuery(meta_tags=["科幻,太空", "校园|日常"]), "search")

    assert index.expressions == [r"@meta_tags:{科幻,太空} @meta_tags:{校园\|日常}"]


def test_business_failure_never_returns_unvalidated_redis_candidates():
    """Removing the authority gate would leak stale Redis data to the model."""
    service = RagRetrievalService(
        FakeIndex(lexical=[{"subject_id": 7, "title": "动画 7"}], semantic=[]),
        VectorEmbedding(),
        authority_lookup=lambda *_args, **_kwargs: {"error": True, "message": "backend down"},
    )

    result = service.retrieve(RetrievalQuery(keywords=["治愈"]), "search")

    assert result.available is False
    assert result.items == []
    assert result.reason == "business_unavailable"


def test_redis_failure_uses_authoritative_business_fallback():
    """Removing the fallback would make a Redis outage a complete retrieval outage."""
    service = RagRetrievalService(
        FakeIndex(lexical=[], semantic=[], fail=True),
        VectorEmbedding(),
        authority_lookup=_authority,
        business_search=lambda _query, **_kwargs: _authority([9]),
    )

    result = service.retrieve(RetrievalQuery(keywords=["治愈"]), "search")

    assert result.available is True
    assert [item.subject_id for item in result.items] == [9]
    assert result.items[0].retrieval_reason == "business_fallback"


def test_business_fallback_still_requires_batch_visibility_check():
    """A Redis outage must not bypass the user-specific collected/visibility gate."""
    service = RagRetrievalService(
        FakeIndex(lexical=[], semantic=[], fail=True),
        VectorEmbedding(),
        authority_lookup=lambda *_args, **_kwargs: {"error": True, "message": "batch unavailable"},
        business_search=lambda _query, **_kwargs: _authority([9]),
    )

    result = service.retrieve(RetrievalQuery(keywords=["治愈"]), "search")

    assert result.available is False
    assert result.items == []
    assert result.reason == "business_unavailable"


def test_business_fallback_uses_batch_data_when_list_payload_has_no_nsfw_field():
    """SubjectListVO is incomplete, so only batch data may decide the final safety gate."""
    service = RagRetrievalService(
        FakeIndex(lexical=[], semantic=[], fail=True),
        VectorEmbedding(),
        authority_lookup=_authority,
        business_search=lambda _query, **_kwargs: {"content": [{"id": 9, "name": "动画 9", "type": 2}]},
    )

    result = service.retrieve(RetrievalQuery(keywords=["治愈"]), "search")

    assert [item.subject_id for item in result.items] == [9]


def test_authoritative_results_keep_only_safe_anime_candidates():
    service = RagRetrievalService(
        FakeIndex(lexical=[{"subject_id": 7, "title": "动画 7"}], semantic=[]),
        VectorEmbedding(),
        authority_lookup=lambda *_args, **_kwargs: {
            "items": [
                {"id": 7, "name": "unsafe", "type": 1, "nsfw": False},
                {"id": 8, "name": "unsafe", "type": 2, "nsfw": True},
            ]
        },
    )

    result = service.retrieve(RetrievalQuery(keywords=["治愈"]), "search")

    assert result.available is True
    assert result.items == []


def test_relaxation_continues_when_first_redis_candidates_fail_authority_gate():
    """Stopping at raw Redis candidates would hide a valid result behind a stale first batch."""
    class RelaxingIndex:
        def __init__(self):
            self.calls = 0

        def lexical_search(self, _expression, *, limit=50):
            self.calls += 1
            return [{"subject_id": 7, "title": "旧候选"}] if self.calls == 1 else [{"subject_id": 8, "title": "可用候选"}]

        def semantic_search(self, *_args, **_kwargs):
            return []

    authority_calls = 0

    def authority(subject_ids, **_kwargs):
        nonlocal authority_calls
        authority_calls += 1
        return {"items": []} if subject_ids == [7] else _authority([8])

    service = RagRetrievalService(RelaxingIndex(), VectorEmbedding(), authority_lookup=authority)

    result = service.retrieve(RetrievalQuery(keywords=["治愈"], score_min=8.0), "search")

    assert [item.subject_id for item in result.items] == [8]
    assert authority_calls == 2


def test_user_profile_vector_reranks_candidates_by_cosine_similarity():
    """Removing profile cosine would keep generic order even when vectors strongly disagree."""
    service = RagRetrievalService(
        FakeIndex(
            lexical=[
                {"subject_id": 7, "title": "非偏好", "vector": [0.0, 1.0]},
                {"subject_id": 8, "title": "偏好", "vector": [1.0, 0.0]},
            ],
            semantic=[],
        ),
        VectorEmbedding(),
        authority_lookup=_authority,
    )
    preference = UserPreference((1.0, 0.0), (), 3, "version")

    result = service.retrieve(RetrievalQuery(keywords=["治愈"]), "search", preference=preference)

    assert [item.subject_id for item in result.items] == [8, 7]


def test_missing_profile_marks_cold_start_notice():
    """Without a notice callers cannot explain why early recommendations are generic."""
    service = RagRetrievalService(
        FakeIndex(lexical=[{"subject_id": 7, "title": "动画 7"}], semantic=[]),
        VectorEmbedding(),
        authority_lookup=_authority,
    )

    result = service.retrieve(RetrievalQuery(keywords=["治愈"]), "search", personalization_missing=True)

    assert result.personalization_notice == "基于你当前的收藏还不多，先给你看热门"


def test_redis_binary_subject_vector_is_available_for_profile_reranking():
    """Converting Redis Float32 bytes to text would silently disable production personalization."""
    rows = _items([1, b"test:rag:subject:v1:7", [b"vector", vector_bytes([0.0] * 1024)]])

    assert rows[0]["vector"] == [0.0] * 1024
