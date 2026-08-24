from __future__ import annotations

from array import array
from base64 import b64encode
import json
from math import isclose

from app.adapters.redis.user_preference import RedisUserPreferenceProvider
from app.rag.user_profile import (
    CollectionItem,
    build_preference,
    collection_version,
)


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttl: dict[str, int] = {}
        self.fail_get = False
        self.fail_set = False

    def get(self, key: str) -> str | None:
        if self.fail_get:
            raise RuntimeError("cache unavailable")
        return self.values.get(key)

    def setex(self, key: str, seconds: int, value: str) -> None:
        if self.fail_set:
            raise RuntimeError("cache unavailable")
        self.values[key] = value
        self.ttl[key] = seconds


class FakeBusiness:
    def __init__(self, collection):
        self.collection = collection
        self.calls = []

    def request(self, method, path, *, params=None, token=None, json_body=None):
        self.calls.append((method, path, params, token, json_body))
        return {"content": [
            {
                "subjectId": row.subject_id,
                "type": row.type,
                "rate": row.rate,
                "epStatus": row.ep_status,
            }
            for row in self.collection
        ]}


def vector(*head: float) -> list[float]:
    return [*head, *([0.0] * (1024 - len(head)))]


VECTORS = {1: vector(1.0, 0.0), 2: vector(0.0, 1.0), 3: vector(1.0, 1.0), 4: vector(-1.0, 0.0)}


def item(subject_id: int, type: int, *, rate: int | None = None, ep_status: int | None = None) -> CollectionItem:
    return CollectionItem(subject_id=subject_id, type=type, rate=rate, ep_status=ep_status)


def test_collection_version_is_order_independent():
    """Changing response order must not invalidate a valid 24-hour cache."""
    first = item(1, 2, rate=8, ep_status=12)
    second = item(2, 1, ep_status=0)

    assert collection_version([first, second]) == collection_version([second, first])


def test_profile_weights_collection_types_and_normalizes_vector():
    """Removing negative feedback or L2 normalization would distort personalization."""
    profile = build_preference(
        [item(1, 2), item(2, 3), item(3, 1), item(4, 5), item(99, 4)],
        vector_lookup=VECTORS.get,
    )

    assert profile is not None
    assert profile.exclude_subject_ids == (1, 2, 3, 4, 99)
    assert profile.sample_count == 4
    assert isclose(profile.vector[0], 2.10 / (2.10**2 + 1.35**2) ** 0.5, rel_tol=1e-6)
    assert isclose(profile.vector[1], 1.35 / (2.10**2 + 1.35**2) ** 0.5, rel_tol=1e-6)


def test_profile_requires_three_available_non_neutral_samples():
    """A tiny or neutral history must use the cold-start path instead of fake precision."""
    assert build_preference([item(1, 2), item(2, 4), item(3, 1)], vector_lookup=VECTORS.get) is None


def test_profile_rejects_non_1024_nonfinite_and_non_float32_subject_vectors():
    """Accepting a malformed subject vector would make the stored preference unusable by the fixed Redis index."""
    for bad_vector in ([1.0, 0.0], vector(float("nan")), vector(float("inf")), vector(1e100)):
        assert build_preference(
            [item(1, 2), item(2, 3), item(3, 1)], vector_lookup=lambda _subject_id: bad_vector
        ) is None


def test_service_caches_float32_payload_with_ttl_and_natural_version_expiry():
    """A cache payload must contain only the compact preference data, never user secrets or raw collections."""
    redis = FakeRedis()
    collection = [item(1, 2), item(2, 3), item(3, 1)]
    business = FakeBusiness(collection)
    service = RedisUserPreferenceProvider(redis, business=business, vector_lookup=VECTORS.get)

    profile, missing = service.load(7, "jwt-secret")

    assert profile is not None
    assert missing is False
    assert business.calls == [("GET", "/api/client/collections", {"page": 1, "size": 100}, "jwt-secret", None)]
    key = f"rag:user-profile:7:{profile.collection_version}"
    assert redis.ttl[key] == 86400
    assert "jwt-secret" not in redis.values[key]
    assert "ep_status" not in redis.values[key]
    cached, cached_missing = RedisUserPreferenceProvider(
        redis, business=business, vector_lookup=lambda _subject_id: None
    ).load(7, "jwt-secret")
    assert cached is not None
    assert cached_missing is False
    assert cached.sample_count == 3
    changed, changed_missing = RedisUserPreferenceProvider(
        redis, business=FakeBusiness([*collection, item(4, 5)]), vector_lookup=VECTORS.get
    ).load(7, "jwt-secret")
    assert changed is not None
    assert changed_missing is False
    assert changed.collection_version != profile.collection_version


def test_cache_failure_falls_back_to_local_calculation():
    """A Redis outage must not call external services or prevent a safe local profile."""
    redis = FakeRedis()
    redis.fail_get = True
    redis.fail_set = True
    service = RedisUserPreferenceProvider(
        redis,
        business=FakeBusiness([item(1, 2), item(2, 3), item(3, 1)]),
        vector_lookup=VECTORS.get,
    )

    profile, missing = service.load(7, "jwt-secret")

    assert profile is not None
    assert missing is False
    assert profile.sample_count == 3


def test_invalid_cache_vector_is_a_miss_and_rebuilds_safely():
    """A short, malformed, NaN or infinite cache vector must never reach retrieval."""
    collection = [item(1, 2), item(2, 3), item(3, 1)]
    version = collection_version(collection)
    key = f"rag:user-profile:7:{version}"
    bad_payloads = [
        b64encode(array("f", [1.0, 0.0]).tobytes()).decode(),
        b64encode(b"x" * 4095).decode(),
        b64encode(array("f", vector(float("nan"))).tobytes()).decode(),
        b64encode(array("f", vector(float("inf"))).tobytes()).decode(),
    ]
    for encoded in bad_payloads:
        redis = FakeRedis()
        redis.values[key] = json.dumps({"vector": encoded, "sampleCount": 3, "excludeSubjectIds": [1, 2, 3]})

        profile, missing = RedisUserPreferenceProvider(
            redis, business=FakeBusiness(collection), vector_lookup=VECTORS.get
        ).load(7, "jwt-secret")

        assert profile is not None
        assert missing is False
        assert len(profile.vector) == 1024
