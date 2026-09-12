import pytest

from app.chat.events import AgentEventType
from app.chat.streaming import StreamConfig, stream_agent_events


class _FallbackWorkflow:
    async def astream(self, _state, stream_mode):
        assert stream_mode == ["values"]
        yield "values", {"result": "fallback answer"}


@pytest.mark.asyncio
async def test_fallback_answer_is_persisted_and_emitted() -> None:
    saved: list[str] = []

    async def save_answer(answer: str, _tools: list[str]) -> None:
        saved.append(answer)

    events = [
        event
        async for event in stream_agent_events(
            StreamConfig(
                workflow=_FallbackWorkflow(),
                build_initial_state=lambda: {},
                extract_final_content=lambda state: state.get("result", ""),
                on_answer_completed=save_answer,
            )
        )
    ]

    assert [event.type for event in events] == [AgentEventType.ANSWER, AgentEventType.END]
    assert events[0].text == "fallback answer"
    assert saved == ["fallback answer"]


@pytest.mark.asyncio
async def test_persistence_failure_emits_error_status_and_still_ends() -> None:
    def fail_to_save(_answer: str, _tools: list[str]) -> None:
        raise RuntimeError("store down")

    events = [
        event
        async for event in stream_agent_events(
            StreamConfig(
                workflow=_FallbackWorkflow(),
                build_initial_state=lambda: {},
                extract_final_content=lambda state: state.get("result", ""),
                on_answer_completed=fail_to_save,
            )
        )
    ]

    assert events[0].type is AgentEventType.ANSWER
    assert any(event.type is AgentEventType.STATUS and event.state == "error" for event in events)
    assert events[-1].type is AgentEventType.END
