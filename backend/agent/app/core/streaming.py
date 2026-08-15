import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from fastapi.responses import StreamingResponse

from app.core.event_bus import reset_status_emitter, set_status_emitter
from app.core.pending_action import (
    PendingActionEvent,
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.schemas.sse_response import AssistantResponse, Content, MessageType, serialize_sse

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    workflow: Any
    build_initial_state: Callable[[], dict]
    extract_final_content: Callable[[dict], str] | None = None
    map_exception: Callable[[Exception], str] | None = None
    on_answer_completed: Callable[[str, list[str]], Awaitable[None] | None] | None = None
    on_pending_action: Callable[[PendingActionEvent], Awaitable[None] | None] | None = None


def _build_emitted_response(payload: dict) -> AssistantResponse | None:
    if not isinstance(payload, dict):
        return None
    content = payload.get("content")
    if not isinstance(content, dict):
        return None
    try:
        message_type = MessageType(payload.get("type"))
    except ValueError:
        message_type = MessageType.STATUS
    node = content.get("node")
    if message_type == MessageType.FUNCTION_CALL:
        node = None  # 不暴露内部工具节点标识
    return AssistantResponse(
        content=Content(**{k: v for k, v in content.items() if v is not None}),
        type=message_type,
    )


def create_streaming_response(config: StreamConfig) -> StreamingResponse:
    async def event_stream():
        state = config.build_initial_state()
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def emitter(payload: dict) -> None:
            # 同一事件循环内直接入队(否则 call_soon_threadsafe 的延迟可能让
            # 同步 "done" 先入队而丢掉已发射事件);跨线程(节点经 _run_async 线程池)
            # 时仍走 call_soon_threadsafe。
            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None
            if running_loop is loop:
                queue.put_nowait(("emitted", payload))
            else:
                loop.call_soon_threadsafe(queue.put_nowait, ("emitted", payload))

        emitter_token = set_status_emitter(emitter)
        pending_token = set_pending_action_collector()
        latest_state: dict = {}
        aggregated_answer: list[str] = []
        used_tools: list[str] = []
        has_streamed = False
        has_error = False

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
                    text = config.map_exception(payload) if config.map_exception else "处理请求时出错，请重试"
                    yield serialize_sse(AssistantResponse(type=MessageType.ANSWER, content=Content(text=text)))
                    continue
                response = _build_emitted_response(payload)
                if response is None:
                    continue
                if response.type == MessageType.ANSWER and response.content.text:
                    has_streamed = True
                    aggregated_answer.append(response.content.text)
                if (
                    response.type == MessageType.FUNCTION_CALL
                    and response.content.state == "start"
                    and response.content.name
                    and response.content.name not in used_tools
                ):
                    used_tools.append(response.content.name)
                yield serialize_sse(response)

            if not has_streamed and not has_error and config.extract_final_content:
                text = config.extract_final_content(latest_state)
                if text:
                    yield serialize_sse(AssistantResponse(type=MessageType.ANSWER, content=Content(text=text)))

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
            yield serialize_sse(AssistantResponse(content=Content(), is_end=True))
        finally:
            reset_status_emitter(emitter_token)
            reset_pending_action_collector(pending_token)
            if not producer.done():
                producer.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
