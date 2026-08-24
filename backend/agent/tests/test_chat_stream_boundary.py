import inspect
import json

from app.chat.events import AgentEvent, AgentEventType


def test_chat_service_returns_internal_event_iterator():
    from app.chat.service import ChatService

    assert inspect.isasyncgenfunction(ChatService.stream_chat)


def test_chat_package_has_no_fastapi_import():
    for module in ("app/chat/service.py", "app/chat/streaming.py", "app/chat/event_sink.py"):
        source = open(module, encoding="utf-8").read()
        assert "fastapi" not in source


def test_sse_adapter_maps_internal_answer_event():
    from app.api.sse import serialize_agent_event

    raw = serialize_agent_event(AgentEvent(type=AgentEventType.ANSWER, text="你好"))
    assert '"type":"answer"' in raw.replace(" ", "")
    assert '"text":"你好"' in raw.replace(" ", "")


async def test_function_call_sse_preserves_node_from_internal_stream():
    from app.api.sse import serialize_agent_event
    from app.chat.event_sink import emit_function_call
    from app.chat.streaming import StreamConfig, stream_agent_events

    class Workflow:
        async def astream(self, state, stream_mode):
            emit_function_call(
                node="tool:search",
                state="start",
                message="正在调用 Search",
                name="Search",
                arguments='{"q":"eva"}',
            )
            yield "values", {"result": ""}

    config = StreamConfig(workflow=Workflow(), build_initial_state=lambda: {})
    events = [event async for event in stream_agent_events(config)]
    raw = serialize_agent_event(events[0])
    payload = json.loads(raw.removeprefix("data: ").strip())

    assert payload["type"] == "function_call"
    assert payload["content"]["node"] == "tool:search"
    assert payload["content"]["state"] == "start"
    assert payload["content"]["name"] == "Search"


async def test_sse_response_preserves_all_agent_event_fields_and_order():
    from app.api.sse import create_sse_response

    async def events():
        yield AgentEvent(type=AgentEventType.ANSWER, text="第一段")
        yield AgentEvent(type=AgentEventType.THINKING, text="正在推理")
        yield AgentEvent(
            type=AgentEventType.FUNCTION_CALL,
            text="调用工具",
            node="tool:search",
            parent_node="gateway",
            state="start",
            message="正在调用 Search",
            result="未完成",
            name="Search",
            arguments='{"q":"eva"}',
            meta={"traceId": "trace-7"},
        )
        yield AgentEvent(type=AgentEventType.STATUS, node="tool:search", state="end", result="完成")
        yield AgentEvent(type=AgentEventType.END)

    response = create_sse_response(events())
    frames = [chunk async for chunk in response.body_iterator]
    payloads = [json.loads(frame.removeprefix("data: ").strip()) for frame in frames]

    assert [payload.get("type") for payload in payloads] == ["answer", "thinking", "function_call", "status", "answer"]
    assert payloads[0]["content"] == {"text": "第一段"}
    assert payloads[1]["content"] == {"text": "正在推理"}
    assert payloads[2]["content"] == {
        "text": "调用工具",
        "node": "tool:search",
        "parent_node": "gateway",
        "state": "start",
        "message": "正在调用 Search",
        "result": "未完成",
        "name": "Search",
        "arguments": '{"q":"eva"}',
    }
    assert payloads[2]["meta"] == {"traceId": "trace-7"}
    assert payloads[3]["content"] == {"node": "tool:search", "state": "end", "result": "完成"}
    assert payloads[4]["content"] == {}
    assert payloads[4]["is_end"] is True
