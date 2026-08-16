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
from app.schemas.auth import UserInfo
from app.schemas.pending_action import CollectionProgressPendingAction


def _require_user(user: UserInfo | None) -> dict | None:
    if user is None:
        return {"error": True, "message": "用户上下文不可用"}
    return None


def _preview_data_to_pending_action(data: dict, user: UserInfo) -> CollectionProgressPendingAction:
    return CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id=data["previewId"],
        user_id=user.user_id,
        expires_at=data["expiresAt"],
        items=data.get("items", []),
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
        if data.get("code") == 404 or (
                data.get("code") == 409 and "重新生成" in data.get("message", "")):
            emit_pending_action_clear()
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


collection_progress_tools = [
    preview_weekly_collection_progress,
    execute_weekly_collection_progress,
    cancel_weekly_collection_progress,
]
