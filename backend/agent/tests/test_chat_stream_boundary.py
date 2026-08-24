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
