from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.agent.http import call_api
from app.core.middleware import tool_call_status
from app.core.pending_action import (
    emit_pending_action_clear,
    emit_pending_action_replace,
    emit_pending_action_set,
)
from app.db.models import PendingAction
from app.schemas.auth import UserInfo


def _require_user(user: UserInfo | None) -> dict | None:
    if user is None:
        return {"error": True, "message": "用户上下文不可用"}
    return None


# 收藏类型映射（与后端 /api/client/collections 返回的 type 数字一致）
_TYPE_LABELS = {0: "全部", 1: "想看", 2: "看过", 3: "在看", 4: "搁置", 5: "抛弃"}


@tool
@tool_call_status(display_name="查看我的追番列表")
def get_my_collections(type: int = 0, page: int = 1, size: int = 20,
                       user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """查看当前用户的追番收藏列表。type: 0=全部 1=想看 2=看过 3=在看 4=搁置 5=抛弃；page: 页码；size: 每页数量"""
    err = _require_user(user)
    if err:
        return err
    params = {"page": page, "size": size}
    if type:
        params["type"] = type
    return call_api("GET", "/api/client/collections", params=params, token=user.token)


@tool
@tool_call_status(display_name="查看我的单部追番")
def get_my_collection(subject_id: int,
                      user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """查看当前用户对某部番的收藏状态与进度。subject_id: 番剧 ID"""
    err = _require_user(user)
    if err:
        return err
    return call_api("GET", f"/api/client/collections/{subject_id}", token=user.token)


@tool
@tool_call_status(display_name="查看我的收藏统计")
def get_my_stats(user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """查看当前用户各类收藏数量统计（1=想看 2=看过 3=在看 4=搁置 5=抛弃）"""
    err = _require_user(user)
    if err:
        return err
    return call_api("GET", "/api/client/collections/counts", token=user.token)


@tool
@tool_call_status(display_name="获取我的观看画像")
def get_my_watch_profile(cap: int = 50,
                         user: Annotated[UserInfo | None, InjectedState("user")] = None) -> list:
    """获取当前用户观看历史压缩画像，供个性化推荐。cap: 最多取前 N 部"""
    err = _require_user(user)
    if err:
        return err
    data = call_api("GET", "/api/client/collections", params={"page": 1, "size": cap}, token=user.token)
    if isinstance(data, dict) and data.get("error"):
        return data
    items = data.get("content") if isinstance(data, dict) else []
    return [_compact(item) for item in items][:cap]


def _compact(item: dict) -> dict:
    sub = item.get("subject") or {}
    return {
        "name": sub.get("name") or sub.get("nameCn") or "",
        "subject_type": sub.get("type"),
        "score": sub.get("score"),
        "eps": sub.get("eps"),
        "my_progress": item.get("epStatus"),
        "collection_type": item.get("type"),
        "collection_type_label": _TYPE_LABELS.get(item.get("type"), "未知"),
    }


user_collections_tools = [get_my_collections, get_my_collection, get_my_stats, get_my_watch_profile]


def _preview_data_to_pending_action(data: dict, user: UserInfo) -> PendingAction:
    return PendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id=data["previewId"],
        user_id=user.user_id,
        expires_at=data["expiresAt"],
        summary=data.get("items", []),
    )


@tool
@tool_call_status(display_name="预览本周追番进度")
def preview_weekly_collection_progress(
        user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """预览本周周一至昨日已播出的在看追番进度更新。调用后必须向用户展示明细并询问是否确认。"""
    err = _require_user(user)
    if err:
        return err
    data = call_api("POST", "/api/client/collections/progress-preview", token=user.token)
    if not data.get("error") and data.get("previewId"):
        emit_pending_action_set(_preview_data_to_pending_action(data, user))
    return data


@tool
@tool_call_status(display_name="确认本周追番进度更新")
def execute_weekly_collection_progress(
        preview_id: Annotated[str, InjectedState("pending_preview_id")],
        user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """确认并执行已预览的追番进度更新。preview_id 由系统从待确认动作注入，不要自行编造。"""
    err = _require_user(user)
    if err:
        return err
    data = call_api("POST", f"/api/client/collections/progress-preview/{preview_id}/execute", token=user.token)
    if data.get("error"):
        return data
    state = data.get("state")
    if state == "COMPLETED":
        emit_pending_action_clear()
    elif state == "PREVIEW_CHANGED":
        preview = data.get("preview") or {}
        if preview.get("previewId"):
            emit_pending_action_replace(_preview_data_to_pending_action(preview, user))
    return data


@tool
@tool_call_status(display_name="取消追番进度更新")
def cancel_weekly_collection_progress() -> dict:
    """取消当前待确认的追番进度更新，只清理本地待确认状态，不修改后端数据。"""
    emit_pending_action_clear()
    return {"cancelled": True}


user_collections_tools += [
    preview_weekly_collection_progress,
    execute_weekly_collection_progress,
    cancel_weekly_collection_progress,
]
