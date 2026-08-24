import json

from app.api.schemas.sse import AssistantResponse, Content, MessageType, serialize_sse


def test_answer_sse_wire_contract_is_stable():
    raw = serialize_sse(AssistantResponse(type=MessageType.ANSWER, content=Content(text="你好")))

    assert raw.startswith("data: ")
    assert raw.endswith("\n\n")

    payload = json.loads(raw.removeprefix("data: ").strip())
    assert payload["type"] == "answer"
    assert payload["content"]["text"] == "你好"
    assert payload["is_end"] is False


def test_end_sse_wire_contract_is_stable():
    raw = serialize_sse(AssistantResponse(content=Content(), is_end=True))

    payload = json.loads(raw.removeprefix("data: ").strip())
    assert payload["is_end"] is True
