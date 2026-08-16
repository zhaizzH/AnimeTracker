import asyncio
import json
import logging

import pytest

from app.core.event_bus import emit_answer_delta, emit_function_call
from app.core.observability import (
    get_session_hash,
    get_user_hash,
    hash_value,
    reset_trace_context,
    set_trace_context,
)
from app.core.streaming import StreamConfig, create_streaming_response
from app.service.chat import ChatService


def last_event(caplog, event_name):
    for record in reversed(caplog.records):
        try:
            payload = json.loads(record.message)
        except (ValueError, TypeError):
            continue
        if payload.get("event") == event_name:
            return payload
    raise AssertionError(f"no {event_name!r} event captured")


class EmittingWorkflow:
    def __init__(self, result="ok", route="search_agent"):
        self.result = result
        self.route = route
        self.state = None

    async def astream(self, state, stream_mode=None):
        self.state = state
        emit_function_call(node="tool:search_subjects", state="start", name="search_subjects", arguments="{}")
        emit_answer_delta("答案内容")
        emit_function_call(node="tool:search_subjects", state="end", name="search_subjects")
        yield ("values", {"result": self.result, "routing": {"route_target": self.route}})


class ErrorWorkflow:
    async def astream(self, state, stream_mode=None):
        yield ("values", {"result": "", "routing": {"route_target": "search_agent"}})
        raise ValueError("gateway returned invalid JSON")


class HangingWorkflow:
    async def astream(self, state, stream_mode=None):
        await asyncio.Event().wait()
        yield ("values", {"result": "never"})  # pragma: no cover


def _config(workflow):
    return StreamConfig(
        workflow=workflow,
        build_initial_state=lambda: {"user": None, "routing": None, "result": ""},
        map_exception=lambda exc: "处理请求时出错，请重试",
    )


async def _consume(resp):
    async for _chunk in resp.body_iterator:
        pass


@pytest.mark.asyncio
async def test_stream_logs_request_completion(caplog):
    caplog.set_level(logging.INFO)
    config = _config(EmittingWorkflow())
    await _consume(create_streaming_response(config))
    event = last_event(caplog, "agent.request.completed")
    assert event["success"] is True
    assert event["toolCount"] == 1
    assert event["routeTarget"] == "search_agent"
    assert "errorType" not in event
    assert "firstTokenMs" in event


@pytest.mark.asyncio
async def test_stream_logs_failure_with_error_type(caplog):
    caplog.set_level(logging.INFO)
    config = _config(ErrorWorkflow())
    await _consume(create_streaming_response(config))
    event = last_event(caplog, "agent.request.completed")
    assert event["success"] is False
    assert event["errorType"] == "MODEL_RESPONSE_INVALID"
    assert "firstTokenMs" not in event  # 失败不伪造 firstTokenMs


@pytest.mark.asyncio
async def test_stream_logs_client_disconnect(caplog):
    caplog.set_level(logging.INFO)
    config = _config(HangingWorkflow())
    resp = create_streaming_response(config)
    gen = resp.body_iterator
    task = asyncio.create_task(gen.__anext__())
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.sleep(0)  # 让 producer 完成取消
    event = last_event(caplog, "agent.request.completed")
    assert event["success"] is False
    assert event["errorType"] == "CLIENT_DISCONNECTED"


@pytest.mark.asyncio
async def test_stream_logs_session_and_user_hash(caplog):
    caplog.set_level(logging.INFO)
    token = set_trace_context("trace-hash", session_id="s-1", user_id="7")
    try:
        config = _config(EmittingWorkflow())
        await _consume(create_streaming_response(config))
    finally:
        reset_trace_context(token)
    event = last_event(caplog, "agent.request.completed")
    assert event["traceId"] == "trace-hash"
    assert event["sessionHash"] == hash_value("s-1")
    assert event["userHash"] == hash_value("7")
    assert event["sessionHash"] != "s-1"


class FakeStore:
    def __init__(self):
        self.saved = []

    async def save_message(self, session_id, role, content, tool_calls=None):
        self.saved.append((session_id, role, content))

    async def get_messages(self, session_id):
        return []

    async def update_session_title(self, session_id, title):
        pass

    async def get_pending_action(self, session_id, user_id):
        return None


class CapturingGraph:
    async def astream(self, state, stream_mode=None):
        yield ("values", {"result": "ok"})


def test_stream_chat_establishes_trace_context():
    svc = ChatService(store=FakeStore(), graph=CapturingGraph(), settings=None)

    async def _run():
        await svc.stream_chat("s1", "确认", 7, "USER")
        return get_session_hash(), get_user_hash()

    session_hash, user_hash = asyncio.run(_run())
    assert session_hash == hash_value("s1")
    assert user_hash == hash_value("7")
