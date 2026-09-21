"""API-layer test scaffolding.

The app under test mounts only the client chat router with ``include_health``
and fills ``app.state`` with stand-ins.  The real lifespan is never started: it
would connect to Redis/MySQL and build the LangGraph.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.chat import create_chat_router


class NoopStore:
    """Store stand-in whose PING succeeds."""

    def __init__(self) -> None:
        self.ping_count = 0

    async def init_db(self) -> None:
        self.ping_count += 1


class NoopBusiness:
    """Business gateway stand-in answering liveness successfully."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"status": "UP"}


def fake_settings(*, rag_enabled: bool = False, llm_configured: bool = True) -> SimpleNamespace:
    """Settings stand-in for ``resolve_llm_provider``.

    It must expose every attribute that function reads, or the LLM check would
    fail for the wrong reason (AttributeError instead of a missing key).
    ``llm_configured=False`` makes the resolution raise.
    """
    return SimpleNamespace(
        rag_enabled=rag_enabled,
        llm_provider="deepseek" if llm_configured else "",
        llm_reasoning_effort="high",
        deepseek_api_key="test-key" if llm_configured else "",
        deepseek_model="deepseek-v4-flash",
        deepseek_model_route="deepseek-v4-flash",
        deepseek_base_url="https://api.deepseek.com",
        dashscope_api_key="",
        dashscope_model="qwen3.7-plus",
        dashscope_model_route="qwen3.7-plus",
    )


def _auth_dep():
    raise AssertionError("health 端点不得注入鉴权依赖")


@pytest.fixture
def make_client():
    """Build a TestClient over a hand-assembled ``app.state``.

    ``with_state=False`` leaves ``app.state`` empty to exercise the fail-closed
    path (handler falls back to the process settings singleton for the LLM check).
    """

    def build(*, store=None, business=None, rag_redis=None, settings_obj=None, with_state=True):
        app = FastAPI()
        if with_state:
            app.state.store = NoopStore() if store is None else store
            app.state.business_gateway = NoopBusiness() if business is None else business
            app.state.rag_redis = rag_redis
            app.state.settings = fake_settings() if settings_obj is None else settings_obj
        app.include_router(
            create_chat_router(prefix="/api/client/agent", auth_dep=_auth_dep, include_health=True)
        )
        return TestClient(app)

    return build
