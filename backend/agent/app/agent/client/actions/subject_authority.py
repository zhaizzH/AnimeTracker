"""权威安全校验：调用 Business /batch 过滤候选，只保留 active=true / type=2 / nsfw=false 的动画条目。

基础设施错误（超时、5xx）返回 (None, error)，绝不伪装成「无候选」。
副作用：发起一次 Business HTTP 调用。
"""

from __future__ import annotations

from typing import Any

from app.agent.client.actions.candidate_matcher import (  # noqa: SLF001 — 跨模块复用私有辅助，避免重复实现
    _safe_subject_id,
    dedup_ids,
)
from app.agent.ports import BusinessGateway


def _batch_items(response: Any) -> list[Any]:
    if isinstance(response, dict):
        items = response.get("items")
        return items if isinstance(items, list) else []
    if isinstance(response, list):
        return response
    return []


def _is_safe_batch_item(item: Any) -> bool:
    """权威安全边界：只接受 active=true、type=2、nsfw=false 的动画条目。"""
    if not isinstance(item, dict):
        return False
    try:
        if int(item.get("type") or 0) != 2:
            return False
    except (TypeError, ValueError):
        return False
    return item.get("nsfw") is False and item.get("active") is True


def filter_authoritative(
    subject_ids: list[int],
    business: BusinessGateway,
    token: str | None,
) -> tuple[dict[int, dict] | None, dict | None]:
    """调用 ``/batch(excludeCollected=false)`` 并只保留安全候选。

    返回 ``(valid_by_id, error)``：基础设施错误时 ``valid_by_id`` 为 None 且 error 非空。
    """
    ids = dedup_ids(subject_ids)
    if not ids:
        return {}, None
    try:
        response = business.batch_subjects(ids, token=token, exclude_collected=False)
    except Exception:  # noqa: BLE001 - 网络/适配器异常按基础设施错误处理
        return None, {"error": True, "message": "校验番剧失败，请稍后再试"}
    if isinstance(response, dict) and response.get("error"):
        return None, {
            "error": True,
            "code": response.get("code"),
            "message": response.get("message", "校验番剧失败"),
        }
    details: dict[int, dict] = {}
    for item in _batch_items(response):
        subject_id = _safe_subject_id(item.get("id")) if isinstance(item, dict) else None
        if subject_id is not None and subject_id not in details:
            details[subject_id] = item
    valid: dict[int, dict] = {}
    for subject_id in ids:
        item = details.get(subject_id)
        if item is not None and _is_safe_batch_item(item):
            valid[subject_id] = item
    return valid, None


def _display_name(detail: dict | None, fallback: str = "") -> str:
    if isinstance(detail, dict):
        name = detail.get("nameCn") or detail.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return fallback or ""
