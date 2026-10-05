from datetime import datetime, timedelta, timezone
from typing import Annotated

import secrets

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.agent.middleware import tool_call_status
from app.agent.ports import BusinessGateway
from app.chat.pending_events import emit_pending_action_clear, emit_pending_action_set
from app.chat.user import UserInfo
from app.chat.pending_action import WishlistPendingAction, WishlistPendingItem
from app.agent.client.actions.collection_state import check_collection_state
from app.agent.client.actions.collection_state import require_user as _require_user
from app.agent.client.actions.write_guard import require_confirmed_write

_MAX_WISHLIST_PREVIEW_ITEMS = 10


def _pending_action_from_items(items: list[dict], user: UserInfo) -> WishlistPendingAction:
    return WishlistPendingAction(
        type="ADD_TO_WISHLIST",
        user_id=user.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        items=[WishlistPendingItem(subject_id=i["subjectId"], subject_name=i.get("subjectName", "")) for i in items],
        action_id=secrets.token_hex(8),
    )


def build_wishlist_preview(subjects: list[dict], user: UserInfo, business: BusinessGateway) -> dict:
    """既有加入想看预览核心：去重、跳过已收藏、生成待确认动作，不写入。

    多个入口复用（推荐结果批量加入、单标题解析后的唯一候选），保证预览→确认
    的写入边界只有一处实现。返回 ``{"pendingItems": [...], "skippedItems": [...]}``；
    只有存在待确认条目时才发出 SET 待确认动作。
    """
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
        state = check_collection_state(sid, user, business)
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


def build_wishlist_tools(business: BusinessGateway):
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
        return build_wishlist_preview(subjects, user, business)

    @tool
    @tool_call_status(display_name="确认加入想看")
    def execute_add_to_wishlist(
            pending: Annotated[WishlistPendingAction | None, InjectedState("pending_action")],
            user: Annotated[UserInfo | None, InjectedState("user")] = None,
            write_confirmed: Annotated[bool, InjectedState("write_confirmed")] = False) -> dict:
        """确认把预览过的番剧加入「想看」。只处理系统待确认动作中的条目，不接受模型自造列表；
        仅当用户在当前回合明确确认（服务端 write_confirmed 标志）时才写入，否则拒绝；
        每项由 Business 幂等接口保证不覆盖已有收藏。"""
        gate = require_confirmed_write(
            user=user, pending=pending, expected_type="ADD_TO_WISHLIST",
            write_confirmed=write_confirmed,
        )
        if gate is not None:
            return gate
        succeeded, skipped, failed = [], [], []
        infra_error = False
        for item in pending.items:
            sid = item.subject_id
            name = item.subject_name
            result = business.request("POST", f"/api/client/collections/{sid}/wishlist", token=user.token)
            if isinstance(result, dict) and result.get("error"):
                if result.get("code") is None:
                    infra_error = True  # 基础设施错误：写入结果不确定，保留待确认动作供重试
                failed.append({"subjectId": sid, "subjectName": name,
                               "reason": result.get("message", "加入失败")})
            elif isinstance(result, dict) and result.get("state") == "ALREADY_COLLECTED":
                skipped.append({"subjectId": sid, "subjectName": name,
                                "existingType": result.get("existingType")})
            elif isinstance(result, dict) and result.get("state") == "ADDED":
                succeeded.append({"subjectId": sid, "subjectName": name})
            else:
                failed.append({"subjectId": sid, "subjectName": name,
                               "reason": "未返回预期的 ADDED 状态"})

        if not infra_error:
            emit_pending_action_clear()
        return {"succeeded": succeeded, "skipped": skipped, "failed": failed}

    @tool
    @tool_call_status(display_name="取消加入想看")
    def cancel_add_to_wishlist() -> dict:
        """取消当前待确认的加入想看动作，只清理本地待确认状态，不修改后端数据。"""
        emit_pending_action_clear()
        return {"cancelled": True}

    return [
        preview_add_to_wishlist,
        execute_add_to_wishlist,
        cancel_add_to_wishlist,
    ]
