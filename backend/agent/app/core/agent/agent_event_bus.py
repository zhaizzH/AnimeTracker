from contextvars import ContextVar, Token
from typing import Any, Callable

EventEmitter = Callable[[dict[str, Any]], None]

_status_emitter: ContextVar[EventEmitter | None] = ContextVar("sse_event_emitter", default=None)


def set_status_emitter(emitter: EventEmitter) -> Token:
    return _status_emitter.set(emitter)


def reset_status_emitter(token: Token) -> None:
    _status_emitter.reset(token)


def _emit(payload: dict[str, Any]) -> None:
    emitter = _status_emitter.get()
    if emitter is None:
        return
    try:
        emitter(payload)
    except Exception:
        pass  # 发射失败不中断主流程


def emit_answer_delta(text: str) -> None:
    _emit({"type": "answer", "content": {"text": text}})


def emit_thinking_delta(text: str) -> None:
    _emit({"type": "thinking", "content": {"text": text}})


def emit_function_call(*, node, state, message=None, result=None, name=None, arguments=None, parent_node=None) -> None:
    content = {"node": node, "state": state}
    for k, v in (("parent_node", parent_node), ("message", message), ("result", result), ("name", name), ("arguments", arguments)):
        if v is not None:
            content[k] = v
    _emit({"type": "function_call", "content": content})


def emit_status(*, node, state, message=None, result=None) -> None:
    content = {"node": node, "state": state}
    if message:
        content["message"] = message
    if result:
        content["result"] = result
    _emit({"type": "status", "content": content})
