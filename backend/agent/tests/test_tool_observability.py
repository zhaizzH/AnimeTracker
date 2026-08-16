import asyncio
import json
import logging
from types import SimpleNamespace

from langchain_core.messages import ToolMessage

from app.core.event_bus import reset_status_emitter, set_status_emitter
from app.core.middleware import build_tool_status_middleware, tool_call_status


def last_event(caplog, event_name):
    for record in reversed(caplog.records):
        try:
            payload = json.loads(record.message)
        except (ValueError, TypeError):
            continue
        if payload.get("event") == event_name:
            return payload
    raise AssertionError(f"no {event_name!r} event captured")


def _register_tool(tool_name, display_name):
    class _Dummy:
        name = tool_name

    return tool_call_status(display_name=display_name)(_Dummy())


def _request(tool_name="test_obs_tool"):
    return SimpleNamespace(tool_call={"name": tool_name, "id": "call-1", "args": {"q": 1}})


async def _run(middleware, request, handler):
    return await middleware.awrap_tool_call(request, handler)


def _capture_emitter(events):
    return set_status_emitter(events.append)


def test_tool_success_logs_completed_and_keeps_sse_events(caplog):
    caplog.set_level(logging.INFO)
    _register_tool("test_obs_tool", "测试工具")
    middleware = build_tool_status_middleware()
    events = []
    token = _capture_emitter(events)
    try:
        result = ToolMessage(content="ok", tool_call_id="call-1")

        async def handler(req):
            return result

        out = asyncio.run(_run(middleware, _request(), handler))
    finally:
        reset_status_emitter(token)

    assert out is result
    event = last_event(caplog, "agent.tool.completed")
    assert event["toolName"] == "test_obs_tool"
    assert event["success"] is True
    assert "errorType" not in event
    assert "durationMs" in event
    states = [e["content"]["state"] for e in events]
    assert states == ["start", "end"]  # 既有 SSE function-call 状态事件保留


def test_tool_failure_logs_failure_and_returns_error_tool_message(caplog):
    caplog.set_level(logging.INFO)
    _register_tool("test_obs_tool", "测试工具")
    middleware = build_tool_status_middleware()
    events = []
    token = _capture_emitter(events)
    try:
        async def handler(req):
            raise RuntimeError("tool boom")

        out = asyncio.run(_run(middleware, _request(), handler))
    finally:
        reset_status_emitter(token)

    assert isinstance(out, ToolMessage)
    assert json.loads(out.content)["error"] == "tool boom"
    event = last_event(caplog, "agent.tool.completed")
    assert event["toolName"] == "test_obs_tool"
    assert event["success"] is False
    assert event["errorType"] == "TOOL_INTERNAL_ERROR"
    states = [e["content"]["state"] for e in events]
    assert states == ["start", "end"]
    assert events[-1]["content"]["result"] == "error"
