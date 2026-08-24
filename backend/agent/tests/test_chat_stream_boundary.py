import inspect

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
