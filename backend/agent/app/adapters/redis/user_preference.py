from __future__ import annotations

from array import array
from base64 import b64decode, b64encode
import json
import math
from typing import Any, Mapping, Sequence

from app.agent.ports import BusinessGateway
from app.rag.user_profile import CollectionItem, UserPreference, build_preference, collection_version


_CACHE_TTL_SECONDS = 24 * 60 * 60
_VECTOR_DIMENSIONS = 1024
_VECTOR_BYTES = _VECTOR_DIMENSIONS * 4


class RedisUserPreferenceProvider:
    """只缓存可重建的短期用户向量，不保存个人资料或原始收藏。"""

    def __init__(
        self,
        redis: Any,
        *,
        business: BusinessGateway,
        vector_lookup,
        key_prefix: str = "rag:user-profile:",
    ) -> None:
        self._redis = redis
        self._business = business
        self._vector_lookup = vector_lookup
        self._key_prefix = key_prefix

    def load(self, user_id: int, token: str | None) -> tuple[UserPreference | None, bool]:
        try:
            response = self._business.request(
                "GET",
                "/api/client/collections",
                params={"page": 1, "size": 100},
                token=token,
            )
        except Exception:
            return None, False
        if isinstance(response, Mapping) and response.get("error"):
            return None, False
        items = _collection_items(response)
        if not items:
            return None, True
        try:
            profile = self._get_or_build(user_id, items)
        except Exception:
            return None, True
        return profile, profile is None

    def _get_or_build(self, user_id: int, collection_items: Sequence[CollectionItem]) -> UserPreference | None:
        version = collection_version(collection_items)
        key = f"{self._key_prefix}{int(user_id)}:{version}"
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


def _collection_items(response: Any) -> list[CollectionItem]:
    rows = response.get("content", response.get("items", [])) if isinstance(response, Mapping) else response
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    items: list[CollectionItem] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        subject = row.get("subject") if isinstance(row.get("subject"), Mapping) else {}
        subject_id = row.get("subjectId", subject.get("id"))
        try:
            items.append(CollectionItem(int(subject_id), int(row.get("type")), row.get("rate"), row.get("epStatus")))
        except (TypeError, ValueError):
            continue
    return items


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
