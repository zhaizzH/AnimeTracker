"""SSE wire 契约：序列化是单一入口，帧格式与字段集不得静默漂移。

覆盖 ``app/api/sse.py`` 与 ``app/api/schemas/sse.py``。契约事实：
每帧只有 ``data:`` 行、``\\n\\n`` 分帧、类型在 JSON 内部、``exclude_none`` 剔除空字段、
``end`` 事件以 ``is_end=true`` 表达（``MessageType`` 枚举不含 ``end``）。
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.api.schemas.sse import AssistantResponse, Content, MessageType, serialize_sse
from app.api.sse import create_sse_response, serialize_agent_event
from app.chat.events import AgentEvent, AgentEventType

def _payload(frame: str) -> dict:
    """剥离 ``data: `` 前缀并解析 JSON，同时断言分帧形态。"""
    assert frame.startswith("data: "), f"帧必须以 'data: ' 开头: {frame!r}"
    assert frame.endswith("\n\n"), f"帧必须以空行结束: {frame!r}"
    return json.loads(frame[len("data: "):-2])

# --------------------------------------------------------------------------- #
# serialize_agent_event：五类事件
# --------------------------------------------------------------------------- #

def test_answer_event_maps_type_and_text() -> None:
    data = _payload(serialize_agent_event(AgentEvent(type=AgentEventType.ANSWER, text="你好")))
    assert data["type"] == "answer"
    assert data["content"] == {"text": "你好"}
    assert data["is_end"] is False
    assert isinstance(data["timestamp"], int)

@pytest.mark.parametrize(
    ("event_type", "wire_type"),
    [
        (AgentEventType.THINKING, "thinking"),
        (AgentEventType.FUNCTION_CALL, "function_call"),
        (AgentEventType.STATUS, "status"),
    ],
)
def test_event_type_enum_maps_to_wire_value(event_type: AgentEventType, wire_type: str) -> None:
    data = _payload(serialize_agent_event(AgentEvent(type=event_type)))
    assert data["type"] == wire_type

def test_status_event_carries_state_and_message() -> None:
    data = _payload(serialize_agent_event(AgentEvent(
        type=AgentEventType.STATUS, state="error", message="保存失败",
    )))
    assert data["type"] == "status"
    assert data["content"]["state"] == "error"
    assert data["content"]["message"] == "保存失败"

def test_function_call_event_carries_name_and_arguments() -> None:
    data = _payload(serialize_agent_event(AgentEvent(
        type=AgentEventType.FUNCTION_CALL, name="search", arguments='{"q":"x"}',
    )))
    assert data["content"]["name"] == "search"
    assert data["content"]["arguments"] == '{"q":"x"}'

def test_node_fields_are_serialized_when_present() -> None:
    data = _payload(serialize_agent_event(AgentEvent(
        type=AgentEventType.ANSWER, text="t", node="n1", parent_node="n0",
    )))
    assert data["content"]["node"] == "n1"
    assert data["content"]["parent_node"] == "n0"

def test_result_field_is_serialized_when_present() -> None:
    data = _payload(serialize_agent_event(AgentEvent(
        type=AgentEventType.ANSWER, result="tool-output",
    )))
    assert data["content"]["result"] == "tool-output"

def test_meta_is_serialized_when_present() -> None:
    data = _payload(serialize_agent_event(AgentEvent(
        type=AgentEventType.STATUS, state="error", meta={"persistence": "answer", "success": False},
    )))
    assert data["meta"] == {"persistence": "answer", "success": False}

def test_end_event_uses_is_end_marker_not_type_end() -> None:
    """``end`` 不进入 ``MessageType``；靠 ``is_end=true`` 表达。"""
    data = _payload(serialize_agent_event(AgentEvent(type=AgentEventType.END)))
    assert data["is_end"] is True
    assert data["type"] == "answer"          # 默认值，而非 "end"
    assert "end" not in {m.value for m in MessageType}
    assert data["content"] == {}             # 空 Content 经 exclude_none 后为空对象

# --------------------------------------------------------------------------- #
# serialize_sse：exclude_none 与分帧
# --------------------------------------------------------------------------- #

def test_exclude_none_drops_empty_content_fields() -> None:
    data = _payload(serialize_sse(AssistantResponse(content=Content(text="只有text"))))
    assert data["content"] == {"text": "只有text"}
    for absent in ("node", "parent_node", "state", "message", "result", "name", "arguments"):
        assert absent not in data["content"]

def test_exclude_none_drops_none_meta_but_keeps_empty_dict() -> None:
    assert "meta" not in _payload(serialize_sse(AssistantResponse()))
    assert _payload(serialize_sse(AssistantResponse(meta={})))["meta"] == {}

def test_frame_uses_data_prefix_and_blank_line_terminator() -> None:
    frame = serialize_sse(AssistantResponse(content=Content(text="x")))
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    assert frame.count("\n\n") == 1

def test_non_ascii_is_not_escaped() -> None:
    frame = serialize_sse(AssistantResponse(content=Content(text="中文内容")))
    assert "中文内容" in frame            # ensure_ascii=False（不转义非 ASCII）
    assert "\\u" not in frame

# --------------------------------------------------------------------------- #
# create_sse_response：media type 与响应头
# --------------------------------------------------------------------------- #

def _collect(response) -> list[str]:
    async def drain() -> list[str]:
        return [chunk async for chunk in response.body_iterator]

    return asyncio.run(drain())

def test_response_declares_event_stream_media_type_and_headers() -> None:
    async def events():
        yield AgentEvent(type=AgentEventType.ANSWER, text="hi")

    response = create_sse_response(events())
    assert response.media_type == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["connection"] == "keep-alive"
    assert response.headers["x-accel-buffering"] == "no"

def test_response_streams_one_frame_per_event_and_ends() -> None:
    async def events():
        yield AgentEvent(type=AgentEventType.ANSWER, text="hi")
        yield AgentEvent(type=AgentEventType.END)

    chunks = _collect(create_sse_response(events()))
    assert len(chunks) == 2
    assert _payload(chunks[0])["content"]["text"] == "hi"
    assert _payload(chunks[1])["is_end"] is True
