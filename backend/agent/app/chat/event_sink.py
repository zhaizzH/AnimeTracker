from contextvars import ContextVar, Token
from typing import Protocol

from app.chat.events import AgentEvent, AgentEventType


class AgentEventSink(Protocol):
    def emit(self, event: AgentEvent) -> None: ...


_sink: ContextVar[AgentEventSink | None] = ContextVar("agent_event_sink", default=None)


def set_event_sink(sink: AgentEventSink) -> Token:
    return _sink.set(sink)


def reset_event_sink(token: Token) -> None:
    _sink.reset(token)


def emit_event(event: AgentEvent) -> None:
    sink = _sink.get()
    if sink is None:
        return
    try:
        sink.emit(event)
    except Exception:
        pass  # 发射失败不中断主流程


def emit_answer_delta(text: str) -> None:
    emit_event(AgentEvent(type=AgentEventType.ANSWER, text=text))


def emit_thinking_delta(text: str) -> None:
    emit_event(AgentEvent(type=AgentEventType.THINKING, text=text))


def emit_ui_action(*, action: str, params: dict, path: str, label: str) -> None:
    emit_event(AgentEvent(
        type=AgentEventType.UI_ACTION,
        # meta 必须非空：serialize 侧 exclude_none 会剔除空 meta
        meta={"action": action, "params": params, "path": path, "label": label},
    ))

def emit_function_call(*, node, state, message=None, result=None, name=None, arguments=None, parent_node=None) -> None:
    emit_event(AgentEvent(
        type=AgentEventType.FUNCTION_CALL,
        node=node,
        state=state,
        message=message,
        result=result,
        name=name,
        arguments=arguments,
        parent_node=parent_node,
    ))
