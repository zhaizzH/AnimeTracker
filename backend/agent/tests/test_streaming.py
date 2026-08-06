import asyncio

from app.core.event_bus import emit_answer_delta
from app.core.streaming import StreamConfig, create_streaming_response


class FakeWorkflow:
    async def astream(self, state, stream_mode=None):
        emit_answer_delta("你好")
        yield ("values", {"result": "fallback"})


def _collect_stream(text_stream):
    async def _consume():
        parts = []
        async for item in text_stream:
            parts.append(item)
        return parts

    return asyncio.run(_consume())


def test_stream_emits_answer_then_end():
    config = StreamConfig(workflow=FakeWorkflow(), build_initial_state=lambda: {})
    resp = create_streaming_response(config)
    lines = _collect_stream(resp.body_iterator)

    assert lines[0].startswith("data: ")
    assert '"type": "answer"' in lines[0]
    assert '"text": "你好"' in lines[0]
    assert '"is_end": true' in lines[-1]


def test_stream_fallback_text_when_no_delta():
    class NoDeltaWorkflow:
        async def astream(self, state, stream_mode=None):
            yield ("values", {"result": "兜底文本"})

    config = StreamConfig(workflow=NoDeltaWorkflow(), build_initial_state=lambda: {}, extract_final_content=lambda s: str(s.get("result") or ""))
    lines = _collect_stream(create_streaming_response(config).body_iterator)
    assert '"text": "兜底文本"' in lines[0]


def test_stream_error_emits_friendly_answer():
    class BoomWorkflow:
        async def astream(self, state, stream_mode=None):
            raise RuntimeError("boom")

    config = StreamConfig(
        workflow=BoomWorkflow(),
        build_initial_state=lambda: {},
        map_exception=lambda exc: "服务暂时不可用，请稍后再试",
    )
    lines = _collect_stream(create_streaming_response(config).body_iterator)
    assert '"text": "服务暂时不可用，请稍后再试"' in lines[0]
    assert '"is_end": true' in lines[-1]
