"""写入硬确认守卫：三条写链路（wishlist / progress / collection_type）统一复用。

安全不变量：没有服务端设置的“当前回合明确确认”标志（write_confirmed），任何写入执行工具都不得写入，
无论模型是否调用。校验顺序：用户 → 待确认动作存在且类型匹配 → 用户绑定 → 未过期 → 明确确认。
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.chat.user import UserInfo


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= now


def require_confirmed_write(
    *,
    user: UserInfo | None,
    pending,
    expected_type: str,
    write_confirmed: bool,
) -> dict | None:
    """写入前的统一硬门禁；通过返回 None，否则返回可读错误 dict（调用方直接返回，不写入）。"""
    if user is None:
        return {"error": True, "message": "用户上下文不可用"}
    if pending is None or getattr(pending, "type", None) != expected_type:
        return {"error": True, "message": "没有待确认的动作"}
    if getattr(pending, "user_id", None) != user.user_id:
        return {"error": True, "message": "待确认动作不属于当前用户"}
    if _is_expired(getattr(pending, "expires_at", None)):
        return {"error": True, "message": "待确认动作已过期，请重新发起"}
    if not write_confirmed:
        # 关键硬门禁：非明确确认回合，即使模型调用 execute 也拒绝写入
        return {"error": True, "message": "需要用户明确确认后才能执行写入"}
    return None
