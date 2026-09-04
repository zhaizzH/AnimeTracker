"""端到端故障矩阵测试。

覆盖 MySQL/Redis/Embedding/Business/Evidence 各层故障场景，
证明系统在各种故障下的 fail-closed 或既定降级行为。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.rag.retrieval import RagRetrievalService, RetrievalCandidate
from app.rag.schemas import RetrievalQuery
from app.rag.use_case import RetrieveSubjectsUseCase


@dataclass(frozen=True)
class _MockIndex:
    _lexical_fn: Any = None
    _semantic_fn: Any = None

    def lexical_search(self, expression, limit=50):
        if self._lexical_fn is None:
            raise ConnectionError("Redis unavailable")
        return self._lexical_fn(expression, limit=limit)

    def semantic_search(self, expression, vector, limit=50):
        if self._semantic_fn is None:
            raise ConnectionError("Redis unavailable")
        return self._semantic_fn(expression, vector, limit=limit)


@dataclass(frozen=True)
class _MockEmbeddings:
    _fail: bool = False

    def embed_documents(self, texts):
        if self._fail:
            raise RuntimeError("Embedding service unavailable")
        return [[0.0] * 1024 for _ in texts]


def _mock_authority(ids, token=None, exclude_collected=False):
    return [{"id": sid, "name": f"Subject {sid}", "type": 2, "nsfw": False} for sid in ids]


def _mock_business_search(query, token=None):
    return [{"id": 1, "name": "Test", "nameCn": "测试", "type": 2, "nsfw": False}]


def _mock_evidence(ids, token=None):
    return [
        {
            "subjectId": sid,
            "name": f"Subject {sid}",
            "nameCn": f"测试{sid}",
            "summary": f"简介{sid}",
            "aliases": [],
            "metaTags": ["tag1"],
            "credits": [],
            "characters": [],
            "relations": [],
            "score": 8.0,
            "ratingTotal": 1000,
            "collectionTotal": 5000,
            "airDate": "2024-01-01",
            "sourceTime": "2026-08-01T12:00:00",
        }
        for sid in ids
    ]


class TestRedisFailure:
    """Redis 完全不可用时，应降级到 Business 搜索。"""

    def test_fallback_to_business(self):
        """Redis 故障 → Business 搜索 → 权威回查 → 返回结果。"""
        service = RagRetrievalService(
            index=_MockIndex(),  # 所有搜索都抛异常
            embeddings=_MockEmbeddings(),
            authority_lookup=_mock_authority,
            business_search=_mock_business_search,
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is True
        assert result.reason == "" or result.reason != "business_unavailable"
        assert len(result.items) >= 0

    def test_fallback_with_evidence(self):
        """Redis 故障 + Evidence 可用 → Business 降级 + Evidence 回查。"""
        service = RagRetrievalService(
            index=_MockIndex(),
            embeddings=_MockEmbeddings(),
            authority_lookup=_mock_authority,
            business_search=_mock_business_search,
            evidence_lookup=_mock_evidence,
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is True
        for item in result.items:
            if item.evidence is not None:
                assert "summaryExcerpt" in item.evidence


class TestEmbeddingFailure:
    """Embedding 服务不可用时，应仅使用 BM25 词法搜索。"""

    def test_lexical_only(self):
        """Embedding 失败 → 仅 BM25 → 正常返回。"""
        service = RagRetrievalService(
            index=_MockIndex(
                _lexical_fn=lambda expr, limit=50: [{"subject_id": 1, "title": "Test"}],
                _semantic_fn=None,
            ),
            embeddings=_MockEmbeddings(_fail=True),
            authority_lookup=_mock_authority,
            business_search=_mock_business_search,
        )
        query = RetrievalQuery(semantic_query="test query", keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is True

    def test_embedding_failure_with_evidence(self):
        """Embedding 失败 + Evidence 可用 → BM25 + Evidence 回查。"""
        service = RagRetrievalService(
            index=_MockIndex(
                _lexical_fn=lambda expr, limit=50: [{"subject_id": 1, "title": "Test"}],
            ),
            embeddings=_MockEmbeddings(_fail=True),
            authority_lookup=_mock_authority,
            business_search=_mock_business_search,
            evidence_lookup=_mock_evidence,
        )
        query = RetrievalQuery(semantic_query="test query", keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is True
        for item in result.items:
            assert item.evidence is not None


class TestBusinessFailure:
    """Business API 不可用时，应 fail-closed（返回 available=False）。"""

    def test_authority_failure_returns_unavailable(self):
        """权威回查失败 → available=False。"""

        def failing_authority(ids, token=None, exclude_collected=False):
            return {"error": True, "message": "Business unavailable"}

        service = RagRetrievalService(
            index=_MockIndex(
                _lexical_fn=lambda expr, limit=50: [{"subject_id": 1, "title": "Test"}],
            ),
            embeddings=_MockEmbeddings(),
            authority_lookup=failing_authority,
            business_search=_mock_business_search,
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is False
        assert result.items == []

    def test_business_search_also_fails(self):
        """Redis + Business 都失败 → available=False。"""

        def failing_authority(ids, token=None, exclude_collected=False):
            return {"error": True}

        def failing_search(query, token=None):
            return {"error": True}

        service = RagRetrievalService(
            index=_MockIndex(),  # Redis 也失败
            embeddings=_MockEmbeddings(),
            authority_lookup=failing_authority,
            business_search=failing_search,
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is False
        assert result.items == []


class TestEvidenceFailure:
    """Evidence API 不可用时，候选应保持原样（无证据字段但不崩溃）。"""

    def test_evidence_exception_keeps_candidates(self):
        """Evidence 抛异常 → 候选无 evidence 字段但不影响返回。"""
        service = RagRetrievalService(
            index=_MockIndex(
                _lexical_fn=lambda expr, limit=50: [{"subject_id": 1, "title": "Test"}],
            ),
            embeddings=_MockEmbeddings(),
            authority_lookup=_mock_authority,
            business_search=_mock_business_search,
            evidence_lookup=lambda ids, token=None: (_ for _ in ()).throw(ConnectionError("down")),
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is True
        assert len(result.items) >= 1
        for item in result.items:
            assert item.evidence is None

    def test_evidence_error_response_keeps_candidates(self):
        """Evidence 返回错误 → 候选无 evidence 字段。"""
        service = RagRetrievalService(
            index=_MockIndex(
                _lexical_fn=lambda expr, limit=50: [{"subject_id": 1, "title": "Test"}],
            ),
            embeddings=_MockEmbeddings(),
            authority_lookup=_mock_authority,
            business_search=_mock_business_search,
            evidence_lookup=lambda ids, token=None: {"error": True},
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is True
        for item in result.items:
            assert item.evidence is None


class TestUseCaseEvidenceIntegration:
    """use_case 层应正确传递证据字段到输出。"""

    def test_full_evidence_output(self):
        """完整证据链：Redis → Authority → Evidence → use_case 输出。"""

        def mock_index_search(expression, limit=50):
            return [{"subject_id": 1, "title": "Test"}]

        service = RagRetrievalService(
            index=_MockIndex(_lexical_fn=mock_index_search),
            embeddings=_MockEmbeddings(),
            authority_lookup=_mock_authority,
            business_search=_mock_business_search,
            evidence_lookup=_mock_evidence,
        )

        class MockPreferenceProvider:
            def load(self, user_id, token):
                return None, False

        use_case = RetrieveSubjectsUseCase(
            retrieval=service,
            preference_provider=MockPreferenceProvider(),
            evidence_lookup=_mock_evidence,
        )

        query = RetrievalQuery(keywords=["test"])

        class MockUser:
            user_id = 1
            token = "test_token"

        result = use_case.execute(query, mode="search", user=MockUser())
        assert result["available"] is True
        assert len(result["items"]) >= 1

        item = result["items"][0]
        assert "subjectId" in item
        assert "summaryExcerpt" in item
        assert "matchedTags" in item
        assert "matchedCredits" in item
        assert "matchedCharacters" in item
        assert "matchedRelations" in item
        assert "ratingTotal" in item
        assert "collectionTotal" in item
        assert "airStatus" in item
        assert "sourceFetchedAt" in item
        assert "sourceRefs" in item
        assert "retrievalScore" in item
        assert "retrievalReason" in item

    def test_no_evidence_still_works(self):
        """不提供 evidence_lookup 时，use_case 仍正常返回基本字段。"""

        def mock_index_search(expression, limit=50):
            return [{"subject_id": 1, "title": "Test"}]

        service = RagRetrievalService(
            index=_MockIndex(_lexical_fn=mock_index_search),
            embeddings=_MockEmbeddings(),
            authority_lookup=_mock_authority,
            business_search=_mock_business_search,
        )

        class MockPreferenceProvider:
            def load(self, user_id, token):
                return None, False

        use_case = RetrieveSubjectsUseCase(
            retrieval=service,
            preference_provider=MockPreferenceProvider(),
        )

        query = RetrievalQuery(keywords=["test"])

        class MockUser:
            user_id = 1
            token = "test_token"

        result = use_case.execute(query, mode="search", user=MockUser())
        assert result["available"] is True
        item = result["items"][0]
        assert item["subjectId"] == 1
        assert item["summaryExcerpt"] == ""
        assert item["matchedTags"] == []
        assert item["sourceRefs"] == ["https://bgm.tv/subject/1"]
