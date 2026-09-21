"""播出状态推断的唯一实现；两处调用点必须复用本函数。

``retrieval._infer_air_status_name``（过滤）与 ``use_case._infer_air_status``
（对外输出）曾各存一份互相矛盾的规则：过滤侧把无权威状态的过去日期判为
``FINISHED``，输出侧判为 ``UNKNOWN``。单个首播日期不能证明作品已完结，
因此本模块把规则收敛为一份保守实现，禁止在消费方内联第二份判断。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def infer_air_status(air_date: Any, explicit_status: Any = None) -> str:
    """输出可信播出状态；单个首播日期不足以证明已完结。

    优先采用权威 ``airStatus``；无权威状态时按日期保守推断：未来日期 →
    ``UPCOMING``，过去或无法解析的日期 → ``UNKNOWN``。绝不返回 ``FINISHED``。
    """
    normalized = str(explicit_status or "").upper()
    if normalized in {"UPCOMING", "AIRING", "FINISHED"}:
        return normalized
    parsed = _parse_date(air_date)
    if parsed is None:
        return "UNKNOWN"
    today = datetime.today().date()
    if parsed > today:
        return "UPCOMING"
    return "UNKNOWN"


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except (TypeError, ValueError):
        return None
