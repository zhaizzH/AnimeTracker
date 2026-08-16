import asyncio
import json
import logging
import time

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk

from app.core.agent_runtime import _run_async, agent_invoke, agent_stream
from app.core.observability import get_trace_id, reset_trace_context, set_trace_context


def last_event(caplog, event_name):
    for record in reversed(caplog.records):
        try:
            payload = json.loads(record.message)
        except (ValueError, TypeError):
            continue
        if payload.get("event") == event_name:
            return payload
    raise AssertionError(f"no {event_name!r} event captured")


class FakeInvokeAgent:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    async def ainvoke(self, payload):
        if self.error is not None:
            raise self.error
        return self.result


class FakeStreamAgent:
    def __init__(self, chunks=None, error=None):
        self.chunks = chunks or []
        self.error = error

    async def astream(self, payload, stream_mode=None):
        if self.error is not None:
            raise self.error
        for chunk in self.chunks:
            yield chunk


def _ok_stream_chunks(text="你好"):
    return [
        ("values", {"messages": []}),
        ("messages", (AIMessageChunk(content=""), {"langgraph_node": "model"})),
        ("messages", (AIMessageChunk(content=text), {"langgraph_node": "model"})),
    ]


def test_stream_logs_first_token_and_total_time(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    agent = FakeStreamAgent(chunks=_ok_stream_chunks())
    monkeypatch.setattr(time, "perf_counter", iter([1.0, 1.2, 1.8]).__next__)
    agent_stream(agent, [], slot="client_recommend", provider="deepseek", model="m")
    event = last_event(caplog, "agent.model.completed")
    assert event["firstTokenMs"] == 200
    assert event["durationMs"] == 800
    assert event["slot"] == "client_recommend"
    assert event["provider"] == "deepseek"
    assert event["model"] == "m"
    assert event["success"] is True


def test_stream_exception_logs_failure_and_reraises(caplog):
    caplog.set_level(logging.INFO)
    agent = FakeStreamAgent(error=ValueError("gateway returned invalid JSON"))
    with pytest.raises(ValueError, match="gateway returned invalid JSON"):
        agent_stream(agent, [])
    event = last_event(caplog, "agent.model.completed")
    assert event["success"] is False
    assert event["errorType"] == "MODEL_RESPONSE_INVALID"
    assert "firstTokenMs" not in event  # 无输出不伪造 firstTokenMs


def test_agent_invoke_success_logs_completed(caplog):
    caplog.set_level(logging.INFO)
    agent = FakeInvokeAgent(result={"messages": [AIMessage(content="ok")]})
    result = agent_invoke(agent, [], slot="client_route", provider="dashscope", model="qwen-plus")
    assert result.content == "ok"
    event = last_event(caplog, "agent.model.completed")
    assert event["success"] is True
    assert event["slot"] == "client_route"
    assert event["provider"] == "dashscope"
    assert event["model"] == "qwen-plus"


def test_agent_invoke_exception_logs_failure_and_reraises(caplog):
    caplog.set_level(logging.INFO)
    agent = FakeInvokeAgent(error=RuntimeError("boom"))
    with pytest.raises(RuntimeError, match="boom"):
        agent_invoke(agent, [])
    event = last_event(caplog, "agent.model.completed")
    assert event["success"] is False
    assert event["errorType"] == "INTERNAL_ERROR"


def test_agent_invoke_invalid_response_still_logs_completed(caplog):
    caplog.set_level(logging.INFO)
    agent = FakeInvokeAgent(result="not a dict")
    result = agent_invoke(agent, [])
    assert result.content == ""
    event = last_event(caplog, "agent.model.completed")
    assert event["success"] is True


def test_run_async_preserves_trace_context_across_thread_pool():
    """_run_async 线程池分支必须复制 ContextVar：线程内 get_trace_id() 与主线程同值。"""

    async def probe():
        return get_trace_id()

    async def main():
        token = set_trace_context("trace-across-pool")
        try:
            return _run_async(probe())
        finally:
            reset_trace_context(token)

    # asyncio.run 内存在运行中的 loop → _run_async 走 ThreadPoolExecutor + copy_context 分支
    assert asyncio.run(main()) == "trace-across-pool"
