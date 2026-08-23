from __future__ import annotations

from array import array
from base64 import b64decode, b64encode
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Callable, Sequence


_CACHE_TTL_SECONDS = 24 * 60 * 60
_WEIGHTS = {1: 0.35, 2: 1.0, 3: 1.0, 4: 0.0, 5: -0.75}
_VECTOR_DIMENSIONS = 1024
_VECTOR_BYTES = _VECTOR_DIMENSIONS * 4


@dataclass(frozen=True)
class CollectionItem:
    subject_id: int
    type: int
    rate: int | float | None = None
    ep_status: int | None = None


@dataclass(frozen=True)
class UserPreference:
    vector: tuple[float, ...]
    exclude_subject_ids: tuple[int, ...]
    sample_count: int
    collection_version: str

    def __post_init__(self) -> None:
        vector = _float32_vector(self.vector)
        if vector is None:
            raise ValueError("用户画像必须是 1024 维有限 Float32 向量")
        object.__setattr__(self, "vector", vector)


VectorLookup = Callable[[int], Sequence[float] | None]


def collection_version(items: Sequence[CollectionItem]) -> str:
    """返回与返回顺序无关的收藏快照摘要。"""
    rows = sorted(
        f"{int(item.subject_id)}:{int(item.type)}:{_value(item.rate)}:{_value(item.ep_status)}"
        for item in items
    )
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def build_preference(items: Sequence[CollectionItem], *, vector_lookup: VectorLookup) -> UserPreference | None:
    """用既有条目向量构建归一化偏好，不调用嵌入服务。"""
    version = collection_version(items)
    excludes = tuple(sorted({int(item.subject_id) for item in items}))
    weighted: list[tuple[float, tuple[float, ...]]] = []
    for item in items:
        weight = _WEIGHTS.get(int(item.type), 0.0)
        if weight == 0.0:
            continue
        vector = _float32_vector(vector_lookup(int(item.subject_id)))
        if vector is not None:
            weighted.append((weight, vector))
    if len(weighted) < 3:
        return None
    totals = [0.0] * _VECTOR_DIMENSIONS
    total_weight = sum(abs(weight) for weight, _ in weighted)
    if total_weight == 0.0:
        return None
    for weight, vector in weighted:
        for offset, value in enumerate(vector):
            totals[offset] += weight * value
    mean = [value / total_weight for value in totals]
    magnitude = math.sqrt(sum(value * value for value in mean))
    if not math.isfinite(magnitude) or magnitude == 0.0:
        return None
    return UserPreference(
        vector=tuple(value / magnitude for value in mean),
        exclude_subject_ids=excludes,
        sample_count=len(weighted),
        collection_version=version,
    )


class UserProfileService:
    """只缓存可重建的短期用户向量，不保存个人资料或原始收藏。"""

    def __init__(self, redis: Any, *, vector_lookup: VectorLookup, key_prefix: str = "rag:user-profile:") -> None:
        self._redis = redis
        self._vector_lookup = vector_lookup
        self._key_prefix = key_prefix

    def get_or_build(self, user: Any, collection_items: Sequence[CollectionItem]) -> UserPreference | None:
        version = collection_version(collection_items)
        key = f"{self._key_prefix}{self._user_id(user)}:{version}"
        try:
            cached = self._decode(self._redis.get(key), version)
        except Exception:
            cached = None
        if cached is not None:
            return cached
        profile = build_preference(collection_items, vector_lookup=self._vector_lookup)
        if profile is None:
            return None
        try:
            self._redis.setex(key, _CACHE_TTL_SECONDS, self._encode(profile))
        except Exception:
            pass
        return profile

    @staticmethod
    def _user_id(user: Any) -> int:
        return int(user if isinstance(user, int) else user.user_id)

    @staticmethod
    def _encode(profile: UserPreference) -> str:
        encoded = b64encode(array("f", profile.vector).tobytes()).decode()
        return json.dumps(
            {
                "vector": encoded,
                "sampleCount": profile.sample_count,
                "excludeSubjectIds": list(profile.exclude_subject_ids),
            },
            separators=(",", ":"),
        )

    @staticmethod
    def _decode(raw: Any, version: str) -> UserPreference | None:
        if raw is None:
            return None
        value = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
        encoded = value.get("vector")
        sample_count = value.get("sampleCount")
        excludes = value.get("excludeSubjectIds")
        if not isinstance(encoded, str) or not isinstance(sample_count, int) or not isinstance(excludes, list):
            return None
        encoded_bytes = b64decode(encoded, validate=True)
        if len(encoded_bytes) != _VECTOR_BYTES:
            return None
        decoded = array("f")
        decoded.frombytes(encoded_bytes)
        vector = _float32_vector(decoded)
        if vector is None or sample_count < 3:
            return None
        return UserPreference(
            vector=vector,
            exclude_subject_ids=tuple(sorted(int(subject_id) for subject_id in excludes)),
            sample_count=sample_count,
            collection_version=version,
        )


def _float32_vector(values: Sequence[float] | None) -> tuple[float, ...] | None:
    if values is None:
        return None
    try:
        vector = tuple(float(value) for value in values)
        if len(vector) != _VECTOR_DIMENSIONS or not all(math.isfinite(value) for value in vector):
            return None
        encoded = array("f", vector)
    except (TypeError, ValueError, OverflowError):
        return None
    return tuple(encoded) if all(math.isfinite(value) for value in encoded) else None


def _value(value: Any) -> str:
    return "" if value is None else str(value)
