"""API-layer tests for ``GET /api/client/agent/health``.

Covers AC1-AC10 and AC13 of the health-depth task.  Every dependency is a
stand-in; no real network or Redis connection is opened.
"""

from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path

import httpx
import pytest
import redis

from app.adapters.business_http import HttpBusinessGateway
from app.adapters.redis.vector_set import VectorSetUnavailable, probe_vector_set_commands
from tests.api.conftest import NoopBusiness, NoopStore, fake_settings

HEALTH_PATH = "/api/client/agent/health"
ENUM_VALUES = {"ok", "down", "disabled"}


class _FakeResponse:
    """Minimal successful ``httpx`` response stand-in for monkeypatched calls."""

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return {"status": "UP"}

_SENSITIVE = (
    "redis://",
    "Bearer ",
    "minioadmin",
    "Traceback",
    '.py", line',
)


# --- AC1 / AC2: shape and all-green -------------------------------------------


def test_health_returns_stable_status_and_keys(make_client):
    with make_client(settings_obj=fake_settings()) as client:
        response = client.get(HEALTH_PATH)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "llm_configured", "checks"}
    assert set(body["checks"]) == {"llm", "redis", "business", "rag"}


def test_all_dependencies_up_reports_ok(make_client):
    store = NoopStore()
    business = NoopBusiness()
    with make_client(
        store=store, business=business, settings_obj=fake_settings()
    ) as client:
        response = client.get(HEALTH_PATH)

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["llm_configured"] is True
    assert body["checks"] == {"llm": "ok", "redis": "ok", "business": "ok", "rag": "disabled"}
    # Toggles are not faults (R2).
    assert all(value in ENUM_VALUES for value in body["checks"].values())
    assert store.ping_count == 1


# --- AC3: Redis failure must not short-circuit others -------------------------


class _FailingRedisStore:
    def __init__(self) -> None:
        self.ping_count = 0

    async def init_db(self) -> None:
        self.ping_count += 1
        raise redis.ConnectionError("redis is down")


def test_redis_failure_degrades_without_short_circuiting(make_client):
    store = _FailingRedisStore()
    business = NoopBusiness()
    rag_redis = _RecordingRedis()
    with make_client(
        store=store,
        business=business,
        rag_redis=rag_redis,
        settings_obj=fake_settings(rag_enabled=True),
    ) as client:
        response = client.get(HEALTH_PATH)

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "degraded"
    assert body["checks"]["redis"] == "down"
    # The remaining probes still ran and reported truthfully.
    assert store.ping_count == 1
    assert business.calls, "Business probe was skipped after Redis failed"
    assert rag_redis.commands, "RAG probe was skipped after Redis failed"
    assert body["checks"]["llm"] == "ok"
    assert body["checks"]["business"] == "ok"
    assert body["checks"]["rag"] == "ok"


def test_missing_state_objects_are_down_not_errors(make_client):
    with make_client(with_state=False, settings_obj=fake_settings()) as client:
        response = client.get(HEALTH_PATH)

    assert response.status_code == 200
    assert response.json()["checks"]["redis"] == "down"
    assert response.json()["checks"]["business"] == "down"


# --- AC4: Business failure semantics ------------------------------------------


def test_business_connect_error_is_down(make_client):
    gateway = HttpBusinessGateway("http://localhost:8080")

    def boom(*args, **kwargs):
        raise httpx.ConnectError("refused")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(httpx, "request", boom)
        with make_client(business=gateway, settings_obj=fake_settings()) as client:
            response = client.get(HEALTH_PATH)

    body = response.json()
    assert body["checks"]["business"] == "down"
    assert body["status"] == "degraded"


def test_business_error_envelope_is_down(make_client):
    class ErrorBusiness:
        def request(self, method, path, **kwargs):
            return {"error": True, "code": 503, "message": "后端服务不可用: secret-host"}

    with make_client(business=ErrorBusiness(), settings_obj=fake_settings()) as client:
        response = client.get(HEALTH_PATH)

    body = response.json()
    assert body["checks"]["business"] == "down"
    assert "secret-host" not in response.text


def test_business_probe_uses_liveness_and_narrowed_timeout(make_client):
    business = NoopBusiness()
    with make_client(business=business, settings_obj=fake_settings()) as client:
        client.get(HEALTH_PATH)

    assert len(business.calls) == 1
    method, path, kwargs = business.calls[0]
    assert method == "GET"
    # Not the default /actuator/health: that aggregates Business' own DB/Redis.
    assert path == "/actuator/health/liveness"
    assert kwargs["timeout_seconds"] == 2.0


# --- AC5 / AC6: RAG conditional probe -----------------------------------------


class _RecordingRedis:
    def __init__(self, *, unsupported: str | None = None) -> None:
        self.commands: list[str] = []
        self._unsupported = unsupported

    def execute_command(self, *args):
        command = args[2]
        self.commands.append(command)
        return [None] if command == self._unsupported else [{"arity": -5}]


def test_rag_disabled_reports_disabled_and_skips_probe(make_client):
    rag_redis = _RecordingRedis()
    with make_client(
        rag_redis=rag_redis, settings_obj=fake_settings(rag_enabled=False)
    ) as client:
        response = client.get(HEALTH_PATH)

    body = response.json()
    assert body["checks"]["rag"] == "disabled"
    assert body["checks"]["rag"] != "down"
    assert rag_redis.commands == [], "Vector Set was probed while RAG_ENABLED=false"
    assert body["status"] == "ok"


def test_rag_enabled_with_all_commands_is_ok(make_client):
    rag_redis = _RecordingRedis()
    with make_client(
        rag_redis=rag_redis, settings_obj=fake_settings(rag_enabled=True)
    ) as client:
        response = client.get(HEALTH_PATH)

    assert response.json()["checks"]["rag"] == "ok"
    assert rag_redis.commands == ["VADD", "VSIM", "VREM"]


def test_rag_enabled_with_missing_command_is_down(make_client):
    rag_redis = _RecordingRedis(unsupported="VADD")
    with make_client(
        rag_redis=rag_redis, settings_obj=fake_settings(rag_enabled=True)
    ) as client:
        response = client.get(HEALTH_PATH)

    body = response.json()
    assert body["checks"]["rag"] == "down"
    assert body["status"] == "degraded"


def test_rag_enabled_without_client_is_down(make_client):
    with make_client(rag_redis=None, settings_obj=fake_settings(rag_enabled=True)) as client:
        response = client.get(HEALTH_PATH)

    assert response.json()["checks"]["rag"] == "down"


def test_probe_entry_point_does_not_require_index_version():
    """R4: the health entry point must not call validate_version."""
    redis_stub = _RecordingRedis()
    # Called with no version argument at all; a required parameter would TypeError.
    probe_vector_set_commands(redis_stub)
    assert redis_stub.commands == ["VADD", "VSIM", "VREM"]

    unsupported = _RecordingRedis(unsupported="VREM")
    with pytest.raises(VectorSetUnavailable):
        probe_vector_set_commands(unsupported)


# --- AC7: LLM is configuration-only -------------------------------------------


def test_llm_not_configured_is_down_without_network(make_client):
    probed: list[str] = []

    def record(*args, **kwargs):
        probed.append("http")
        return {"status": "UP"}

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(httpx, "request", record)
        with make_client(settings_obj=fake_settings(llm_configured=False)) as client:
            response = client.get(HEALTH_PATH)

    body = response.json()
    assert body["checks"]["llm"] == "down"
    assert body["llm_configured"] is False
    assert body["status"] == "degraded"
    # The standing gateway stand-in never touches httpx, so this only proves a
    # real gateway was not substituted in.  The load-bearing assertion lives in
    # ``test_llm_not_configured_makes_no_request_through_real_gateway``, which
    # mounts a real gateway and observes what actually reaches httpx.
    assert probed == []


def test_llm_not_configured_makes_no_request_through_real_gateway(make_client):
    """AC7: with a real ``HttpBusinessGateway`` mounted, the LLM=down path still
    issues no HTTP call (it is a pure configuration check)."""
    calls: list[tuple] = []

    def record(method, url, **kwargs):
        calls.append((method, url))
        return _FakeResponse()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(httpx, "request", record)
        with make_client(
            business=HttpBusinessGateway("http://localhost:8080"),
            settings_obj=fake_settings(llm_configured=False),
        ) as client:
            response = client.get(HEALTH_PATH)

    body = response.json()
    assert body["checks"]["llm"] == "down"
    assert body["status"] == "degraded"
    # Only the Business probe may reach the network; the LLM check never does.
    assert len(calls) == 1, f"expected only the business probe, got {calls}"
    method, url = calls[0]
    assert method == "GET"
    assert url.endswith("/actuator/health/liveness")


def test_llm_down_does_not_block_other_probes(make_client):
    store = NoopStore()
    business = NoopBusiness()
    with make_client(
        store=store,
        business=business,
        settings_obj=fake_settings(llm_configured=False),
    ) as client:
        client.get(HEALTH_PATH)

    assert store.ping_count == 1
    assert business.calls


# --- AC8: authorization stays anonymous on the Python side --------------------


def test_health_is_anonymous(make_client):
    """Pins the deliberate Python/Java split: direct :8090 access is anonymous,
    the browser path goes through the Spring proxy which requires a JWT."""
    with make_client(settings_obj=fake_settings()) as client:
        response = client.get(HEALTH_PATH)

    assert response.status_code == 200


def test_other_routes_still_require_auth(make_client):
    """The anonymous health branch must not have removed auth elsewhere."""
    with make_client(settings_obj=fake_settings()) as client:
        with pytest.raises(AssertionError):
            client.get("/api/client/agent/sessions")


# --- AC9: no sensitive information --------------------------------------------


@pytest.mark.parametrize("healthy", [True, False])
def test_response_never_leaks_internals(make_client, healthy):
    class LeakyBusiness:
        def request(self, method, path, **kwargs):
            if healthy:
                return {"status": "UP"}
            return {"error": True, "message": "redis://u:pw@host:6379 Bearer abc /backend/app.py\", line 3"}

    class LeakyStore:
        async def init_db(self) -> None:
            if not healthy:
                raise redis.ConnectionError("redis://u:pw@host:6379")

    with make_client(
        store=LeakyStore(),
        business=LeakyBusiness(),
        settings_obj=fake_settings(llm_configured=healthy),
    ) as client:
        response = client.get(HEALTH_PATH)

    for pattern in _SENSITIVE:
        assert pattern not in response.text, f"leaked {pattern!r}"


def test_minio_absent_from_response(make_client):
    with make_client(settings_obj=fake_settings()) as client:
        response = client.get(HEALTH_PATH)

    assert "minio" not in response.text.lower()


# --- AC10: bounded total probe time -------------------------------------------


def test_probes_never_return_still_answer_within_budget(make_client):
    # Both probes outlive their budget.  The synchronous Business call runs in a
    # worker thread that Python cannot cancel, so it is kept to 3s: the point is
    # that the *response* arrives at the 2s per-probe budget, not that the
    # orphaned thread is killed.
    class HangingStore:
        async def init_db(self) -> None:
            await asyncio.sleep(30)

    class HangingBusiness:
        def request(self, method, path, **kwargs):
            time.sleep(3)
            return {"status": "UP"}

    started = time.monotonic()
    with make_client(
        store=HangingStore(),
        business=HangingBusiness(),
        settings_obj=fake_settings(),
    ) as client:
        response = client.get(HEALTH_PATH)
        # Measured before teardown, which joins the orphaned worker thread.
        elapsed = time.monotonic() - started

    body = response.json()
    assert response.status_code == 200
    assert body["checks"]["redis"] == "down"
    assert body["checks"]["business"] == "down"
    assert body["status"] == "degraded"
    # Per-probe budget is 2s; the probes would have run for 3s/30s.
    assert elapsed < 2.8, f"health probe took {elapsed:.1f}s"


# --- AC13: no MinIO scope creep ------------------------------------------------


def test_no_new_minio_import_in_app_package():
    app_dir = Path(__file__).resolve().parents[2] / "app"
    offenders = [
        path.relative_to(app_dir).as_posix()
        for path in app_dir.rglob("*.py")
        if "minio" in path.read_text(encoding="utf-8").lower()
        and path.name != "config.py"
    ]
    assert offenders == [], f"unexpected MinIO references in app/: {offenders}"
