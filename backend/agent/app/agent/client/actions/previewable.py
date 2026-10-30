"""PreviewableAction 抽象：「预览 → 确认 → 取消」三件套骨架。

三条写链路（wishlist / collection_type / collection_progress）共用同一骨架：
`require_confirmed_write` gate → 调 Business 写入 → 按业务结果 emit Clear/Keep/Replace。

差异点通过子类钩子表达：
- ``pending_type``：声明对应的 ``PendingAction.type`` 字面量
- ``do_execute``：调 Business 接口，返回业务自己的中间表示
- ``classify_result``：把中间表示映射到「PendingAction 清理动作 + 返回给模型的 dict」

三层同步架构见 ``app/chat/pending_action.py`` 模块 docstring；写入硬门禁见
``app/agent/client/actions/write_guard.py``。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Generic, TypeVar

from app.agent.client.actions.turn_state import mark_pending_resolved
from app.agent.client.actions.write_guard import require_confirmed_write
from app.chat.pending_events import (
    emit_pending_action_clear,
    emit_pending_action_replace,
)
from app.chat.user import UserInfo


@dataclass(frozen=True)
class Clear:
    """写入已确定（成功或确定性失败），清理待确认动作。"""


@dataclass(frozen=True)
class Keep:
    """基础设施错误等写入结果不确定，保留待确认动作供重试。"""


@dataclass(frozen=True)
class Replace:
    """预览已变化（如 Business 端数据更新），用新动作替换旧的。"""

    new_pending: Any


ClearAction = Clear | Keep | Replace


P = TypeVar("P")


class PreviewableAction(ABC, Generic[P]):
    """「预览 → 确认 → 取消」三件套骨架。

    子类只需声明 ``pending_type`` 并实现 ``do_execute`` / ``classify_result``；
    cancel 与 execute 的 gate/emit 时序由基类统一保证。
    """

    pending_type: ClassVar[str]

    def cancel(self) -> dict:
        """取消当前待确认动作，只清理本地状态，不修改后端数据。"""
        emit_pending_action_clear()
        # 取消也是「本回合 pending 已结束」：门控据此放行后续导航（design D2/D3）
        mark_pending_resolved()
        return {"cancelled": True}

    def execute(
        self,
        *,
        pending: P | None,
        user: UserInfo | None,
        write_confirmed: bool,
    ) -> dict:
        """模板方法：gate → do_execute → classify_result → 按三态 emit。"""
        gate = require_confirmed_write(
            user=user,
            pending=pending,
            expected_type=self.pending_type,
            write_confirmed=write_confirmed,
        )
        if gate is not None:
            return gate
        result = self.do_execute(pending=pending, user=user)
        action, response = self.classify_result(result=result, pending=pending, user=user)
        if isinstance(action, Clear):
            emit_pending_action_clear()
            # 写入已定（成功或确定性失败）：pending 结束，本回合导航门控放行。
            # Keep 不打标——基础设施错误时 pending 还在，可重试，门控应继续拦。
            mark_pending_resolved()
        elif isinstance(action, Replace):
            emit_pending_action_replace(action.new_pending)
        return response

    @abstractmethod
    def do_execute(self, *, pending: P, user: UserInfo) -> Any:
        """调 Business 写入接口，返回业务自己的中间表示（由 classify_result 配对解释）。"""

    @abstractmethod
    def classify_result(self, *, result: Any, pending: P, user: UserInfo) -> tuple[ClearAction, dict]:
        """把 do_execute 的中间表示映射到「清理动作 + 返回给模型的 dict」。

        user 一并传入是因为 collection_progress 在 Replace 分支需要用 user 构造新
        PendingAction；wishlist / collection_type 直接忽略。
        """
