from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import re
from typing import Iterable

from .schema import EvalCase


_SYNONYMS = {
    "治愈": "healing", "日常": "slice", "科幻": "sciencefiction", "机甲": "mecha",
    "悬疑": "mystery", "校园": "school", "恋爱": "romance", "冒险": "adventure",
}
_SAFETY_OUTCOMES = {
    "nsfw": ("safe_fallback", None),
    "non_anime": ("safe_fallback", None),
    "redis_injection": (None, "REDIS_QUERY_REJECTED"),
    "embedding_unavailable": ("safe_fallback", None),
    "redis_unavailable": ("safe_fallback", None),
    "business_unavailable": (None, "BUSINESS_UNAVAILABLE"),
    "minio_unavailable": (None, "MINIO_UNAVAILABLE"),
    "no_candidates": ("no_results", None),
    "expired_index": ("reindex_required", None),
}


class FakeEmbedding:
    """A deterministic 1024-dimensional signed feature-hash embedding."""

    dimensions = 1024

    def embed(self, text: str) -> list[float]:
        normalized = text.casefold()
        for source, target in _SYNONYMS.items():
            normalized = normalized.replace(source, target)
        tokens = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", normalized)
        vector = [0.0] * self.dimensions
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += -1.0 if digest[4] & 1 else 1.0
        size = math.sqrt(sum(value * value for value in vector))
        return [value / size for value in vector] if size else vector

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


@dataclass(frozen=True)
class FixtureSubject:
    subject_id: int
    title: str
    aliases: tuple[str, ...]
    text: str
    year: int
    quarter: int
    score: float
    tags: tuple[str, ...]
    preference_states: tuple[str, ...] = ()
    excluded_states: tuple[str, ...] = ()
    nsfw: bool = False
    subject_type: int = 2


class FakeRedis:
    def __init__(self, subjects: Iterable[FixtureSubject], embeddings: FakeEmbedding) -> None:
        self._subjects = tuple(subjects)
        self._embeddings = embeddings
        self._vectors = {subject.subject_id: embeddings.embed(subject.text) for subject in self._subjects}

    def search(self, query: str, case: EvalCase, limit: int = 20) -> list[int]:
        vector = self._embeddings.embed(query)
        folded = query.casefold().strip()
        scored = []
        for subject in self._subjects:
            if case.year is not None and subject.year != case.year:
                continue
            if case.quarter is not None and subject.quarter != case.quarter:
                continue
            if case.scoreMin is not None and subject.score < case.scoreMin:
                continue
            if case.tags and not set(case.tags).issubset(subject.tags):
                continue
            title_match = folded in {subject.title.casefold(), *(alias.casefold() for alias in subject.aliases)}
            tag_matches = sum(tag in query for tag in subject.tags)
            score = sum(left * right for left, right in zip(vector, self._vectors[subject.subject_id]))
            scored.append((1 if title_match else 0, tag_matches, score, -subject.subject_id, subject.subject_id))
        return [item[-1] for item in sorted(scored, reverse=True)[:limit]]


class FakeBusiness:
    def __init__(self, subjects: Iterable[FixtureSubject]) -> None:
        self._subjects = {subject.subject_id: subject for subject in subjects}

    def visible(self, subject_ids: Iterable[int], preference_state: str | None = None, query: str = "") -> list[int]:
        subjects = [self._subjects[sid] for sid in subject_ids if sid in self._subjects]
        subjects = [subject for subject in subjects if not subject.nsfw and subject.subject_type == 2]
        if preference_state in {"watched", "watching", "wish"}:
            subjects = [subject for subject in subjects if preference_state in subject.preference_states]
            folded = query.casefold().strip()
            subjects.sort(key=lambda subject: (
                folded not in {subject.title.casefold(), *(alias.casefold() for alias in subject.aliases)},
                -subject.score,
            ))
        elif preference_state == "onhold":
            subjects = [subject for subject in subjects if "onhold" in subject.preference_states]
        elif preference_state == "cold_start":
            subjects.sort(key=lambda subject: (-subject.score, subject.subject_id))
        elif preference_state == "dropped":
            subjects = [subject for subject in subjects if "dropped" not in subject.excluded_states]
        return [subject.subject_id for subject in subjects]


@dataclass(frozen=True)
class OfflineResult:
    ranked: list[int]
    fallback: str | None = None
    error_type: str | None = None


class OfflineAdapter:
    def __init__(self, subjects: Iterable[FixtureSubject]) -> None:
        subjects = tuple(subjects)
        embeddings = FakeEmbedding()
        self._redis = FakeRedis(subjects, embeddings)
        self._business = FakeBusiness(subjects)

    def evaluate(self, case: EvalCase) -> OfflineResult:
        if case.fault is not None:
            fallback, error_type = _SAFETY_OUTCOMES.get(case.fault, (None, "UNKNOWN_FAULT"))
            return OfflineResult([], fallback, error_type)
        ranked = self._redis.search(case.query, case)
        ranked = self._business.visible(ranked, case.preferenceState, case.query)
        return OfflineResult(ranked[:1])
