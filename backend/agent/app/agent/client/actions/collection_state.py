"""共享的收藏状态检查：想看链路与设类型链路复用同一权威读取语义。"""

from __future__ import annotations

from app.agent.ports import BusinessGateway
from app.chat.user import UserInfo


def require_user(user: UserInfo | None) -> dict | None:
    """注入用户缺失时返回统一错误；否则返回 None。"""
    if user is None:
        return {"error": True, "message": "用户上下文不可用"}
    return None


def check_collection_state(subject_id: int, user: UserInfo, business: BusinessGateway) -> dict:
    """检查某条目的当前收藏状态。

    - 404 视为未收藏（可加入/可设置）；其它 4xx/5xx 为真实错误。
    - 适配器对空成功信封返回 None：只有真实收藏对象才算已收藏。
    返回 ``{"collected": bool, "type": int | None}``，或 ``{"error": True, "data": <错误响应>}``。
    """
    data = business.request("GET", f"/api/client/collections/{subject_id}", token=user.token)
    if isinstance(data, dict) and data.get("error"):
        if data.get("code") == 404:
            return {"collected": False, "type": None}
        return {"error": True, "data": data}
    collected = isinstance(data, dict)
    return {"collected": collected, "type": data.get("type") if collected else None}
