"""四项副作用的集中回归（implement.md 步骤 4）。

1. 孤立 user 消息：任何终止路径都必须补一条 assistant 消息（成功/部分/完全无内容）；
2. 工具中间态：未闭合工具必须有终态，不能永久 running；
3. pending_action：正常路径落库、被 stop 的跳过；
4. 资源：断连不取消 run、shutdown 有超时上限、退订即摘除队列。

测试边界仍是 ``ChatRunManager`` 公开接口；用裸事件生成器精确构造边界情形，
避免依赖 workflow 的间接行为。
"""

import asyncio

import pytest

from app.chat.events import AgentEvent, AgentEventType
from app.chat.runs import INTERRUPTED_PREFIX, ChatRunManager, RunStatus


def _recorder():
    saved: list[tuple[str, list[str]]] = []

    async def save(answer: str, tools: list[str]) -> None:
        saved.append((answer, tools))

    return saved, save


async def _empty_events():
    """不含任何 answer 的事件流：模拟「一个字都没生成」。"""
    yield AgentEvent(type=AgentEventType.END)


async def _failing_without_answer():
    """只有错误信号、没有任何 answer 文本的失败流。"""
    yield AgentEvent(type=AgentEventType.STATUS, state="error", message="上游超时")
    yield AgentEvent(type=AgentEventType.END)


async def _open_tool(release: asyncio.Event):
    """吐一个未闭合的工具调用，然后挂住直到 release——模拟「生成到一半」。"""
    yield AgentEvent(
        type=AgentEventType.FUNCTION_CALL, name="rag_search_subjects", state="start"
    )
    await release.wait()


async def _stubborn(release: asyncio.Event):
    """对 cancel 免疫的生成器：用来验证 shutdown 的超时上限真的生效。"""
    yield AgentEvent(
        type=AgentEventType.FUNCTION_CALL, name="rag_search_subjects", state="start"
    )
    while not release.is_set():
        try:
            await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            continue
    yield AgentEvent(type=AgentEventType.END)


# --------------------------------------------------------------------------- #
# 4.1 孤立 user 消息
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_failed_run_without_answer_still_persists_interrupted_marker() -> None:
    """失败且无任何回答时也必须落一条 assistant，否则用户消息永久孤立。"""
    saved, save = _recorder()
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1", user_id=1, events=_failing_without_answer(), on_answer_completed=save
    )
    await asyncio.wait_for(run.task, timeout=1.0)

    assert run.status is RunStatus.FAILED
    assert len(saved) == 1
    assert saved[0][0] == INTERRUPTED_PREFIX, "不能落空串，否则历史里是一条空消息"


@pytest.mark.asyncio
async def test_successful_run_without_answer_does_not_persist_empty_message() -> None:
    """正常结束但没有任何回答内容时不写空消息（不制造噪声）。"""
    saved, save = _recorder()
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1", user_id=1, events=_empty_events(), on_answer_completed=save
    )
    await asyncio.wait_for(run.task, timeout=1.0)

    assert run.status is RunStatus.DONE
    assert saved == []


@pytest.mark.asyncio
async def test_each_run_persists_exactly_once() -> None:
    """幂等：stop 后再自然跑完，不得重复落库（既有 + 补充各算一次）。"""
    saved, save = _recorder()
    manager = ChatRunManager(store=None)

    async def events():
        yield AgentEvent(type=AgentEventType.ANSWER, text="部分")
        yield AgentEvent(type=AgentEventType.END)

    run = await manager.start(
        session_id="s1", user_id=1, events=events(), on_answer_completed=save
    )
    await manager.stop(run.run_id)
    await asyncio.wait_for(run.task, timeout=1.0)

    assert len(saved) == 1
    assert saved[0][0] == f"{INTERRUPTED_PREFIX}部分"


# --------------------------------------------------------------------------- #
# 4.2 工具中间态
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_no_tool_frame_is_left_running_after_stop() -> None:
    """R3：stop 之后订阅者看到的最后一个工具帧必须是终态。"""
    release = asyncio.Event()
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_open_tool(release))
    subscriber = manager.subscribe(run.run_id)
    await subscriber.__anext__()  # start 帧
    await manager.stop(run.run_id)
    seen = [event async for event in subscriber]

    tool_frames = [e for e in seen if e.type is AgentEventType.FUNCTION_CALL]
    assert tool_frames[-1].state == "end"
    assert tool_frames[-1].result == "aborted"
    release.set()
    await asyncio.wait_for(run.task, timeout=1.0)


@pytest.mark.asyncio
async def test_disconnect_alone_does_not_synthesise_tool_terminal() -> None:
    """Q12：单纯断连（未 stop）不合成终态——run 还在跑，工具并未中断。"""
    release = asyncio.Event()
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_open_tool(release))
    subscriber = manager.subscribe(run.run_id)
    await subscriber.__anext__()
    await subscriber.aclose()

    await asyncio.sleep(0)
    aborted = [e for e in run.events if e.result == "aborted"]
    assert aborted == []
    assert run.status is RunStatus.RUNNING
    release.set()
    await asyncio.wait_for(run.task, timeout=1.0)


# --------------------------------------------------------------------------- #
# 4.4 资源
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_unsubscribe_removes_queue_from_run() -> None:
    """退订必须摘除队列，否则长命 run 会一直持有死队列。"""
    release = asyncio.Event()
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_open_tool(release))
    subscriber = manager.subscribe(run.run_id)
    await subscriber.__anext__()
    assert len(run.subscribers) == 1

    await subscriber.aclose()
    assert run.subscribers == set()
    release.set()
    await asyncio.wait_for(run.task, timeout=1.0)


@pytest.mark.asyncio
async def test_shutdown_cancels_pending_runs() -> None:
    """D9：关闭时取消所有 run 并等待，不无限挂住进程。"""
    release = asyncio.Event()
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_open_tool(release))
    await asyncio.sleep(0)

    await asyncio.wait_for(manager.shutdown(), timeout=2.0)
    assert run.task.done()
    assert run.status is not RunStatus.RUNNING


@pytest.mark.asyncio
async def test_shutdown_gives_up_after_timeout(monkeypatch) -> None:
    """D9 上限：底层对 cancel 免疫时，shutdown 不得永久阻塞。"""
    import app.chat.runs as runs_module

    monkeypatch.setattr(runs_module, "SHUTDOWN_TIMEOUT_SECONDS", 0.05)
    release = asyncio.Event()
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_stubborn(release))
    await asyncio.sleep(0)

    started = asyncio.get_running_loop().time()
    await asyncio.wait_for(manager.shutdown(), timeout=2.0)
    assert asyncio.get_running_loop().time() - started < 1.0, "超时上限未生效"
    assert not run.task.done(), "故意的：底层不响应 cancel"

    release.set()
    await asyncio.wait_for(asyncio.gather(run.task, return_exceptions=True), timeout=2.0)
