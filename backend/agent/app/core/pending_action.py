from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Literal

from app.db.models import PendingAction


@dataclass
class PendingActionEvent:
    """工具在一次流中报告的待确认动作操作;流结束回调消费最后一条。"""

    operation: Literal["SET", "REPLACE", "CLEAR"]
    action: PendingAction | None = None


_pending_action_collector: ContextVar[list[PendingActionEvent] | None] = ContextVar(
    "pending_action_collector", default=None
)


def set_pending_action_collector() -> Token:
    return _pending_action_collector.set([])


def reset_pending_action_collector(token: Token) -> None:
    _pending_action_collector.reset(token)


def get_pending_action_event() -> PendingActionEvent | None:
    collector = _pending_action_collector.get()
    if not collector:
        return None
    return collector[-1]


def _emit(event: PendingActionEvent) -> None:
    collector = _pending_action_collector.get()
    if collector is None:
        return
    collector.append(event)


def emit_pending_action_set(action: PendingAction) -> None:
    _emit(PendingActionEvent(operation="SET", action=action))


def emit_pending_action_replace(action: PendingAction) -> None:
    _emit(PendingActionEvent(operation="REPLACE", action=action))


def emit_pending_action_clear() -> None:
    _emit(PendingActionEvent(operation="CLEAR"))
