from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

from app.rag.retrieval import RagRetrievalService
from app.rag.schemas import RetrievalQuery


RetrievalMode = Literal["search", "discover", "recommend"]


@dataclass
class RetrieveSubjectsUseCase:
    retrieval: RagRetrievalService
    preference_provider: Any
    business_searches: Mapping[RetrievalMode, Any] = field(default_factory=dict)

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
        )
        return {
            "available": result.available,
            "reason": result.reason,
            "personalizationNotice": result.personalization_notice,
            "items": [self._compact(item) for item in result.items],
        }

    @staticmethod
    def _compact(candidate) -> dict:
        details = candidate.details if isinstance(candidate.details, Mapping) else {}
        return {
            "subjectId": candidate.subject_id,
            "title": str(details.get("nameCn") or details.get("name") or candidate.title),
            "score": candidate.retrieval_score,
            "reason": candidate.retrieval_reason,
        }
