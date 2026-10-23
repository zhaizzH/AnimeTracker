"""ChatRunManager 行为测试：断连不取消 run、逻辑停止、持久化保证。

对应任务 ``10-22-fix-agent-stream-disconnect``，决策 D1–D10。
测试边界是 ``ChatRunManager`` 的公开接口（start/subscribe/stop/active_for_session），
不触碰 ``_drive`` 等私有实现。
"""
import asyncio

import pytest

from app.chat.event_sink import emit_answer_delta, emit_function_call
from app.chat.events import AgentEventType
from app.chat.runs import ChatRunManager, RunStatus
from app.chat.streaming import StreamConfig, stream_agent_events


class _GatedWorkflow:
    """吐出答案后挂起，直到测试放行——模拟「已上屏、流程未跑完」。"""

    def __init__(self, *, tool: bool = False) -> None:
        self.release = asyncio.Event()
        self.tool = tool

    async def astream(self, _state, stream_mode):
        if self.tool:
            emit_function_call(node="search_agent", state="start", name="rag_search_subjects")
        emit_answer_delta("A")
        yield "values", {}
        await self.release.wait()
        emit_answer_delta("B")
        yield "values", {}


class _FastWorkflow:
    async def astream(self, _state, stream_mode):
        emit_answer_delta("A")
        yield "values", {}


def _events(workflow):
    return stream_agent_events(StreamConfig(workflow=workflow, build_initial_state=dict))


def _recorder():
    saved: list[tuple[str, list[str]]] = []

    async def save(answer: str, tools: list[str]) -> None:
        saved.append((answer, tools))

    return saved, save


async def _drain(subscriber) -> list:
    seen = []
    async for event in subscriber:
        seen.append(event)
    return seen


@pytest.mark.asyncio
async def test_disconnect_does_not_cancel_run_and_answer_persists() -> None:
    """AC1/AC2：订阅者断连后 run 继续跑完，答案最终落库。"""
    saved, save = _recorder()
    workflow = _GatedWorkflow()
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1", user_id=1, events=_events(workflow), on_answer_completed=save
    )

    subscriber = manager.subscribe(run.run_id)
    first = await subscriber.__anext__()
    assert first.type is AgentEventType.ANSWER
    await subscriber.aclose()  # 客户端刷新 = 退订

    await asyncio.sleep(0)
    assert not run.task.done(), "断连不得取消 run"
    assert run.status is RunStatus.RUNNING

    workflow.release.set()  # 流程自然跑完
    await asyncio.wait_for(run.task, timeout=1.0)

    assert run.status is RunStatus.DONE
    assert saved == [("AB", [])]


@pytest.mark.asyncio
async def test_stop_returns_immediately_and_marks_cancelled() -> None:
    """D3：stop 立即返回，不等底层流程跑完？——不，它标记 cancelled 并封存事件。"""
    saved, save = _recorder()
    workflow = _GatedWorkflow(tool=True)
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1", user_id=1, events=_events(workflow), on_answer_completed=save
    )

    subscriber = manager.subscribe(run.run_id)
    await subscriber.__anext__()  # 工具 start 帧

    stopped = await manager.stop(run.run_id)
    assert stopped is True
    assert run.status is RunStatus.CANCELLED
    assert not run.task.done(), "stop 不得取消底层 task（D3）"

    workflow.release.set()
    await asyncio.wait_for(run.task, timeout=1.0)
    assert saved and saved[0][0].startswith("*（生成已中断）*")


@pytest.mark.asyncio
async def test_stop_synthesises_aborted_tool_frame_and_single_end() -> None:
    """R3 + R4：stop 时未闭合工具收到 aborted 终态，且恰好一个 END。"""
    workflow = _GatedWorkflow(tool=True)
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_events(workflow))

    subscriber = manager.subscribe(run.run_id)
    await subscriber.__anext__()  # 消费工具 start 帧
    await manager.stop(run.run_id)

    events = await _drain(subscriber)
    aborted = [
        e for e in events
        if e.type is AgentEventType.FUNCTION_CALL and e.result == "aborted"
    ]
    assert len(aborted) == 1
    assert aborted[0].name == "rag_search_subjects"
    assert [e for e in events if e.type is AgentEventType.END].__len__() == 1
    assert events[-1].type is AgentEventType.END
    workflow.release.set()
    await asyncio.wait_for(run.task, timeout=1.0)


@pytest.mark.asyncio
async def test_stop_seals_event_stream() -> None:
    """D6：stop 之后底层产出的事件不再进入缓冲。"""
    workflow = _GatedWorkflow()
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_events(workflow))

    subscriber = manager.subscribe(run.run_id)
    await subscriber.__anext__()
    await manager.stop(run.run_id)
    await _drain(subscriber)

    workflow.release.set()
    await asyncio.wait_for(run.task, timeout=1.0)

    assert not any(e.text == "B" for e in run.events), "stop 后事件必须封存"


@pytest.mark.asyncio
async def test_cancelled_run_skips_pending_action() -> None:
    """D7：被 stop 的 run 不落 pending_action。"""
    from app.chat.pending_action import PendingAction
    from app.chat.pending_events import emit_pending_action_clear

    pending_written: list = []

    async def on_pending(event) -> None:
        pending_written.append(event)

    class _PendingWorkflow:
        async def astream(self, _state, stream_mode):
            emit_pending_action_clear()  # 工具真的报告了一个 pending 变更
            emit_answer_delta("A")
            yield "values", {}
            await manager_release.wait()

    manager_release = asyncio.Event()
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1",
        user_id=1,
        events=_events(_PendingWorkflow()),
        on_pending_action=on_pending,
    )
    await manager.stop(run.run_id)
    manager_release.set()
    await asyncio.wait_for(run.task, timeout=1.0)

    assert pending_written == [], "被 stop 的 run 不得落 pending_action"


@pytest.mark.asyncio
async def test_pending_action_persisted_on_normal_completion() -> None:
    """R3 反向：正常路径（含断连后台跑完）pending_action 照常落库。"""
    from app.chat.pending_events import emit_pending_action_clear

    pending_written: list = []

    async def on_pending(event) -> None:
        pending_written.append(event)

    class _PendingWorkflow:
        async def astream(self, _state, stream_mode):
            emit_pending_action_clear()
            emit_answer_delta("A")
            yield "values", {}

    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1", user_id=1, events=_events(_PendingWorkflow()), on_pending_action=on_pending
    )
    await asyncio.wait_for(run.task, timeout=1.0)

    assert [e.operation for e in pending_written] == ["CLEAR"]


@pytest.mark.asyncio
async def test_failed_run_aborts_open_tools_and_marks_answer_interrupted() -> None:
    """R3：流程异常时工具不得停在 running，答案落库带中断前缀。"""
    saved, save = _recorder()

    class _ExplodingWorkflow:
        async def astream(self, _state, stream_mode):
            emit_function_call(node="search_agent", state="start", name="rag_search_subjects")
            emit_answer_delta("A")
            yield "values", {}
            raise RuntimeError("LLM 挂了")

    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1", user_id=1, events=_events(_ExplodingWorkflow()), on_answer_completed=save
    )
    await asyncio.wait_for(run.task, timeout=1.0)

    aborted = [
        e for e in run.events
        if e.type is AgentEventType.FUNCTION_CALL and e.result == "aborted"
    ]
    assert len(aborted) == 1
    assert [e for e in run.events if e.type is AgentEventType.END].__len__() == 1
    assert run.events[-1].type is AgentEventType.END
    # 答案 = 已生成内容 + 用户看到的错误文案；失败信号已由文案承载，不重复加前缀
    assert saved and saved[0][0].startswith("A")
    assert "处理请求时出错" in saved[0][0]
    assert not saved[0][0].startswith("*（生成已中断）*")


@pytest.mark.asyncio
async def test_active_for_session_ignores_cancelled() -> None:
    """D8：cancelled 不算 active，新 run 可直接启动。"""
    workflow = _GatedWorkflow()
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_events(workflow))

    assert manager.active_for_session("s1") is run
    await manager.stop(run.run_id)
    assert manager.active_for_session("s1") is None
    assert manager.active_for_session("other") is None

    workflow.release.set()
    await asyncio.wait_for(run.task, timeout=1.0)


@pytest.mark.asyncio
async def test_subscribe_replays_from_cursor() -> None:
    """重连回放：after=N 精确从第 N 条开始，不漏不重。"""
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1", user_id=1, events=_events(_FastWorkflow())
    )
    await asyncio.wait_for(run.task, timeout=1.0)

    all_events = await _drain(manager.subscribe(run.run_id, after=0))
    tail = await _drain(manager.subscribe(run.run_id, after=1))
    assert tail == all_events[1:]
    assert [e for e in all_events if e.type is AgentEventType.END].__len__() == 1


@pytest.mark.asyncio
async def test_persist_future_resolves_after_persistence() -> None:
    """D4：persist_future 在落库完成后 resolve，供下一条 run 排队。"""
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_events(_FastWorkflow()))
    assert not run.persist_future.done()
    await asyncio.wait_for(run.persist_future, timeout=1.0)
    assert run.persist_future.done()
