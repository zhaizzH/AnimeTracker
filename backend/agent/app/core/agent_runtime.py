import asyncio
import contextvars
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable

from langchain_core.messages import HumanMessage


def _run_async(coro: Any) -> Any:
    """在同步上下文安全执行异步协程;保留当前 contextvars(事件总线 emitter)。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        current_context = contextvars.copy_context()
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(current_context.run, asyncio.run, coro).result()
    return asyncio.run(coro)


def extract_text(chunk: Any) -> str:
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
        return "".join(parts)
    return ""


def _normalize_history_messages(history_messages: list[Any] | str | None) -> list[Any]:
    if isinstance(history_messages, list):
        return list(history_messages)
    if history_messages is None:
        return []
    return [HumanMessage(content=str(history_messages))]


def _extract_reasoning_content_from_chunk(chunk: Any) -> str:
    parts: list[str] = []
    for raw in (
        getattr(chunk, "reasoning_content", None),
        (getattr(chunk, "additional_kwargs", None) or {}).get("reasoning_content"),
    ):
        if isinstance(raw, str) and raw.strip() and raw.strip() not in parts:
            parts.append(raw.strip())
    # Anthropic thinking 块(langchain-anthropic 将其并入 content 列表)
    content = getattr(chunk, "content", None)
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "thinking":
                thinking = str(item.get("thinking") or "").strip()
                if thinking and thinking not in parts:
                    parts.append(thinking)
    return "".join(parts)


@dataclass(frozen=True)
class _AgentInvokeResult:
    payload: Any
    messages: list[Any]
    content: str
    raw_content: Any


def agent_invoke(agent_instance: Any, history_messages: list[Any] | str) -> _AgentInvokeResult:
    payload = {"messages": _normalize_history_messages(history_messages)}
    raw_result = _run_async(agent_instance.ainvoke(payload))

    messages = list(raw_result.get("messages") or []) if isinstance(raw_result, dict) else []
    content = ""
    raw_content = None
    for message in reversed(messages):
        if str(getattr(message, "type", "") or "").lower() != "ai":
            continue
        raw_content = getattr(message, "content", None)
        content = extract_text(message).strip()
        break
    if not content and isinstance(raw_result, dict):
        content = str(raw_result.get("output") or raw_result.get("text") or "").strip()
        if raw_content is None:
            raw_content = raw_result.get("output") or raw_result.get("text")
    return _AgentInvokeResult(payload=raw_result, messages=messages, content=content, raw_content=raw_content)


def agent_stream(
    agent_instance: Any,
    history_messages: list[Any] | str,
    initial_state: dict | None = None,
    on_model_delta: Callable[[str], None] | None = None,
    on_thinking_delta: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    normalized = _normalize_history_messages(history_messages)
    input_payload = {**(initial_state or {}), "messages": normalized}

    async def _collect():
        answer_chunks: list[str] = []
        thinking_chunks: list[str] = []
        latest_state: dict[str, Any] = {}
        is_answering = False
        async for raw_event in agent_instance.astream(
            input_payload, stream_mode=["messages", "values"]
        ):
            if not (isinstance(raw_event, tuple) and len(raw_event) == 2):
                continue
            mode, payload = raw_event
            if mode == "values":
                if isinstance(payload, dict):
                    latest_state = payload
                continue
            if mode != "messages":
                continue
            if not (isinstance(payload, tuple) and len(payload) == 2):
                continue
            message_chunk, metadata = payload
            if str((metadata or {}).get("langgraph_node") or "") != "model":
                continue
            if not is_answering:
                thinking = _extract_reasoning_content_from_chunk(message_chunk)
                if thinking:
                    thinking_chunks.append(thinking)
                    if on_thinking_delta is not None:
                        on_thinking_delta(thinking)
            delta = extract_text(message_chunk)
            if delta:
                is_answering = True
                answer_chunks.append(delta)
                if on_model_delta is not None:
                    on_model_delta(delta)
        return answer_chunks, thinking_chunks, latest_state

    answer_chunks, thinking_chunks, latest_state = _run_async(_collect())
    return {
        "latest_state": latest_state,
        "streamed_text": "".join(answer_chunks),
        "streamed_thinking": "".join(thinking_chunks),
        "final_messages": list(latest_state.get("messages") or []),
    }
