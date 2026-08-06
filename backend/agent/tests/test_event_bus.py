import app.core.event_bus as bus


def test_emitter_roundtrip():
    captured = []
    token = bus.set_status_emitter(captured.append)
    try:
        bus.emit_answer_delta("你好")
        bus.emit_function_call(node="tool:search_subjects", state="start", name="search_subjects", arguments="{}")
        bus.emit_thinking_delta("推理中")
    finally:
        bus.reset_status_emitter(token)

    assert captured[0]["type"] == "answer"
    assert captured[0]["content"]["text"] == "你好"
    assert captured[1]["type"] == "function_call"
    assert captured[1]["content"]["state"] == "start"
    assert captured[1]["content"]["name"] == "search_subjects"


def test_no_emitter_is_noop():
    bus.emit_answer_delta("x")  # 不应抛异常


def test_emitter_exception_is_swallowed():
    def _boom(_payload):
        raise RuntimeError("boom")

    token = bus.set_status_emitter(_boom)
    try:
        bus.emit_answer_delta("x")  # 不应抛异常
    finally:
        bus.reset_status_emitter(token)
