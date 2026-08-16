from datetime import datetime, timedelta, timezone
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.agent.http import call_api
from app.core.middleware import tool_call_status
from app.core.pending_action import emit_pending_action_clear, emit_pending_action_set
from app.schemas.auth import UserInfo
from app.schemas.pending_action import WishlistPendingAction, WishlistPendingItem

_MAX_WISHLIST_PREVIEW_ITEMS = 10


def _require_user(user: UserInfo | None) -> dict | None:
    if user is None:
        return {"error": True, "message": "用户上下文不可用"}
    return None


def _check_collection_state(subject_id: int, user: UserInfo) -> dict:
    """检查收藏状态；404 视为未收藏（可加入），其他 4xx/5xx 为真实错误。"""
    data = call_api("GET", f"/api/client/collections/{subject_id}", token=user.token)
    if isinstance(data, dict) and data.get("error"):
        if data.get("code") == 404:
            return {"collected": False, "type": None}
        return {"error": True, "data": data}
    return {"collected": data is not None, "type": (data or {}).get("type")}


def _pending_action_from_items(items: list[dict], user: UserInfo) -> WishlistPendingAction:
    return WishlistPendingAction(
        type="ADD_TO_WISHLIST",
        user_id=user.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        items=[WishlistPendingItem(subject_id=i["subjectId"], subject_name=i.get("subjectName", "")) for i in items],
    )


@tool
@tool_call_status(display_name="预览加入想看")
def preview_add_to_wishlist(
        subjects: list[dict],
        user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """预览把推荐的番剧加入「想看」：去重并筛选尚未收藏的条目，不写入。
    subjects: [{"subjectId": 番剧ID, "subjectName": 番剧名}]，subjectId 必须来自推荐或搜索结果。"""
    err = _require_user(user)
    if err:
        return err
    seen = set()
    deduped = []
    for item in subjects:
        sid = (item or {}).get("subjectId")
        if sid is None or sid in seen:
            continue
        seen.add(sid)
        deduped.append(item)
        if len(deduped) >= _MAX_WISHLIST_PREVIEW_ITEMS:
            break

    pending_items = []
    skipped_items = []
    for item in deduped:
        sid = item["subjectId"]
        state = _check_collection_state(sid, user)
        if state.get("error"):
            return {"error": True, "code": state["data"].get("code"),
                    "message": state["data"].get("message", "检查收藏状态失败")}
        if state["collected"]:
            skipped_items.append({"subjectId": sid, "subjectName": item.get("subjectName", ""),
                                  "existingType": state["type"]})
        else:
            pending_items.append({"subjectId": sid, "subjectName": item.get("subjectName", "")})

    if pending_items:
        emit_pending_action_set(_pending_action_from_items(pending_items, user))
    return {"pendingItems": pending_items, "skippedItems": skipped_items}


@tool
@tool_call_status(display_name="确认加入想看")
def execute_add_to_wishlist(
        pending: Annotated[WishlistPendingAction | None, InjectedState("pending_action")],
        user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """确认把预览过的番剧加入「想看」。只处理系统待确认动作中的条目，不接受模型自造列表；
    每项由 Business 幂等接口保证不覆盖已有收藏。"""
    err = _require_user(user)
    if err:
        return err
    if pending is None or pending.type != "ADD_TO_WISHLIST":
        return {"error": True, "message": "没有待确认的加入想看动作"}
    succeeded, skipped, failed = [], [], []
    infra_error = False
    for item in pending.items:
        sid = item.subject_id
        name = item.subject_name
        result = call_api("POST", f"/api/client/collections/{sid}/wishlist", token=user.token)
        if isinstance(result, dict) and result.get("error"):
            if result.get("code") is None:
                infra_error = True  # 基础设施错误：写入结果不确定，保留待确认动作供重试
            failed.append({"subjectId": sid, "subjectName": name,
                           "reason": result.get("message", "加入失败")})
        elif isinstance(result, dict) and result.get("state") == "ALREADY_COLLECTED":
            skipped.append({"subjectId": sid, "subjectName": name,
                            "existingType": result.get("existingType")})
        else:
            succeeded.append({"subjectId": sid, "subjectName": name})

    if not infra_error:
        emit_pending_action_clear()
    return {"succeeded": succeeded, "skipped": skipped, "failed": failed}


@tool
@tool_call_status(display_name="取消加入想看")
def cancel_add_to_wishlist() -> dict:
    """取消当前待确认的加入想看动作，只清理本地待确认状态，不修改后端数据。"""
    emit_pending_action_clear()
    return {"cancelled": True}


wishlist_tools = [
    preview_add_to_wishlist,
    execute_add_to_wishlist,
    cancel_add_to_wishlist,
]
