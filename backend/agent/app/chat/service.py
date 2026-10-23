import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from app.chat.events import AgentEvent
from app.chat.ports import ChatStore
from app.shared.observability import get_trace_id, set_trace_context
from app.chat.pending_events import PendingActionEvent
from app.chat.runs import ChatRun, ChatRunManager
from app.chat.streaming import StreamConfig, stream_agent_events
from app.chat.user import UserInfo

logger = logging.getLogger(__name__)

# D4：等待同会话上一条 run 落库的上限。一次 Redis rpush 远低于此值，
# 超时即降级继续，避免一次抖动卡死整个会话。
PERSIST_WAIT_SECONDS = 5.0


@dataclass
class _Prepared:
    events: AsyncIterator[AgentEvent]
    on_answer_completed: Any
    on_pending_action: Any


class ChatService:
    """编排 store + graph + 内部事件流,负责历史加载、落库回调和初始 state。"""

    def __init__(self, store: ChatStore, graph, settings, runs: ChatRunManager | None = None):
        self.store = store
        self.graph = graph
        self.settings = settings
        self.runs = runs if runs is not None else ChatRunManager(store=store)

    # ------------------------------------------------------------------ run 化

    async def start_run(
        self,
        session_id: str,
        content: str,
        user_id: int,
        role: str,
        token: str = "",
    ) -> ChatRun:
        """启动一条后台 run 并立即返回；SSE 响应只是它的订阅者。

        D4：落 user 消息前先等同会话上一条 run 落库完成，保证消息顺序；超时降级。
        """
        await self._await_previous_persist(session_id)
        # 建立请求级上下文(不覆盖已有 traceId): session/user 只记录匿名哈希
        set_trace_context(get_trace_id(), session_id=session_id, user_id=str(user_id))
        prepared = await self._prepare(
            session_id=session_id,
            content=content,
            user_id=user_id,
            role=role,
            token=token,
        )
        return await self.runs.start(
            session_id=session_id,
            user_id=user_id,
            events=prepared.events,
            on_answer_completed=prepared.on_answer_completed,
            on_pending_action=prepared.on_pending_action,
        )
    async def _await_previous_persist(self, session_id: str) -> None:
        """等待同会话上一条 run 的落库完成（D4），超时或失败降级继续。"""
        previous = self.runs.latest_for_session(session_id)
        if previous is None or previous.persist_future is None:
            return
        if previous.persist_future.done():
            return
        try:
            await asyncio.wait_for(
                asyncio.shield(previous.persist_future), timeout=PERSIST_WAIT_SECONDS
            )
        except asyncio.TimeoutError:  # noqa: UP041 - 兼容 3.10 命名
            logger.warning(
                "等待上一条 run 落库超时 %.0fs，继续写新消息 session=%s",
                PERSIST_WAIT_SECONDS,
                session_id,
            )
        except Exception:
            logger.warning("上一条 run 落库失败，继续写新消息 session=%s", session_id, exc_info=True)

    async def stream_chat(
        self,
        session_id: str,
        content: str,
        user_id: int,
        role: str,
        token: str = "",
    ) -> AsyncIterator[AgentEvent]:
        """向后兼容的薄壳：启动 run 并订阅它。"""
        run = await self.start_run(
            session_id=session_id,
            content=content,
            user_id=user_id,
            role=role,
            token=token,
        )
        async for event in self.runs.subscribe(run.run_id):
            yield event

    # ------------------------------------------------------------------ 准备

    async def _prepare(
        self,
        *,
        session_id: str,
        content: str,
        user_id: int,
        role: str,
        token: str = "",
    ) -> _Prepared:
        await self.store.save_message(session_id, "user", content)
        history = await self.store.get_messages(session_id)

        if len(history) == 1:
            try:
                await self.store.update_session_title(session_id, content[:20])
            except Exception:
                pass

        history_messages = []
        for m in history:
            if m.role == "user":
                history_messages.append(HumanMessage(content=m.content))
            else:
                history_messages.append(AIMessage(content=m.content))

        user = UserInfo(user_id=user_id, username="", role=role, token=token)

        pending_action = await self.store.get_pending_action(session_id, user_id)

        def build_initial_state() -> dict:
            state = {
                "user": user,
                "history_messages": history_messages,
                "current_question": content,
                "routing": None,
                "result": "",
                "session_id": session_id,
                "pending_action": pending_action,
                "pending_preview_id": getattr(pending_action, "preview_id", None),
                "write_confirmed": False,
            }
            return state

        async def on_answer_completed(answer_text: str, used_tools: list[str]) -> None:
            await self.store.save_message(
                session_id,
                "assistant",
                answer_text,
                json.dumps(used_tools) if used_tools else None,
            )

        async def on_pending_action(event: PendingActionEvent) -> None:
            if event.operation == "CLEAR":
                await self.store.delete_pending_action(session_id, user_id)
            elif event.action is not None:
                await self.store.save_pending_action(session_id, event.action, ttl_seconds=600)

        config = StreamConfig(
            workflow=self.graph,
            build_initial_state=build_initial_state,
            extract_final_content=lambda s: str(s.get("result") or ""),
            map_exception=lambda exc: "处理请求时出错，请重试",
        )
        return _Prepared(
            events=stream_agent_events(config),
            on_answer_completed=on_answer_completed,
            on_pending_action=on_pending_action,
        )
