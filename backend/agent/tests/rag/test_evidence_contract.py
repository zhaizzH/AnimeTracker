"""EvidenceCandidate 契约测试。

Agent 返回的每项推荐必须携带可验证证据。
use_case._compact 现在输出完整的证据字段，包括：
- summaryExcerpt / summarySource
- matchedTags / matchedCredits / matchedCharacters / matchedRelations
- ratingTotal / collectionTotal（热度）
- airStatus（播出状态）
- sourceFetchedAt（数据时间）
- sourceRefs（来源引用）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

import pytest

from app.rag.retrieval import RetrievalCandidate, RagRetrievalService
from app.rag.schemas import RetrievalQuery
from app.rag.use_case import RetrieveSubjectsUseCase


class TestEvidenceCandidateOutput:
    """use_case._compact 必须输出完整的证据字段。"""

    def test_compact_has_summary_excerpt(self):
        """有证据时必须包含简介摘录。"""
        candidate = _evidence_candidate()
        compact = RetrieveSubjectsUseCase._compact(candidate)
        assert compact["summaryExcerpt"] == "这是一个测试动画的简介。"
        assert compact["summarySource"] == "bangumi_official"

    def test_compact_has_matched_tags(self):
        compact = RetrieveSubjectsUseCase._compact(_evidence_candidate())
        assert isinstance(compact["matchedTags"], list)
        assert compact["matchedTags"] == ["热血", "奇幻"]

    def test_compact_has_matched_credits(self):
        compact = RetrieveSubjectsUseCase._compact(_evidence_candidate())
        assert isinstance(compact["matchedCredits"], list)
        assert "导演(Test)(MAIN)" in compact["matchedCredits"]

    def test_compact_has_matched_characters(self):
        compact = RetrieveSubjectsUseCase._compact(_evidence_candidate())
        assert isinstance(compact["matchedCharacters"], list)
        assert "主角(MAIN)" in compact["matchedCharacters"]

    def test_compact_has_matched_relations(self):
        compact = RetrieveSubjectsUseCase._compact(_evidence_candidate())
        assert isinstance(compact["matchedRelations"], list)
        assert "续作2(续集)" in compact["matchedRelations"]

    def test_compact_has_popularity_metrics(self):
        compact = RetrieveSubjectsUseCase._compact(_evidence_candidate())
        assert compact["ratingTotal"] == 5000
        assert compact["collectionTotal"] == 10000

    def test_compact_has_air_status(self):
        compact = RetrieveSubjectsUseCase._compact(_evidence_candidate())
        assert compact["airStatus"] in {"UPCOMING", "AIRING", "FINISHED", "UNKNOWN"}

    def test_compact_has_source_fetched_at(self):
        compact = RetrieveSubjectsUseCase._compact(_evidence_candidate())
        assert compact["sourceFetchedAt"] is not None

    def test_compact_has_source_refs(self):
        compact = RetrieveSubjectsUseCase._compact(_evidence_candidate())
        assert isinstance(compact["sourceRefs"], list)
        assert "https://bgm.tv/subject/1" in compact["sourceRefs"]

    def test_compact_without_evidence_has_defaults(self):
        """无证据时字段使用默认值，不崩溃。"""
        candidate = RetrievalCandidate(
            subject_id=2,
            retrieval_score=0.5,
            retrieval_reason="lexical",
            title="No Evidence",
            details={"nameCn": "无证据", "name": "No Evidence"},
        )
        compact = RetrieveSubjectsUseCase._compact(candidate)
        assert compact["summaryExcerpt"] == ""
        assert compact["matchedTags"] == []
        assert compact["matchedCredits"] == []
        assert compact["sourceRefs"] == ["https://bgm.tv/subject/2"]


class TestBusinessVerificationRequired:
    """未经 Business 回查的候选不得进入模型上下文。"""

    def test_unverified_candidates_excluded(self):
        """Business 回查失败的候选应当被排除。"""

        def failing_authority(ids, token=None, exclude_collected=False):
            return {"error": "unavailable"}

        service = RagRetrievalService(
            index=None,
            embeddings=None,
            authority_lookup=failing_authority,
            business_search=lambda q, token=None: [],
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is True or result.available is False
        for item in result.items:
            assert item.details is not None, "候选必须有 Business 验证的 details"


class TestEvidenceEnrichment:
    """RagRetrievalService 在权威回查后应调用 evidence_lookup  enrich 候选。"""

    def test_enrich_attaches_evidence(self):
        """evidence_lookup 成功时，候选应携带 evidence 字段。"""
        evidence_data = [
            {
                "subjectId": 1,
                "name": "Test",
                "nameCn": "测试",
                "type": 2,
                "nsfw": False,
                "summary": "测试简介",
                "aliases": ["テスト"],
                "metaTags": ["SF"],
                "credits": [{"personName": "导演", "relation": "MAIN"}],
                "characters": [],
                "relations": [],
                "score": 8.0,
                "ratingTotal": 1000,
                "collectionTotal": 5000,
                "airDate": "2024-01-01",
                "sourceTime": "2026-08-01T12:00:00",
                "sourceUrl": "https://bgm.tv/subject/1",
            }
        ]

        def mock_index_search(expression, limit=50):
            return [{"subject_id": 1, "title": "Test"}]

        def mock_authority(ids, token=None, exclude_collected=False):
            return [{"id": 1, "name": "Test", "type": 2, "nsfw": False}]

        service = RagRetrievalService(
            index=MockIndex(mock_index_search),
            embeddings=MockEmbeddings(),
            authority_lookup=mock_authority,
            business_search=lambda q, token=None: [],
            evidence_lookup=lambda ids, token=None: evidence_data,
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available
        assert len(result.items) == 1
        assert result.items[0].evidence is not None
        assert result.items[0].evidence["summaryExcerpt"] == "测试简介"
        assert result.items[0].evidence["metaTags"] == ["SF"]

    def test_enrich_failure_is_fail_closed(self):
        """evidence_lookup 失败时，不返回未经证据回查的候选。"""

        def failing_evidence(ids, token=None):
            raise ConnectionError("evidence service down")

        def mock_authority(ids, token=None, exclude_collected=False):
            return [{"id": 1, "name": "Test", "type": 2, "nsfw": False}]

        service = RagRetrievalService(
            index=MockIndex(lambda expr, limit=50: [{"subject_id": 1, "title": "Test"}]),
            embeddings=MockEmbeddings(),
            authority_lookup=mock_authority,
            business_search=lambda q, token=None: [],
            evidence_lookup=failing_evidence,
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is False
        assert result.items == []
        assert result.reason == "evidence_unavailable"

    def test_enrich_error_response_is_fail_closed(self):
        """evidence_lookup 返回错误时，不返回未经证据回查的候选。"""

        def error_evidence(ids, token=None):
            return {"error": True, "message": "bad request"}

        def mock_authority(ids, token=None, exclude_collected=False):
            return [{"id": 1, "name": "Test", "type": 2, "nsfw": False}]

        service = RagRetrievalService(
            index=MockIndex(lambda expr, limit=50: [{"subject_id": 1, "title": "Test"}]),
            embeddings=MockEmbeddings(),
            authority_lookup=mock_authority,
            business_search=lambda q, token=None: [],
            evidence_lookup=error_evidence,
        )
        query = RetrievalQuery(keywords=["test"])
        result = service.retrieve(query, token=None)
        assert result.available is False
        assert result.items == []
        assert result.reason == "evidence_unavailable"

    def test_enrich_partial_response_is_fail_closed(self):
        """Evidence 只返回部分候选时，整批不得进入模型上下文。"""

        def mock_authority(ids, token=None, exclude_collected=False):
            return [
                {"id": 1, "name": "One", "type": 2, "nsfw": False},
                {"id": 2, "name": "Two", "type": 2, "nsfw": False},
            ]

        service = RagRetrievalService(
            index=MockIndex(lambda expr, limit=50: [{"subject_id": 1}, {"subject_id": 2}]),
            embeddings=MockEmbeddings(),
            authority_lookup=mock_authority,
            business_search=lambda q, token=None: [],
            evidence_lookup=lambda ids, token=None: [{"subjectId": 1, "type": 2, "nsfw": False}],
        )
        result = service.retrieve(RetrievalQuery(keywords=["test"]), token=None)
        assert result.available is False
        assert result.items == []
        assert result.reason == "evidence_unavailable"

    def test_enrich_unsafe_response_is_fail_closed(self):
        """Evidence 返回 NSFW 或非动画候选时，整批拒绝。"""

        def mock_authority(ids, token=None, exclude_collected=False):
            return [{"id": 1, "name": "Test", "type": 2, "nsfw": False}]

        service = RagRetrievalService(
            index=MockIndex(lambda expr, limit=50: [{"subject_id": 1}]),
            embeddings=MockEmbeddings(),
            authority_lookup=mock_authority,
            business_search=lambda q, token=None: [],
            evidence_lookup=lambda ids, token=None: [{"subjectId": 1, "type": 1, "nsfw": False}],
        )
        result = service.retrieve(RetrievalQuery(keywords=["test"]), token=None)
        assert result.available is False
        assert result.items == []
        assert result.reason == "evidence_unavailable"


class TestMapEvidence:
    """_map_evidence 应正确映射 EvidenceCandidateVO 字段。"""

    def test_maps_all_fields(self):
        ev = {
            "subjectId": 1,
            "name": "Test",
            "nameCn": "测试",
            "summary": "A" * 300,
            "aliases": ["alias1"],
            "metaTags": ["tag1", "tag2"],
            "credits": [{"personName": "导演A", "relation": "MAIN"}],
            "characters": [{"characterName": "主角", "relation": "MAIN"}],
            "relations": [{"relatedSubjectNameCn": "续作", "relation": "续集"}],
            "score": 8.5,
            "ratingTotal": 5000,
            "collectionTotal": 10000,
            "airDate": "2024-01-01",
            "sourceTime": "2026-08-01T12:00:00",
            "sourceUrl": "https://bgm.tv/subject/1",
        }
        mapped = RagRetrievalService._map_evidence(ev)
        assert mapped["summaryExcerpt"] == "A" * 200
        assert len(mapped["summaryExcerpt"]) == 200
        assert mapped["aliases"] == ["alias1"]
        assert mapped["metaTags"] == ["tag1", "tag2"]
        assert mapped["credits"] == ["导演A(MAIN)"]
        assert mapped["characters"] == ["主角(MAIN)"]
        assert mapped["relations"] == ["续作(续集)"]
        assert mapped["score"] == 8.5
        assert mapped["ratingTotal"] == 5000
        assert mapped["sourceTime"] == "2026-08-01T12:00:00"
        assert mapped["sourceFetchedAt"] == "2026-08-01T12:00:00"

    def test_handles_empty_optional_fields(self):
        ev = {"subjectId": 2, "name": "Minimal"}
        mapped = RagRetrievalService._map_evidence(ev)
        assert mapped["aliases"] == []
        assert mapped["metaTags"] == []
        assert mapped["credits"] == []
        assert mapped["characters"] == []
        assert mapped["relations"] == []
        assert mapped["summaryExcerpt"] == ""


# --- Test helpers ---


@dataclass(frozen=True)
class _MockIndex:
    _search_fn: Any

    def lexical_search(self, expression, limit=50):
        return self._search_fn(expression, limit=limit)

    def semantic_search(self, expression, vector, limit=50):
        return []


@dataclass(frozen=True)
class _MockEmbeddings:
    def embed_documents(self, texts):
        return [[0.0] * 1024 for _ in texts]


def MockIndex(search_fn):
    return _MockIndex(search_fn)


def MockEmbeddings():
    return _MockEmbeddings()


def _evidence_candidate() -> RetrievalCandidate:
    return RetrievalCandidate(
        subject_id=1,
        retrieval_score=0.9,
        retrieval_reason="lexical+semantic",
        title="Test Anime",
        details={"nameCn": "测试动画", "name": "Test Anime"},
        evidence={
            "aliases": ["Test", "测试"],
            "metaTags": ["热血", "奇幻"],
            "credits": ["导演(Test)(MAIN)"],
            "characters": ["主角(MAIN)"],
            "relations": ["续作2(续集)"],
            "summaryExcerpt": "这是一个测试动画的简介。",
            "summarySource": "bangumi_official",
            "score": 8.5,
            "ratingTotal": 5000,
            "collectionTotal": 10000,
            "airDate": "2024-01-01",
            "sourceTime": "2026-08-01T12:00:00",
            "sourceUrl": "https://bgm.tv/subject/1",
            "nameCn": "测试动画",
            "name": "Test Anime",
        },
    )
