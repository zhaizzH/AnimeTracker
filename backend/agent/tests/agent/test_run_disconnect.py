"""断连行为矩阵：刷新页面（客户端断连）时，已产出的回答是否落库。

对应任务 ``10-22-fix-agent-stream-disconnect``。

run 解耦落地后，落库不再由 ``stream_agent_events`` 承担（D1 回调提升），而是由
``ChatRunManager._drive`` 统一负责。因此本矩阵改为在 manager 层验证：把事件流喂给
manager，模拟客户端订阅后断连。

- A 挂起流程 + 中途断连 → 答案仍落库（AC1）
- B 快速完成 + 读完     → 对照组
- C 快速完成 + 中途断连 → 断连不丢答案
- D 同 A，断言「断连后应落库」→ 去掉 xfail，转正为回归测试
"""
import asyncio

import pytest

from app.chat.event_sink import emit_answer_delta
from app.chat.events import AgentEventType
from app.chat.runs import ChatRunManager
from app.chat.streaming import StreamConfig, stream_agent_events


def _events(workflow):
    return stream_agent_events(StreamConfig(workflow=workflow, build_initial_state=dict))


async def _collect(wf, *, disconnect_after_first_answer: bool) -> list[str]:
    """启动 run，按需在收到第一条 answer 后断连，等 run 跑完，返回落库的答案。"""
    saved: list[str] = []

    async def save(answer: str, _tools: list[str]) -> None:
        saved.append(answer)

    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s", user_id=1, events=_events(wf), on_answer_completed=save
    )
    if disconnect_after_first_answer:
        subscriber = manager.subscribe(run.run_id)
        async for event in subscriber:
            if event.type is AgentEventType.ANSWER:
                break
        await subscriber.aclose()
    if hasattr(wf, "release"):
        wf.release.set()
    await asyncio.wait_for(run.task, timeout=1.0)
    return saved


class _HangingWorkflow:
    """先吐出答案，然后挂起——模拟答案已到屏幕、流程尚未跑完。"""

    def __init__(self) -> None:
        self.release = asyncio.Event()

    async def astream(self, _state, stream_mode):
        emit_answer_delta("A")
        yield "values", {}
        await self.release.wait()


class _FastWorkflow:
    async def astream(self, _state, stream_mode):
        emit_answer_delta("A")
        yield "values", {}


@pytest.mark.asyncio
async def test_disconnect_keeps_partial_answer_while_running() -> None:
    """变体 A：挂起流程中途断连——已生成内容不丢，run 继续跑。"""
    workflow = _HangingWorkflow()
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s", user_id=1, events=_events(workflow)
    )
    subscriber = manager.subscribe(run.run_id)
    async for event in subscriber:
        if event.type is AgentEventType.ANSWER:
            break
    await subscriber.aclose()

    await asyncio.sleep(0)
    assert not run.task.done(), "断连不得取消 run"

    workflow.release.set()
    await asyncio.wait_for(run.task, timeout=1.0)
    assert run.status.value == "done"


@pytest.mark.asyncio
async def test_full_read_persists_answer() -> None:
    """变体 B：完整读完时正常落库，证明对照组本身健康。"""
    assert await _collect(_FastWorkflow(), disconnect_after_first_answer=False) == ["A"]


@pytest.mark.asyncio
async def test_disconnect_during_tail_still_persists() -> None:
    """变体 C：与流程快慢无关，断连不再丢答案。"""
    assert await _collect(_FastWorkflow(), disconnect_after_first_answer=True) == ["A"]


@pytest.mark.asyncio
async def test_answer_survives_client_disconnect() -> None:
    """变体 D（AC1 载体）：挂起流程中途断连，答案仍落库。"""
    assert await _collect(_HangingWorkflow(), disconnect_after_first_answer=True) == ["A"]
