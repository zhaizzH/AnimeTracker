import json
import logging
import re
import uuid

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.observability import (
    HEADER_X_REQUEST_ID,
    get_trace_id,
    hash_value,
    log_event,
    reset_trace_context,
    sanitize_trace_id,
    set_trace_context,
    trace_context_middleware,
)

_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _app() -> FastAPI:
    test_app = FastAPI()
    test_app.middleware("http")(trace_context_middleware)

    @test_app.get("/trace")
    async def trace():
        return {"traceId": get_trace_id()}

    return test_app


def test_log_event_emits_json_without_secrets(caplog):
    caplog.set_level(logging.INFO)
    token = set_trace_context("trace-1")
    try:
        log_event("agent.model.completed", provider="deepseek", api_key="secret")
    finally:
        reset_trace_context(token)
    payload = json.loads(caplog.records[-1].message)
    assert payload["traceId"] == "trace-1"
    assert "secret" not in caplog.text
    assert "api_key" not in payload


def test_log_event_filters_unallowed_fields_and_none(caplog):
    caplog.set_level(logging.INFO)
    token = set_trace_context("trace-2")
    try:
        log_event(
            "agent.request.completed",
            sessionHash=None,
            userHash="h1",
            user_input="敏感内容",
            durationMs=3,
        )
    finally:
        reset_trace_context(token)
    payload = json.loads(caplog.records[-1].message)
    assert payload["traceId"] == "trace-2"
    assert "sessionHash" not in payload  # None 省略
    assert payload["userHash"] == "h1"
    assert "user_input" not in payload
    assert "敏感内容" not in caplog.text


def test_hash_value_is_deterministic_and_not_plain():
    h = hash_value("s-1")
    assert h and h != "s-1"
    assert hash_value("s-1") == h  # 确定性
    assert hash_value("") is None
    assert hash_value(None) is None


def test_request_id_middleware_propagates_and_cleans():
    client = TestClient(_app())

    resp1 = client.get("/trace", headers={"X-Request-ID": "req-1"})
    assert resp1.json()["traceId"] == "req-1"
    assert resp1.headers["X-Request-ID"] == "req-1"

    resp2 = client.get("/trace")
    trace2 = resp2.json()["traceId"]
    assert uuid.UUID(trace2)  # 第二个请求无 X-Request-ID 时生成新 UUID
    assert trace2 != "req-1"
    assert resp2.headers["X-Request-ID"] == trace2

    # 请求结束后 ContextVar 清理,不串号
    assert get_trace_id() is None


def test_invalid_header_is_replaced():
    client = TestClient(_app())
    resp = client.get("/trace", headers={HEADER_X_REQUEST_ID: "bad id!\n<script>"})
    header = resp.headers[HEADER_X_REQUEST_ID]
    assert header != "bad id!\n<script>"
    assert _VALID_ID.fullmatch(header)
    assert resp.json()["traceId"] == header


def test_get_trace_id_default_none_outside_request():
    assert get_trace_id() is None


def test_sanitize_rules():
    assert sanitize_trace_id("aB9._-x") == "aB9._-x"
    assert _VALID_ID.fullmatch(sanitize_trace_id("")) is not None
    assert _VALID_ID.fullmatch(sanitize_trace_id(None)) is not None
    long_id = "a" * 129
    assert sanitize_trace_id(long_id) != long_id
    assert _VALID_ID.fullmatch(sanitize_trace_id(long_id)) is not None


@pytest.mark.asyncio
async def test_contextvar_cleared_after_request_same_context():
    transport = httpx.ASGITransport(app=_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/trace", headers={HEADER_X_REQUEST_ID: "abc"})
        assert resp.json()["traceId"] == "abc"
        # 同一任务上下文中,请求结束后 ContextVar 应清理为默认值
        assert get_trace_id() is None
