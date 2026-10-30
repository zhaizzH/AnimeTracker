"""单次图执行内的共享可变事实（turn-bag），供跨工具传递「本回合发生了什么」。

与 ``pending_events`` 的 collector 同为 ContextVar 承载的流内状态，但用途不同：
collector 是「待持久化的意图」（流结束写 Redis），本模块是「已发生的事实」，不落 Redis。

存在理由（design D1）：``state["pending_action"]`` 是回合开始时的 Redis 快照，写成功/取消后
不会更新。判断「写入是否还没结束」只能读本回合实时可变的通道，否则会在「写成功、正要导航」
那一刻把唯一该放行的导航拦死。

Token 纪律同 collector：Token 绑定创建它的 Context，必须由创建者 set/reset
（见 ``app/chat/runs.py::ChatRunManager._drive``）。
"""

from contextvars import ContextVar, Token
from dataclasses import dataclass

@dataclass
class TurnState:
    """单次图执行内的共享可变事实。

    ``pending_resolved``：本回合的待确认动作已结束（写入成功 / 用户取消 / 确定性失败）。
    基础设施错误（``Keep``）不打标——pending 还在，可重试，门控应继续拦。
    """

    pending_resolved: bool = False

_turn_state: ContextVar[TurnState | None] = ContextVar("turn_state", default=None)

def set_turn_state() -> Token:
    return _turn_state.set(TurnState())

def reset_turn_state(token: Token) -> None:
    _turn_state.reset(token)

def get_turn_state() -> TurnState | None:
    """当前回合事实；无回合（工厂组装期、直接单测工具）返回 None。"""
    return _turn_state.get()

def mark_pending_resolved() -> None:
    """打标「本回合 pending 已结束」；无回合时无操作。"""
    turn = _turn_state.get()
    if turn is not None:
        turn.pending_resolved = True
