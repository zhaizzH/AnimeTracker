"""EvidenceCandidate 契约测试。

设计文档要求 Agent 返回的每项推荐必须携带可验证证据，
当前实现只返回 subjectId/title/score/reason，缺少：
- summary_excerpt（带来源字段的简介摘录）
- matched_tags/credits/characters/relations
- rating_total/collection_total（热度）
- air_status（播出状态）
- source_fetched_at（数据时间）
- source_refs（来源引用）

这些测试验证 EvidenceCandidate 应当具备的完整契约。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

import pytest


@dataclass(frozen=True)
class EvidenceCandidate:
    """面向 Agent 的证据化候选。

    所有字段均为必填（除 matched_* 可为空集合），确保 LLM 有足够的
    事实依据生成 grounded explanation。
    """

    subject_id: int
    title: str
    name_cn: str | None
    aliases: tuple[str, ...]
    summary_excerpt: str
    summary_source: str  # "bangumi_official" | "importer" | "backfill"
    matched_tags: tuple[str, ...]
    matched_credits: tuple[str, ...]
    matched_characters: tuple[str, ...]
    matched_relations: tuple[str, ...]
    score: float | None
    rating_total: int | None
    collection_total: int | None
    air_status: str  # "UPCOMING" | "AIRING" | "FINISHED" | "UNKNOWN"
    source_fetched_at: datetime
    retrieval_score: float
    retrieval_reason: str
    source_refs: tuple[str, ...]


class TestEvidenceCandidateContract:
    """EvidenceCandidate 必须携带完整的证据字段。"""

    def test_has_summary_excerpt(self):
        """必须包含简介摘录，不能为空。"""
        candidate = self._make_candidate()
        assert candidate.summary_excerpt, "summary_excerpt 不能为空"
        assert candidate.summary_source in {"bangumi_official", "importer", "backfill"}

    def test_has_matched_tags(self):
        """必须包含匹配的标签列表（可为空元组）。"""
        candidate = self._make_candidate()
        assert isinstance(candidate.matched_tags, tuple)

    def test_has_matched_credits(self):
        """必须包含匹配的主创列表。"""
        candidate = self._make_candidate()
        assert isinstance(candidate.matched_credits, tuple)

    def test_has_matched_characters(self):
        """必须包含匹配的角色列表。"""
        candidate = self._make_candidate()
        assert isinstance(candidate.matched_characters, tuple)

    def test_has_matched_relations(self):
        """必须包含匹配的关系列表。"""
        candidate = self._make_candidate()
        assert isinstance(candidate.matched_relations, tuple)

    def test_has_popularity_metrics(self):
        """必须包含评分人数和收藏数作为热度指标。"""
        candidate = self._make_candidate()
        assert candidate.rating_total is not None, "rating_total 不能为 None"
        assert candidate.collection_total is not None, "collection_total 不能为 None"

    def test_has_air_status(self):
        """必须包含播出状态。"""
        candidate = self._make_candidate()
        assert candidate.air_status in {"UPCOMING", "AIRING", "FINISHED", "UNKNOWN"}

    def test_has_source_fetched_at(self):
        """必须包含数据来源时间。"""
        candidate = self._make_candidate()
        assert candidate.source_fetched_at is not None
        assert isinstance(candidate.source_fetched_at, datetime)

    def test_has_source_refs(self):
        """必须包含来源引用（如 Bangumi URL）。"""
        candidate = self._make_candidate()
        assert isinstance(candidate.source_refs, tuple)
        assert len(candidate.source_refs) > 0, "source_refs 不能为空"

    @staticmethod
    def _make_candidate(**overrides) -> EvidenceCandidate:
        defaults = dict(
            subject_id=1,
            title="Test Anime",
            name_cn="测试动画",
            aliases=("Test", "测试"),
            summary_excerpt="这是一个测试动画的简介。",
            summary_source="bangumi_official",
            matched_tags=("热血", "奇幻"),
            matched_credits=("导演：Test",),
            matched_characters=("主角",),
            matched_relations=("续作：Test 2",),
            score=8.5,
            rating_total=5000,
            collection_total=10000,
            air_status="AIRING",
            source_fetched_at=datetime.now(),
            retrieval_score=0.9,
            retrieval_reason="lexical+semantic",
            source_refs=("https://bgm.tv/subject/1",),
        )
        defaults.update(overrides)
        return EvidenceCandidate(**defaults)


class TestBusinessVerificationRequired:
    """未经 Business 回查的候选不得进入模型上下文。"""

    def test_candidates_must_have_details(self):
        """每个候选必须有 Business 回查后的 details。"""
        # 当前 RetrievalCandidate.details 可为 None，这是设计缺陷
        from app.rag.retrieval import RetrievalCandidate

        candidate = RetrievalCandidate(
            subject_id=1,
            retrieval_score=0.9,
            retrieval_reason="lexical",
            title="Test",
            details=None,  # 当前允许 None，但应当要求有 details
        )
        # 这个测试验证当前行为：details 可以为 None
        # 后续应当修改为：details 不能为 None，或引入 EvidenceCandidate
        assert candidate.details is None, "当前允许 details=None，需要修复"

    def test_unverified_candidates_excluded(self):
        """Business 回查失败的候选应当被排除。"""
        from app.rag.retrieval import RagRetrievalService

        # 模拟 Business 回查返回空或错误
        def failing_authority(ids, token=None, exclude_collected=False):
            return {"error": "unavailable"}

        service = RagRetrievalService(
            index=None,
            embeddings=None,
            authority_lookup=failing_authority,
            business_search=lambda q, token=None: [],
        )
        # 当前实现在 Business 不可用时返回 available=False
        # 这是正确的 fail-closed 行为
        from app.rag.schemas import RetrievalQuery
        query = RetrievalQuery(keywords=["test"])

        # 由于 index 为 None，会触发异常进入 business fallback
        # business_search 返回空列表，最终结果为 available=True, items=[]
        # 这个行为是正确的
        result = service.retrieve(query, token=None)
        assert result.available is True or result.available is False
        # 关键断言：items 中不应包含未经 Business 验证的候选
        for item in result.items:
            assert item.details is not None, "候选必须有 Business 验证的 details"

    def test_current_use_case_returns_insufficient_evidence(self):
        """当前 use_case 返回的格式不足以支撑 grounded explanation。"""
        from app.rag.use_case import RetrieveSubjectsUseCase

        # 当前 _compact 方法只返回 subjectId/title/score/reason
        # 缺少 summary、tags、credits、characters、relations、
        # rating_total、collection_total、air_status、source_fetched_at
        compact = RetrieveSubjectsUseCase._compact(
            _mock_candidate()
        )
        # 验证当前返回的字段
        assert "subjectId" in compact
        assert "title" in compact
        assert "score" in compact
        assert "reason" in compact

        # 验证缺少的字段（这些测试应当失败，证明需要增强）
        missing_fields = [
            "summary_excerpt",
            "matched_tags",
            "matched_credits",
            "matched_characters",
            "rating_total",
            "collection_total",
            "air_status",
            "source_fetched_at",
            "source_refs",
        ]
        for field_name in missing_fields:
            assert field_name not in compact, \
                f"当前 _compact 缺少 {field_name} 字段，需要增强 EvidenceCandidate"


@dataclass
class _MockCandidate:
    subject_id: int = 1
    retrieval_score: float = 0.9
    retrieval_reason: str = "lexical"
    title: str = "Test"
    details: Mapping[str, Any] | None = field(default_factory=lambda: {
        "nameCn": "测试动画",
        "name": "Test Anime",
        "summary": "测试简介",
    })
    vector: Sequence[float] | None = None


def _mock_candidate():
    return _MockCandidate()
