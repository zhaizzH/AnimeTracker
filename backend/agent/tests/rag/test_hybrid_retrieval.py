from __future__ import annotations

from dataclasses import dataclass

from app.rag.embeddings import EmbeddingUnavailable
from app.rag.retrieval import RagRetrievalService, RetrievalCandidate, reciprocal_rank_fusion
from app.rag.schemas import RetrievalQuery


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
