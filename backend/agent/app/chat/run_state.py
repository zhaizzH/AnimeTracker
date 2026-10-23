"""run 状态的持久化端口（design §2.2）。

进程内 ``ChatRunManager`` 是权威状态源；Redis 只是「跨重启可观测」的投影，
供懒加载收敛（D9）使用：读到 ``running`` 但内存里没有对应 run，说明上一个进程
已经死了，收敛为 ``failed``。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

RUN_STATE_TTL_SECONDS = 900


@dataclass(frozen=True)
class RunState:
    """run 的可持久化投影。不含事件流——重放只在本进程内可用。"""

    run_id: str
    session_id: str
    user_id: int
    status: str
    event_count: int = 0


@runtime_checkable
class RunStateStore(Protocol):
    async def save_run_state(self, state: RunState) -> None: ...
    async def get_run_state(self, run_id: str) -> RunState | None: ...
    async def save_session_run(self, session_id: str, run_id: str) -> None: ...
    async def get_session_run(self, session_id: str) -> str | None: ...
