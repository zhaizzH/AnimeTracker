"""断连行为矩阵：刷新页面（客户端断连）时，已产出的回答是否落库。

对应任务 ``10-22-fix-agent-stream-disconnect``。四个变体把因果固定住：

- A 挂起流程 + 中途断连 → 当前 ``[]``（用户症状：回答丢失）
- B 快速完成 + 读完     → ``["A"]``（正常路径，作为对照组必须绿）
- C 快速完成 + 中途断连 → 当前 ``[]``（断连即丢，与流程是否跑完无关）
- D 同 A，断言「断连后应落库」→ 标记 ``xfail(strict=True)``，即当前缺陷

D 是修复的验收载体。run 解耦落地后它必须转绿，strict 模式会强制清理该标记。
"""
import asyncio

import pytest

from app.chat.event_sink import emit_answer_delta
from app.chat.events import AgentEventType
from app.chat.streaming import StreamConfig, stream_agent_events


async def _collect(wf, *, disconnect_after_first_answer: bool) -> list[str]:
    saved: list[str] = []

    async def save(answer: str, _tools: list[str]) -> None:
        saved.append(answer)

    gen = stream_agent_events(
        StreamConfig(workflow=wf, build_initial_state=dict, on_answer_completed=save)
    )
    async for event in gen:
        if disconnect_after_first_answer and event.type is AgentEventType.ANSWER:
            break
    await gen.aclose()
    return saved


class _HangingWorkflow:
    """先吐出答案，然后挂起——模拟答案已到屏幕、流程尚未跑完。"""

    async def astream(self, _state, stream_mode):
        emit_answer_delta("A")
        yield "values", {}
        await asyncio.Event().wait()


class _FastWorkflow:
    async def astream(self, _state, stream_mode):
        emit_answer_delta("A")
        yield "values", {}


@pytest.mark.asyncio
async def test_disconnect_loses_answer() -> None:
    """变体 A：断连时答案未落库（缺陷现场）。"""
    assert await _collect(_HangingWorkflow(), disconnect_after_first_answer=True) == []


@pytest.mark.asyncio
async def test_full_read_persists_answer() -> None:
    """变体 B：完整读完时正常落库，证明对照组本身健康。"""
    assert await _collect(_FastWorkflow(), disconnect_after_first_answer=False) == ["A"]


@pytest.mark.asyncio
async def test_disconnect_during_tail_loses_answer() -> None:
    """变体 C：与流程快慢无关，断连即丢。"""
    assert await _collect(_FastWorkflow(), disconnect_after_first_answer=True) == []


@pytest.mark.xfail(
    strict=True,
    reason="缺陷：on_answer_completed 位于消费循环之后，断连触发 GeneratorExit 时被跳过；"
           "run 解耦（10-22-fix-agent-stream-disconnect）落地后应转绿并删除此标记",
)
@pytest.mark.asyncio
async def test_answer_survives_client_disconnect() -> None:
    """变体 D：断连后答案仍应落库——修复的验收标准（AC1）。"""
    assert await _collect(_HangingWorkflow(), disconnect_after_first_answer=True) == ["A"]
