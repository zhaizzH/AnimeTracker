import io
import json
import logging
import re

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.observability import (
    SERVICE,
    TraceContextMiddleware,
    configure_logging,
    get_trace_id,
)

_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


async def _echo(request):
    return JSONResponse({"traceId": get_trace_id()})


def _make_client():
    inner = Starlette(routes=[Route("/echo", _echo)])
    return TestClient(TraceContextMiddleware(inner))


def test_valid_header_echoed():
    with _make_client() as client:
        resp = client.get("/echo", headers={"X-Request-ID": "abc123_-."})
    assert resp.json()["traceId"] == "abc123_-."
    assert resp.headers["X-Request-ID"] == "abc123_-."


def test_absent_header_generates_id():
    with _make_client() as client:
        resp = client.get("/echo")
    request_id = resp.headers["X-Request-ID"]
    assert _ID_PATTERN.match(request_id)
    assert resp.json()["traceId"] == request_id


def test_invalid_header_replaced():
    with _make_client() as client:
        resp = client.get("/echo", headers={"X-Request-ID": "bad header!!!"})
    request_id = resp.headers["X-Request-ID"]
    assert request_id != "bad header!!!"
    assert _ID_PATTERN.match(request_id)
    assert resp.json()["traceId"] == request_id


def test_request_id_set_in_response_header():
    with _make_client() as client:
        resp = client.get("/echo", headers={"X-Request-ID": "echo-me"})
    assert resp.headers["X-Request-ID"] == "echo-me"


def test_contextvar_cleared_after_request():
    assert get_trace_id() == ""
    with _make_client() as client:
        resp = client.get("/echo", headers={"X-Request-ID": "keep-me"})
        assert resp.json()["traceId"] == "keep-me"
    assert get_trace_id() == ""


def test_logging_json_scrubs_secret_fields():
    root = logging.getLogger()
    saved = (root.level, list(root.handlers))
    buf = io.StringIO()
    try:
        configure_logging(stream=buf)
        logging.getLogger("test.observability").info(
            {"event": "llm_call", "api_key": "sk-secret-value", "model": "deepseek-chat"}
        )
        line = buf.getvalue().strip().splitlines()[-1]
        payload = json.loads(line)
        assert payload["service"] == SERVICE
        assert payload["traceId"] == ""
        assert payload["level"] == "INFO"
        assert payload["logger"] == "test.observability"
        assert payload["message"]["api_key"] == "***"
        assert payload["message"]["model"] == "deepseek-chat"
        assert "sk-secret-value" not in buf.getvalue()
    finally:
        root.setLevel(saved[0])
        root.handlers = saved[1]


def test_logging_includes_trace_id_inside_request():
    root = logging.getLogger()
    saved = (root.level, list(root.handlers))
    buf = io.StringIO()
    try:
        configure_logging(stream=buf)

        async def _echo_and_log(request):
            logging.getLogger("test.observability.request").info("handler ran")
            return JSONResponse({})

        inner = Starlette(routes=[Route("/echo", _echo_and_log)])
        with TestClient(TraceContextMiddleware(inner)) as client:
            client.get("/echo", headers={"X-Request-ID": "req-42"})

        assert '"traceId": "req-42"' in buf.getvalue()
    finally:
        root.setLevel(saved[0])
        root.handlers = saved[1]
