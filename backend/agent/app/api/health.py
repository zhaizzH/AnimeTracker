"""Dependency-aware health report for ``GET /api/client/agent/health``.

The endpoint always answers HTTP 200 and expresses degradation in the body.
That is a deliberate exception to the "HTTP status must match the error code"
rule: this is a diagnostic endpoint, not a business response, and no resident
host consumes its status code (see ``error-handling.md`` and the task notes).

Probe semantics: every probe performs a real dependency call, is bounded by a
timeout, and reports ``down`` for any exception, timeout or error envelope.
``checks`` only ever contains the finite enum ``ok``/``down``/``disabled`` --
never exception text, which would leak upstream bodies and connection strings.
A disabled feature flag is ``disabled``, never ``down``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Mapping

from app.adapters.redis.vector_set import probe_vector_set_commands
from app.config import resolve_llm_provider

logger = logging.getLogger(__name__)

# Business liveness answers "is the Business HTTP process reachable" without
# aggregating Business' own MySQL/Redis readiness.  Probing the default
# ``/actuator/health`` would report a Business-internal DB hiccup as an Agent
# dependency failure.  The path is permitAll in Business SecurityConfig, so the
# anonymous agent probe needs no token.
BUSINESS_LIVENESS_PATH = "/actuator/health/liveness"

# Per-probe ceiling.  Redis already caps its socket connect at 2s
# (``RedisChatStore``); Business is narrowed to the same value for health only
# (its business calls keep the 10s default).
PROBE_TIMEOUT_SECONDS = 2.0
# Overall ceiling, so the endpoint can never hang even if a probe ignores its
# own timeout.  Contains the Redis budget plus headroom and stays far below the
# 10s Business default.
TOTAL_TIMEOUT_SECONDS = 3.0

_PROBE_NAMES = ("redis", "business", "rag")
_DOWN = "down"


async def build_health_report(
    *,
    settings_obj: Any,
    store: Any,
    business: Any,
    rag_redis: Any,
) -> dict[str, Any]:
    """Probe every dependency and build the stable response payload.

    A missing dependency object is reported as ``down`` (fail-closed) instead of
    letting ``AttributeError`` escape.  Probes run concurrently and never
    short-circuit: one failing dependency must not hide the state of the others.
    """
    llm = _probe_llm(settings_obj)
    # Default to fail-closed; a probe that never completes (total budget or
    # cancellation) leaves its entry as ``down``.
    checks: dict[str, str] = {name: _DOWN for name in _PROBE_NAMES}

    async def guarded(name: str, probe: Any) -> None:
        try:
            checks[name] = await asyncio.wait_for(probe, timeout=PROBE_TIMEOUT_SECONDS)
        except Exception:
            # Any failure -- exception, timeout, malformed response -- is
            # ``down``. Only the typed enum is recorded, never the exception.
            checks[name] = _DOWN

    try:
        await asyncio.wait_for(
            asyncio.gather(
                guarded("redis", _probe_redis(store)),
                guarded("business", _probe_business(business)),
                guarded("rag", _probe_rag(settings_obj, rag_redis)),
            ),
            timeout=TOTAL_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("health 探测超出总预算，未完成分项按 down 报告")

    checks["llm"] = llm
    return {
        "status": "degraded" if any(value == _DOWN for value in checks.values()) else "ok",
        "llm_configured": llm == "ok",
        "checks": checks,
    }


def _probe_llm(settings_obj: Any) -> str:
    """Configuration-only check: the LLM has no probeable network endpoint."""
    try:
        resolve_llm_provider(settings_obj)
    except Exception:
        return _DOWN
    return "ok"


async def _probe_redis(store: Any) -> str:
    """Real PING.  Constructing the store proves nothing: it only parses the URL."""
    if store is None:
        return _DOWN
    await store.init_db()
    return "ok"


async def _probe_business(business: Any) -> str:
    """Real HTTP call.  ``request`` normalizes failures into an error envelope."""
    if business is None:
        return _DOWN
    response = await asyncio.to_thread(
        business.request,
        "GET",
        BUSINESS_LIVENESS_PATH,
        timeout_seconds=PROBE_TIMEOUT_SECONDS,
    )
    if isinstance(response, Mapping) and response.get("error"):
        return _DOWN
    return "ok"


async def _probe_rag(settings_obj: Any, rag_redis: Any) -> str:
    """Conditional probe: a disabled flag is ``disabled`` and is not a fault."""
    if not getattr(settings_obj, "rag_enabled", False):
        return "disabled"
    if rag_redis is None:
        # The flag claims RAG is on but no client was assembled: a real
        # inconsistency, not a disabled feature.
        return _DOWN
    await asyncio.to_thread(probe_vector_set_commands, rag_redis)
    return "ok"
