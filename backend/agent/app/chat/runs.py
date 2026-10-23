"""Chat run 生命周期：把「一次对话生成」从 HTTP 请求里解耦出来。

设计见 ``.trellis/tasks/10-22-fix-agent-stream-disconnect/design.md``。

核心不变量：

- run 只由进程关闭取消；订阅者断连只退订（D3/D6）。
- 持久化由 ``_drive`` 的 finally 唯一负责（D1 回调提升）。
- ``stop()`` 是逻辑停止：标记 cancelled + 合成工具终态 + 立即返回，底层 task 自然
  跑完后再落库已生成部分（D3）。
- 封存（D6）：stop 之后产出的事件不再进入缓冲、不再广播。

contextvar 纪律：``pending_action_collector`` 由 ``_drive`` 自己 set/reset。不能由
``start()`` 设置后委托 ``_drive`` 重置——Token 绑定创建它的 Context，跨任务 reset
会抛 ``ValueError: was created in a different Context``。
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.chat.events import AgentEvent, AgentEventType
from app.chat.pending_events import (
    PendingActionEvent,
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)

from app.chat.run_state import RunState

logger = logging.getLogger(__name__)

INTERRUPTED_PREFIX = "*（生成已中断）*"

# 事件缓冲上限：事件数或累计文本字节，先到者截断（design §2.1）
MAX_BUFFER_EVENTS = 2000
MAX_BUFFER_BYTES = 1_000_000

SHUTDOWN_TIMEOUT_SECONDS = 10.0


class RunStatus(str, Enum):
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ChatRun:
    run_id: str
    session_id: str
    user_id: int
    status: RunStatus = RunStatus.RUNNING
    events: list[AgentEvent] = field(default_factory=list)
    buffer_start: int = 0
    subscribers: set[asyncio.Queue] = field(default_factory=set)
    task: asyncio.Task | None = None
    persist_future: asyncio.Future | None = None
    open_tools: list[str] = field(default_factory=list)


class ChatRunManager:
    """进程内 run 注册表。每条 run 由一个 asyncio.Task 驱动。"""

    def __init__(
        self,
        store: Any,
        ttl_seconds: int = 900,
        run_state_store: Any = None,
    ) -> None:
        self._store = store
        self._ttl_seconds = ttl_seconds
        # 可选的状态投影（design §2.2）；None 时纯内存，方便测试与单进程场景。
        self._run_state_store = run_state_store
        self._runs: dict[str, ChatRun] = {}
        self._tasks: set[asyncio.Task] = set()  # 强引用，避免 run 被 GC

    # ---------------------------------------------------------------- 生命周期

    async def start(
        self,
        *,
        session_id: str,
        user_id: int,
        events: AsyncIterator[AgentEvent],
        on_answer_completed: Callable[[str, list[str]], Awaitable[None] | None] | None = None,
        on_pending_action: Callable[[PendingActionEvent], Awaitable[None] | None] | None = None,
    ) -> ChatRun:
        run = ChatRun(run_id=uuid.uuid4().hex, session_id=session_id, user_id=user_id)
        run.persist_future = asyncio.get_running_loop().create_future()
        self._runs[run.run_id] = run
        task = asyncio.create_task(
            self._drive(run, events, on_answer_completed, on_pending_action),
            name=f"chat-run-{run.run_id}",
        )
        run.task = task
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        await self._project(run)
        return run

    # ---------------------------------------------------------------- 状态投影

    async def _project(self, run: ChatRun) -> None:
        """把 run 状态写为持久投影（design §2.2）。失败不影响主流程。"""
        if self._run_state_store is None:
            return
        try:
            await self._run_state_store.save_run_state(
                RunState(
                    run_id=run.run_id,
                    session_id=run.session_id,
                    user_id=run.user_id,
                    status=run.status.value,
                    event_count=len(run.events),
                )
            )
            await self._run_state_store.save_session_run(run.session_id, run.run_id)
        except Exception:
            logger.warning("run 状态投影失败 run_id=%s", run.run_id, exc_info=True)

    async def resolve_session_run(self, session_id: str) -> RunState | None:
        """供重连端查该会话的 run（Q13）。内存优先，否则读投影并收敛（D9）。

        内存里没有、投影却写着 ``running``，说明写入它的进程已经不在了：
        收敛为 ``failed``，返回给调用方的是收敛后的状态。
        """
        active = self.active_for_session(session_id)
        if active is not None:
            return RunState(
                run_id=active.run_id,
                session_id=active.session_id,
                user_id=active.user_id,
                status=active.status.value,
                event_count=len(active.events),
            )
        latest = self.latest_for_session(session_id)
        if latest is not None:
            return RunState(
                run_id=latest.run_id,
                session_id=latest.session_id,
                user_id=latest.user_id,
                status=latest.status.value,
                event_count=len(latest.events),
            )
        if self._run_state_store is None:
            return None
        run_id = await self._run_state_store.get_session_run(session_id)
        if run_id is None:
            return None
        state = await self._run_state_store.get_run_state(run_id)
        if state is None:
            return None
        if state.status == RunStatus.RUNNING.value:
            state = RunState(
                run_id=state.run_id,
                session_id=state.session_id,
                user_id=state.user_id,
                status=RunStatus.FAILED.value,
                event_count=state.event_count,
            )
            await self._run_state_store.save_run_state(state)
            logger.info("收敛重启遗留的 running run run_id=%s", state.run_id)
        return state

    def get(self, run_id: str) -> ChatRun | None:
        return self._runs.get(run_id)

    def latest_for_session(self, session_id: str) -> ChatRun | None:
        """该会话最近一条 run（无论状态），供 D4 等待上一条落库。"""
        latest: ChatRun | None = None
        for run in self._runs.values():
            if run.session_id == session_id:
                latest = run  # dict 保留插入顺序，后写覆盖前写
        return latest

    def active_for_session(self, session_id: str) -> ChatRun | None:
        """只认 RUNNING；cancelled 的后台 task 不算 active（D8）。"""
        for run in self._runs.values():
            if run.session_id == session_id and run.status is RunStatus.RUNNING:
                return run
        return None

    async def stop(self, run_id: str) -> bool:
        """逻辑停止（D3）：标记 cancelled、补齐工具终态、立即返回。

        不 cancel 底层 task——同步节点跑在 LangGraph 的 executor 里，取消只能落在
        节点边界，物理停止在当前架构下不存在。底层跑完后由 ``_drive`` 落库部分答案。
        """
        run = self._runs.get(run_id)
        if run is None or run.status is not RunStatus.RUNNING:
            return False
        run.status = RunStatus.CANCELLED
        self._finish(run)
        await self._project(run)
        return True

    def subscribe(self, run_id: str, *, after: int = 0) -> AsyncIterator[AgentEvent]:
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError(run_id)
        return self._subscription(run, after)

    async def shutdown(self) -> None:
        """进程关闭：取消所有 run 并等待，最长 10s（D9）。

        用 ``asyncio.wait`` 而不是 ``wait_for(gather(...))``：后者超时时会再取消一次
        被等待的任务，并等取消完成——若任务对 cancel 免疫，二次等待会无上限挂住，
        正好把这个超时保护变成陷阱。
        """
        tasks = [
            run.task
            for run in self._runs.values()
            if run.task is not None and not run.task.done()
        ]
        if not tasks:
            return
        for task in tasks:
            task.cancel()
        _, pending = await asyncio.wait(tasks, timeout=SHUTDOWN_TIMEOUT_SECONDS)
        if pending:
            logger.warning(
                "chat run shutdown 超时 %.0fs，放弃等待 %d 条 run",
                SHUTDOWN_TIMEOUT_SECONDS,
                len(pending),
            )

    # ---------------------------------------------------------------- 订阅

    async def _subscription(self, run: ChatRun, after: int) -> AsyncIterator[AgentEvent]:
        """先回放已缓冲事件，再挂队列；退出只退订，绝不 cancel run（D3）。

        Q10：每个订阅者拿到的第一帧都带 ``meta.run_id``，客户端据此重连。
        """
        queue: asyncio.Queue = asyncio.Queue()
        if after < run.buffer_start:
            # Q14：请求的游标已被缓冲上限截断，明确告知而非静默丢事件
            yield self._with_run_id(
                run,
                AgentEvent(
                    type=AgentEventType.STATUS,
                    state="warning",
                    message="部分实时内容已过期，完整回答请查看历史记录",
                ),
            )
        start = max(after, run.buffer_start)
        for event in run.events[start - run.buffer_start :]:
            yield self._with_run_id(run, event)
        if run.status is not RunStatus.RUNNING:
            return
        run.subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                if event is None:
                    return
                yield self._with_run_id(run, event)
        finally:
            run.subscribers.discard(queue)

    @staticmethod
    def _with_run_id(run: ChatRun, event: AgentEvent) -> AgentEvent:
        """给事件补 ``meta.run_id``（Q10）。已带则不覆盖。"""
        if event.meta.get("run_id"):
            return event
        return AgentEvent(
            type=event.type,
            text=event.text,
            state=event.state,
            message=event.message,
            result=event.result,
            name=event.name,
            node=event.node,
            parent_node=event.parent_node,
            arguments=event.arguments,
            meta={**event.meta, "run_id": run.run_id},
        )

    # ---------------------------------------------------------------- 驱动

    async def _drive(
        self,
        run: ChatRun,
        events: AsyncIterator[AgentEvent],
        on_answer_completed: Callable[[str, list[str]], Awaitable[None] | None] | None,
        on_pending_action: Callable[[PendingActionEvent], Awaitable[None] | None] | None,
    ) -> None:
        aggregated: list[str] = []
        used_tools: list[str] = []
        buffer_bytes = 0
        failed = False
        error_message: str | None = None
        pending_token = set_pending_action_collector()
        try:
            async for event in events:
                if run.status is RunStatus.CANCELLED:
                    # 封存（D6）：stop 后不再对外可见，但答案仍聚合以便落库
                    if event.type is AgentEventType.END:
                        break
                    if event.type is AgentEventType.ANSWER and event.text:
                        aggregated.append(event.text)
                    continue
                if event.type is AgentEventType.END:
                    continue  # END 由 _finish 统一补，避免重复
                if event.type is AgentEventType.STATUS and event.state == "error":
                    failed = True
                    error_message = event.message
                run.events.append(event)
                buffer_bytes += len(event.text or "")
                if event.type is AgentEventType.ANSWER and event.text:
                    aggregated.append(event.text)
                elif event.type is AgentEventType.FUNCTION_CALL and event.name:
                    if event.state == "start":
                        if event.name not in used_tools:
                            used_tools.append(event.name)
                        if event.name not in run.open_tools:
                            run.open_tools.append(event.name)
                    elif event.state == "end" and event.name in run.open_tools:
                        run.open_tools.remove(event.name)
                self._broadcast(run, event)
                self._trim_buffer(run, buffer_bytes)
            if run.status is RunStatus.RUNNING:
                run.status = RunStatus.FAILED if failed else RunStatus.DONE
        except asyncio.CancelledError:
            if run.status is RunStatus.RUNNING:
                run.status = RunStatus.CANCELLED
            raise
        except Exception:
            logger.exception("chat run 驱动失败 run_id=%s", run.run_id)
            if run.status is RunStatus.RUNNING:
                run.status = RunStatus.FAILED
        finally:
            try:
                answer = "".join(aggregated)
                if answer:
                    # D5：仅在「没有显式错误文案」时加中断前缀。FAILED 的答案里已经带着
                    # 用户看到的错误提示，再加前缀是重复信号。
                    if run.status is not RunStatus.DONE and error_message is None:
                        answer = f"{INTERRUPTED_PREFIX}{answer}"
                elif run.status is not RunStatus.DONE:
                    # 一个字都没生成就失败了：仍要补一条消息，否则 user 消息永久孤立。
                    answer = INTERRUPTED_PREFIX
                # else: 正常结束且无内容 → 不落库，避免制造空消息噪声。
                if answer and on_answer_completed is not None:
                    try:
                        result = on_answer_completed(answer, used_tools)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception:
                        logger.exception("chat run 答案落库失败 run_id=%s", run.run_id)
                        self._emit_persistence_failure(run, "answer", "回答保存失败，请稍后重试")
                if on_pending_action is not None and run.status is not RunStatus.CANCELLED:
                    # D7：被 stop 的 run 不落 pending_action
                    pending = get_pending_action_event()
                    if pending is not None:
                        try:
                            result = on_pending_action(pending)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception:
                            logger.exception(
                                "chat run pending_action 落库失败 run_id=%s", run.run_id
                            )
                            self._emit_persistence_failure(
                                run, "pending_action", "待确认动作保存失败，请重试"
                            )
            except asyncio.CancelledError:
                # 二次取消：尽力而为，答案可能丢失，由 stale-run 收敛兜底（D9）
                raise
            finally:
                self._finish(run)
                await self._project(run)
                reset_pending_action_collector(pending_token)
                if run.persist_future is not None and not run.persist_future.done():
                    run.persist_future.set_result(None)

    def _emit_persistence_failure(self, run: ChatRun, kind: str, message: str) -> None:
        """落库失败时告知订阅者；已封存（stop）的 run 不再追加帧，否则 END 会不末尾。"""
        if run.status is RunStatus.CANCELLED:
            return
        event = AgentEvent(
            type=AgentEventType.STATUS,
            state="error",
            message=message,
            meta={"persistence": kind, "success": False},
        )
        run.events.append(event)
        self._broadcast(run, event)

    def _finish(self, run: ChatRun) -> None:
        """收尾事件流：补齐未闭合工具终态 + 唯一 END 帧 + 关闭订阅者。

        R3：非正常结束（stop/失败/取消）时，``running`` 中的工具不得永久悬挂，
        这里合成 ``state=end, result=aborted`` 终态帧。
        R4：无论哪条路径，缓冲里恰好一个 END 且位于末尾。
        幂等：重复调用不会重复追加。
        """
        if run.status is RunStatus.RUNNING:
            run.status = RunStatus.DONE
        # R3：流终止时仍在 running 的工具必须有终态，否则前端永久转圈。
        for name in list(run.open_tools):
            event = AgentEvent(
                type=AgentEventType.FUNCTION_CALL,
                name=name,
                state="end",
                result="aborted",
                message="生成已中断",
            )
            run.events.append(event)
            self._broadcast(run, event)
        run.open_tools.clear()
        if not run.events or run.events[-1].type is not AgentEventType.END:
            end = AgentEvent(type=AgentEventType.END)
            run.events.append(end)
            self._broadcast(run, end)
        self._broadcast(run, None)

    def _trim_buffer(self, run: ChatRun, buffer_bytes: int) -> None:
        """超出事件数/字节上限时丢弃最旧事件，并推进 buffer_start（Q14）。"""
        while run.events and (
            len(run.events) > MAX_BUFFER_EVENTS or buffer_bytes > MAX_BUFFER_BYTES
        ):
            dropped = run.events.pop(0)
            run.buffer_start += 1
            buffer_bytes -= len(dropped.text or "")

    def _broadcast(self, run: ChatRun, event: AgentEvent | None) -> None:
        for queue in list(run.subscribers):
            queue.put_nowait(event)
