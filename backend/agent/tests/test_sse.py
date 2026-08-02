from app.schemas.sse_response import AssistantResponse, Content, MessageType, serialize_sse


def test_serialize_sse_excludes_none():
    r = AssistantResponse(content=Content(text="你好"))
    s = serialize_sse(r)
    assert s.startswith("data: ")
    assert '"text": "你好"' in s
    assert '"is_end": false' in s
    assert '"arguments"' not in s  # None 字段被排除


def test_message_type_values():
    assert MessageType.ANSWER.value == "answer"
    assert MessageType.FUNCTION_CALL.value == "function_call"


def test_default_type_is_answer():
    r = AssistantResponse(content=Content())
    assert r.type == MessageType.ANSWER
