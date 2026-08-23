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
    nsfw: bool = False
    subject_type: int = 2


class FakeRedis:
    def __init__(self, subjects: Iterable[FixtureSubject], embeddings: FakeEmbedding) -> None:
        self._subjects = tuple(subjects)
        self._embeddings = embeddings
        self._vectors = {subject.subject_id: embeddings.embed(subject.text) for subject in self._subjects}

    def search(self, query: str, limit: int = 20) -> list[int]:
        vector = self._embeddings.embed(query)
        folded = query.casefold().strip()
        scored = []
        for subject in self._subjects:
            title_match = folded in {subject.title.casefold(), *(alias.casefold() for alias in subject.aliases)}
            score = sum(left * right for left, right in zip(vector, self._vectors[subject.subject_id]))
            scored.append((1 if title_match else 0, score, -subject.subject_id, subject.subject_id))
        return [item[-1] for item in sorted(scored, reverse=True)[:limit]]


class FakeBusiness:
    def __init__(self, subjects: Iterable[FixtureSubject]) -> None:
        self._subjects = {subject.subject_id: subject for subject in subjects}

    def visible(self, subject_ids: Iterable[int]) -> list[int]:
        return [sid for sid in subject_ids if sid in self._subjects and not self._subjects[sid].nsfw and self._subjects[sid].subject_type == 2]


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
        if case.category == "safety_failure":
            return OfflineResult([], case.expectedFallback, case.expectedErrorType)
        return OfflineResult(self._business.visible(self._redis.search(case.query, limit=1)))
