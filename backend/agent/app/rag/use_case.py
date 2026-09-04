from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Mapping

from app.rag.retrieval import RagRetrievalService, RetrievalCandidate
from app.rag.schemas import RetrievalQuery


RetrievalMode = Literal["search", "discover", "recommend"]


@dataclass
class RetrieveSubjectsUseCase:
    retrieval: RagRetrievalService
    preference_provider: Any
    business_searches: Mapping[RetrievalMode, Any] = field(default_factory=dict)
    evidence_lookup: Any = None

    def execute(self, query: RetrievalQuery, *, mode: RetrievalMode, user) -> dict:
        preference, missing = (None, False)
        if mode == "recommend":
            preference, missing = self.preference_provider.load(user.user_id, user.token)
        if mode == "recommend" and preference is not None:
            query = query.model_copy(update={"exclude_subject_ids": list(preference.exclude_subject_ids)})
        result = self.retrieval.retrieve(
            query,
            token=user.token,
            preference=preference,
            personalization_missing=missing,
            business_search=self.business_searches.get(mode),
            evidence_lookup=self.evidence_lookup,
        )
        return {
            "available": result.available,
            "reason": result.reason,
            "personalizationNotice": result.personalization_notice,
            "items": [self._compact(item) for item in result.items],
        }

    @staticmethod
    def _compact(candidate: RetrievalCandidate) -> dict:
        details = candidate.details if isinstance(candidate.details, Mapping) else {}
        evidence = candidate.evidence if isinstance(candidate.evidence, Mapping) else {}
        title = str(details.get("nameCn") or details.get("name") or candidate.title)
        air_date = evidence.get("airDate") or details.get("airDate")
        air_status = _infer_air_status(air_date)
        source_time = evidence.get("sourceFetchedAt") or evidence.get("sourceTime")
        source_fetched_at = _parse_datetime(source_time)
        source_refs = _source_refs(candidate, evidence)
        return {
            "subjectId": candidate.subject_id,
            "title": title,
            "nameCn": evidence.get("nameCn") or details.get("nameCn"),
            "name": evidence.get("name") or details.get("name"),
            "aliases": evidence.get("aliases", []),
            "summaryExcerpt": evidence.get("summaryExcerpt", ""),
            "summarySource": evidence.get("summarySource", ""),
            "matchedTags": evidence.get("metaTags", []),
            "matchedCredits": evidence.get("credits", []),
            "matchedCharacters": evidence.get("characters", []),
            "matchedRelations": evidence.get("relations", []),
            "score": evidence.get("score") or details.get("score"),
            "ratingTotal": evidence.get("ratingTotal") if evidence.get("ratingTotal") is not None else details.get("ratingTotal"),
            "collectionTotal": evidence.get("collectionTotal") if evidence.get("collectionTotal") is not None else details.get("collectionTotal"),
            "airStatus": air_status,
            "sourceFetchedAt": source_fetched_at.isoformat() if source_fetched_at else None,
            "retrievalScore": candidate.retrieval_score,
            "retrievalReason": candidate.retrieval_reason,
            "sourceRefs": source_refs,
        }


def _infer_air_status(air_date: Any) -> str:
    """根据播出日期推断播出状态。"""
    parsed = _parse_date(air_date)
    if parsed is None:
        return "UNKNOWN"
    today = datetime.today().date()
    if parsed > today:
        return "UPCOMING"
    return "FINISHED"


def _parse_date(value: Any):
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _source_refs(candidate: RetrievalCandidate, evidence: Mapping[str, Any]) -> list[str]:
    """只输出 Business 提供的上游来源引用；无证据时保留旧兼容链接。"""
    source_url = evidence.get("sourceUrl") or evidence.get("sourceURL")
    if isinstance(source_url, str) and source_url.strip():
        return [source_url.strip()]
    source_id = evidence.get("sourceId") or evidence.get("bangumiId")
    try:
        if source_id is not None and int(source_id) > 0:
            return [f"https://bgm.tv/subject/{int(source_id)}"]
    except (TypeError, ValueError):
        pass
    if not evidence:
        return [f"https://bgm.tv/subject/{candidate.subject_id}"]
    return []
