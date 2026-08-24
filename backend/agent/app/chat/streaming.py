import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.chat.event_sink import reset_event_sink, set_event_sink
from app.chat.events import AgentEvent, AgentEventType
from app.shared.observability import (
    classify_error,
    elapsed_ms,
    get_session_hash,
    get_user_hash,
    log_event,
)
from app.chat.pending_events import PendingActionEvent, get_pending_action_event, reset_pending_action_collector, set_pending_action_collector

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    workflow: Any
    build_initial_state: Callable[[], dict]
    extract_final_content: Callable[[dict], str] | None = None
    map_exception: Callable[[Exception], str] | None = None
    on_answer_completed: Callable[[str, list[str]], Awaitable[None] | None] | None = None
    on_pending_action: Callable[[PendingActionEvent], Awaitable[None] | None] | None = None


def _build_agent_event(payload: AgentEvent | dict) -> AgentEvent | None:
    if isinstance(payload, AgentEvent):
        if payload.type is AgentEventType.FUNCTION_CALL and payload.node is not None:
            return AgentEvent(
                type=payload.type,
                text=payload.text,
                state=payload.state,
                message=payload.message,
                result=payload.result,
                name=payload.name,
                node=None,
                parent_node=payload.parent_node,
                arguments=payload.arguments,
                meta=payload.meta,
            )
        return payload
    if not isinstance(payload, dict):
        return None
    content = payload.get("content")
    if not isinstance(content, dict):
        return None
    try:
        event_type = AgentEventType(payload.get("type"))
    except ValueError:
        event_type = AgentEventType.STATUS
    node = content.get("node")
    if event_type is AgentEventType.FUNCTION_CALL:
        node = None  # 不暴露内部工具节点标识
    return AgentEvent(
        type=event_type,
        text=content.get("text"),
        state=content.get("state"),
        message=content.get("message"),
        result=content.get("result"),
        name=content.get("name"),
        node=node,
        parent_node=content.get("parent_node"),
        arguments=content.get("arguments"),
        meta=payload.get("meta") if isinstance(payload.get("meta"), dict) else {},
    )


def _extract_route_target(latest_state: dict) -> str | None:
    routing = latest_state.get("routing") or {}
    target = routing.get("route_target")
    return target if isinstance(target, str) and target else None


async def stream_agent_events(config: StreamConfig) -> AsyncIterator[AgentEvent]:
    """执行 workflow 并按产生顺序输出内部 AgentEvent。"""
    state = config.build_initial_state()
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    class _QueueEventSink:
        def emit(self, event: AgentEvent) -> None:
            # 同一事件循环内直接入队(否则 call_soon_threadsafe 的延迟可能让
            # 同步 "done" 先入队而丢掉已发射事件);跨线程(节点经 _run_async 线程池)
            # 时仍走 call_soon_threadsafe。
            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None
            if running_loop is loop:
                queue.put_nowait(("emitted", event))
            else:
                loop.call_soon_threadsafe(queue.put_nowait, ("emitted", event))

    emitter_token = set_event_sink(_QueueEventSink())
    pending_token = set_pending_action_collector()
    latest_state: dict = {}
    aggregated_answer: list[str] = []
    used_tools: list[str] = []
    has_streamed = False
    has_error = False
    request_started = time.perf_counter()
    first_answer_at: float | None = None
    success = False
    error_type: str | None = None

    async def produce():
        nonlocal latest_state
        try:
            async for mode, chunk in config.workflow.astream(state, stream_mode=["values"]):
                if mode == "values" and isinstance(chunk, dict):
                    latest_state = chunk
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Agent 工作流执行异常")  # 记录真实异常,避免被 map_exception 吞掉
            await queue.put(("error", exc))
        finally:
            await queue.put(("done", None))

    producer = asyncio.create_task(produce())
    try:
        while True:
            kind, payload = await queue.get()
            if kind == "done":
                break
            if kind == "error":
                has_error = True
                error_type = classify_error(payload)
                text = config.map_exception(payload) if config.map_exception else "处理请求时出错，请重试"
                yield AgentEvent(type=AgentEventType.ANSWER, text=text)
                continue
            event = _build_agent_event(payload)
            if event is None:
                continue
            if event.type is AgentEventType.ANSWER and event.text:
                if first_answer_at is None:
                    first_answer_at = time.perf_counter()
                has_streamed = True
                aggregated_answer.append(event.text)
            if (
                event.type is AgentEventType.FUNCTION_CALL
                and event.state == "start"
                and event.name
                and event.name not in used_tools
            ):
                used_tools.append(event.name)
            yield event

        if not has_streamed and not has_error and config.extract_final_content:
            text = config.extract_final_content(latest_state)
            if text:
                if first_answer_at is None:
                    first_answer_at = time.perf_counter()
                yield AgentEvent(type=AgentEventType.ANSWER, text=text)

        if config.on_answer_completed is not None:
            try:
                await config.on_answer_completed("".join(aggregated_answer), used_tools)
            except Exception:
                pass  # 落库失败不阻塞流结束

        if config.on_pending_action is not None:
            try:
                event = get_pending_action_event()
                if event is not None:
                    await config.on_pending_action(event)
            except Exception:
                pass  # 待确认动作持久化失败不阻塞流结束
        yield AgentEvent(type=AgentEventType.END)
        success = not has_error
    except asyncio.CancelledError:
        error_type = "CLIENT_DISCONNECTED"
        success = False
        raise
    except Exception as exc:
        error_type = classify_error(exc)
        success = False
        raise
    finally:
        first_token_ms = None
        if first_answer_at is not None:
            first_token_ms = round((first_answer_at - request_started) * 1000)
        log_event(
            "agent.request.completed",
            sessionHash=get_session_hash(),
            userHash=get_user_hash(),
            routeTarget=_extract_route_target(latest_state),
            durationMs=elapsed_ms(request_started),
            firstTokenMs=first_token_ms,
            toolCount=len(used_tools),
            success=success,
            errorType=error_type,
        )
        reset_event_sink(emitter_token)
        reset_pending_action_collector(pending_token)
        if not producer.done():
            producer.cancel()
