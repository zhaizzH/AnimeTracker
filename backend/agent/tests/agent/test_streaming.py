"""``stream_agent_events`` 作为纯事件生产者的契约。

D1（回调提升）之后，本函数不再调用 ``on_answer_completed`` / ``on_pending_action``
——收尾与落库由 ``ChatRunManager._drive`` 负责。因此这里只断言事件产出顺序与内容，
落库行为在 ``test_chat_run_manager.py`` 覆盖。
"""
import pytest

from app.chat.events import AgentEventType
from app.chat.streaming import StreamConfig, stream_agent_events


class _FallbackWorkflow:
    async def astream(self, _state, stream_mode):
        assert stream_mode == ["values"]
        yield "values", {"result": "fallback answer"}


class _ExplodingWorkflow:
    async def astream(self, _state, stream_mode):
        yield "values", {}
        raise RuntimeError("llm down")


@pytest.mark.asyncio
async def test_fallback_answer_is_emitted() -> None:
    """没有流式增量时，从最终 state 提取答案并产出。"""
    events = [
        event
        async for event in stream_agent_events(
            StreamConfig(
                workflow=_FallbackWorkflow(),
                build_initial_state=lambda: {},
                extract_final_content=lambda state: state.get("result", ""),
            )
        )
    ]

    assert [event.type for event in events] == [AgentEventType.ANSWER, AgentEventType.END]
    assert events[0].text == "fallback answer"


@pytest.mark.asyncio
async def test_streaming_does_not_persist() -> None:
    """D1：本函数绝不调用落库回调，即使调用方传了。"""
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

    assert events[0].text == "fallback answer"
    assert saved == [], "落库必须由 ChatRunManager 负责，不得在事件生产者里发生"


@pytest.mark.asyncio
async def test_workflow_error_emits_answer_and_error_status() -> None:
    """工作流异常：产出错误文案 ANSWER + 显式 error STATUS，供 manager 标 FAILED。"""
    events = [
        event
        async for event in stream_agent_events(
            StreamConfig(
                workflow=_ExplodingWorkflow(),
                build_initial_state=lambda: {},
                map_exception=lambda _exc: "处理请求时出错，请重试",
            )
        )
    ]

    assert events[0].type is AgentEventType.ANSWER
    assert events[0].text == "处理请求时出错，请重试"
    error_status = [
        e for e in events if e.type is AgentEventType.STATUS and e.state == "error"
    ]
    assert len(error_status) == 1
    assert events[-1].type is AgentEventType.END
