"""ChatRunManager 行为测试：断连不取消 run、逻辑停止、持久化保证。

对应任务 ``10-22-fix-agent-stream-disconnect``，决策 D1–D10。
测试边界是 ``ChatRunManager`` 的公开接口（start/subscribe/stop/active_for_session），
不触碰 ``_drive`` 等私有实现。
"""
import asyncio

import pytest

from app.chat.event_sink import emit_answer_delta, emit_function_call
import app.chat.runs as runs_module
from app.chat.events import AgentEvent, AgentEventType
from app.chat.run_state import RunState
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

# `ui_action` 目前没有业务节点在产（属 navigation-graph），所以测试直接给 `start()` 喂脚本化
# 事件迭代器——这正是 `ChatRunManager` 的公开入口，不碰 `_drive` 写入侧。
UI_ACTION_META = {
    "action": "open_anime_index",
    "params": {"year": 2022},
    "path": "/anime?year=2022&page=1",
    "label": "2022 年的番",
}

async def _scripted(events: list[AgentEvent]):
    for event in events:
        yield event


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
async def test_failed_run_does_not_fake_tool_terminal_but_persists_answer() -> None:
    """R3：异常路径不伪造工具终态（前端已由 status=error 帧得知出错）；答案落库仍带中断前缀。"""
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
    assert aborted == [], "异常路径不得伪造工具终态；aborted 是 stop 的专属信号"
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
async def test_replay_marks_ui_action_but_keeps_frames_one_to_one() -> None:
    """D1：重放段的 `ui_action` 仍下发（不跳帧）但补 `replayed=true`。

    帧数必须与 `run.events` 保持 1:1：前端 `after` 是已收帧数、后端 `start` 是缓冲下标，
    跳帧会让两者错位，后续重连重放/遗漏其它帧。
    """
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1",
        user_id=1,
        events=_scripted([
            AgentEvent(type=AgentEventType.ANSWER, text="A"),
            AgentEvent(type=AgentEventType.UI_ACTION, meta=dict(UI_ACTION_META)),
            AgentEvent(type=AgentEventType.ANSWER, text="B"),
        ]),
    )
    await asyncio.wait_for(run.task, timeout=1.0)

    replayed = await _drain(manager.subscribe(run.run_id, after=0))
    assert len(replayed) == len(run.events), "重放帧数必须与缓冲下标 1:1"

    marked = [e for e in replayed if e.type is AgentEventType.UI_ACTION]
    assert len(marked) == 1, "重放段不得跳过 ui_action"
    assert marked[0].meta["replayed"] is True
    assert marked[0].meta["path"] == UI_ACTION_META["path"]
    assert marked[0].meta["run_id"] == run.run_id

    buffered = run.events[1]
    assert "replayed" not in buffered.meta, "缓冲里那份保持原样供回溯，不得原地改"

@pytest.mark.asyncio
async def test_live_subscription_does_not_mark_ui_action() -> None:
    """实时段不打标：只有重放才要求前端忽略。"""
    release = asyncio.Event()

    async def events():
        yield AgentEvent(type=AgentEventType.UI_ACTION, meta=dict(UI_ACTION_META))
        await release.wait()

    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=events())

    subscriber = manager.subscribe(run.run_id)
    first = await subscriber.__anext__()
    assert first.type is AgentEventType.UI_ACTION
    assert "replayed" not in first.meta
    assert first.meta["run_id"] == run.run_id
    # 真正锁住「meta 不被剔除」：只断言 run_id 不够，run_id 是 _with_run_id 补的，
    # 不能证明 ui_action 自身的载荷 survived（path/label 都在其中）
    assert first.meta["action"] == UI_ACTION_META["action"]
    assert first.meta["path"] == UI_ACTION_META["path"]
    assert first.meta["label"] == UI_ACTION_META["label"]

    release.set()
    await asyncio.wait_for(run.task, timeout=1.0)
    await subscriber.aclose()

@pytest.mark.asyncio
async def test_two_consecutive_reconnects_neither_duplicate_nor_skip() -> None:
    """游标回归：after 用前端口径（已收帧数）续订时不得重放或遗漏任何帧。"""
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1",
        user_id=1,
        events=_scripted([
            AgentEvent(type=AgentEventType.ANSWER, text="1"),
            AgentEvent(type=AgentEventType.UI_ACTION, meta=dict(UI_ACTION_META)),
            AgentEvent(type=AgentEventType.ANSWER, text="2"),
        ]),
    )
    await asyncio.wait_for(run.task, timeout=1.0)

    first = await _drain(manager.subscribe(run.run_id, after=0))
    second = await _drain(manager.subscribe(run.run_id, after=len(first)))
    assert len(first) == len(run.events)
    assert second == [], f"续订不应再收到帧，实际 {[e.type for e in second]}"
    assert [e.text for e in first if e.type is AgentEventType.ANSWER] == ["1", "2"]

@pytest.mark.asyncio
async def test_truncated_buffer_still_warns_first(monkeypatch) -> None:
    """Q14 不回归：游标被截断时首帧仍是 warning，之后的 `ui_action` 照常打标。"""
    monkeypatch.setattr(runs_module, "MAX_BUFFER_EVENTS", 3)
    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s1",
        user_id=1,
        events=_scripted([
            AgentEvent(type=AgentEventType.ANSWER, text="1"),
            AgentEvent(type=AgentEventType.ANSWER, text="2"),
            AgentEvent(type=AgentEventType.ANSWER, text="3"),
            AgentEvent(type=AgentEventType.UI_ACTION, meta=dict(UI_ACTION_META)),
        ]),
    )
    await asyncio.wait_for(run.task, timeout=1.0)
    assert run.buffer_start > 0, "前提：缓冲确实被截断"

    seen = await _drain(manager.subscribe(run.run_id, after=0))
    assert seen[0].type is AgentEventType.STATUS and seen[0].state == "warning"
    marked = [e for e in seen if e.type is AgentEventType.UI_ACTION]
    assert marked and marked[0].meta["replayed"] is True

@pytest.mark.asyncio
async def test_persist_future_resolves_after_persistence() -> None:
    """D4：persist_future 在落库完成后 resolve，供下一条 run 排队。"""
    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_events(_FastWorkflow()))
    assert not run.persist_future.done()
    await asyncio.wait_for(run.persist_future, timeout=1.0)
    assert run.persist_future.done()


@pytest.mark.asyncio
async def test_persistence_failure_emits_error_status_and_still_ends_once() -> None:
    """落库失败时订阅者仍收到 status/error 帧，且 END 仍是最后一帧（R4）。"""

    async def boom(_answer: str, _tools: list[str]) -> None:
        raise RuntimeError("写库失败")

    manager = ChatRunManager(store=None)
    run = await manager.start(
        session_id="s", user_id=1, events=_events(_FastWorkflow()), on_answer_completed=boom
    )
    seen = await _drain(manager.subscribe(run.run_id))
    await asyncio.wait_for(run.task, timeout=1.0)

    errors = [e for e in seen if e.type is AgentEventType.STATUS and e.state == "error"]
    assert errors and errors[0].message
    assert [e for e in seen if e.type is AgentEventType.END].__len__() == 1
    assert seen[-1].type is AgentEventType.END

# --------------------------------------------------------------------------- #
# D9：跨重启的懒加载 stale 收敛
# --------------------------------------------------------------------------- #

class _MemoryRunState:
    """RunStateStore 替身：只用字典，验证 manager 的收敛行为而非 Redis 细节。"""

    def __init__(self) -> None:
        self.states: dict[str, dict] = {}
        self.session_runs: dict[str, str] = {}

    async def save_run_state(self, state) -> None:
        self.states[state.run_id] = {
            "session_id": state.session_id,
            "user_id": state.user_id,
            "status": state.status,
            "event_count": state.event_count,
        }

    async def get_run_state(self, run_id: str):
        data = self.states.get(run_id)
        if data is None:
            return None
        return RunState(run_id=run_id, **data)

    async def save_session_run(self, session_id: str, run_id: str) -> None:
        self.session_runs[session_id] = run_id

    async def get_session_run(self, session_id: str) -> str | None:
        return self.session_runs.get(session_id)


@pytest.mark.asyncio
async def test_run_state_is_projected_to_store() -> None:
    """每次状态变化都要投影到持久层，供重启后的其他进程观测（design §2.2）。"""
    state_store = _MemoryRunState()
    manager = ChatRunManager(store=None, run_state_store=state_store)
    run = await manager.start(session_id="s1", user_id=1, events=_events(_FastWorkflow()))
    await asyncio.wait_for(run.task, timeout=1.0)

    assert state_store.session_runs["s1"] == run.run_id
    assert state_store.states[run.run_id]["status"] == "done"
    assert state_store.states[run.run_id]["event_count"] > 0


@pytest.mark.asyncio
async def test_stale_running_state_converges_to_failed() -> None:
    """D9：投影说 running 但内存无此 run（进程重启过）→ 收敛为 failed。"""
    state_store = _MemoryRunState()
    await state_store.save_run_state(
        RunState(run_id="dead", session_id="s1", user_id=1, status="running")
    )
    await state_store.save_session_run("s1", "dead")

    manager = ChatRunManager(store=None, run_state_store=state_store)
    info = await manager.resolve_session_run("s1")
    assert info is not None
    assert info.run_id == "dead"
    assert info.status == "failed"
    assert state_store.states["dead"]["status"] == "failed"


@pytest.mark.asyncio
async def test_resolve_session_run_uses_projection_when_memory_is_empty() -> None:
    """重连端拿到的 run 记录来自投影，而不是内存（跨进程可读）。"""
    state_store = _MemoryRunState()
    await state_store.save_run_state(
        RunState(run_id="r9", session_id="s1", user_id=1, status="done", event_count=4)
    )
    await state_store.save_session_run("s1", "r9")

    manager = ChatRunManager(store=None, run_state_store=state_store)
    info = await manager.resolve_session_run("s1")
    assert info is not None
    assert (info.run_id, info.status, info.event_count) == ("r9", "done", 4)

# ---------------------------------------------------------------- turn-bag 生命周期（design D2）

@pytest.mark.asyncio
async def test_drive_installs_turn_state_and_resets_after_run() -> None:
    """turn-bag 由 `_drive` 安装（Token 绑定创建它的 Context），跑完后清空。"""
    from app.agent.client.actions.turn_state import get_turn_state, mark_pending_resolved

    inside: list = []

    class _TurnReadingWorkflow:
        async def astream(self, _state, stream_mode):
            turn = get_turn_state()
            inside.append(turn)
            mark_pending_resolved()
            inside.append(get_turn_state().pending_resolved)
            emit_answer_delta("A")
            yield "values", {}

    assert get_turn_state() is None

    manager = ChatRunManager(store=None)
    run = await manager.start(session_id="s1", user_id=1, events=_events(_TurnReadingWorkflow()))
    await asyncio.wait_for(run.task, timeout=1.0)

    assert inside[0] is not None, "run 内必须有 turn-bag"
    assert inside[1] is True, "打标对同一回合可见"
    assert get_turn_state() is None, "run 结束后必须 reset，避免跨回合残留"
