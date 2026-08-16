import json
import logging
import time

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk

from app.core.agent_runtime import agent_invoke, agent_stream


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
