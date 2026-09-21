"""按标题设置收藏类型（想看/看过/在看/搁置/抛弃）的预览→确认→写入链路。

复用 09-16 的确定性标题解析（`resolve_candidates` / `finalize_resolution`）与共享收藏状态检查，
写入经 Business `POST /api/client/collections/{id}/save`。安全边界：
- 目标类型只能来自受控枚举 1..5，由用户措辞映射；模型不能提交任意 subjectId 或越界类型。
- 已收藏按用户意图处理，但任何类型变更都必须在预览中可见（ADD/CHANGE），经明确确认才写入，绝不静默覆盖。
- 已在目标类型且无变化视为 NOOP：不发待确认动作、不写入（避免 /save 409）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

import secrets

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.agent.client.actions.collection_state import check_collection_state, require_user
from app.agent.client.actions.subject_resolution import finalize_resolution, resolve_candidates
from app.agent.client.actions.write_guard import require_confirmed_write
from app.agent.middleware import tool_call_status
from app.agent.ports import BusinessGateway
from app.chat.pending_action import SetCollectionTypePendingAction
from app.chat.pending_events import emit_pending_action_clear, emit_pending_action_set
from app.chat.user import UserInfo
from app.rag.use_case import RetrieveSubjectsUseCase

_SET_COLLECTION_TTL_SECONDS = 600

# 收藏类型枚举，与 Business CollectionUpdateDTO 及前端映射一致：1想看 2看过 3在看 4搁置 5抛弃
CollectionType = Literal[1, 2, 3, 4, 5]

_TYPE_LABELS = {1: "想看", 2: "看过", 3: "在看", 4: "搁置", 5: "抛弃"}


def collection_type_label(collection_type: int | None) -> str:
    return _TYPE_LABELS.get(collection_type, "未知")


def build_collection_type_preview(
    subject_id: int,
    subject_name: str,
    target_type: int,
    user: UserInfo,
    business: BusinessGateway,
) -> dict:
    """生成设置收藏类型预览：ADD（未收藏）/ NOOP（已在目标类型）/ CHANGE（改类型）。

    仅 ADD/CHANGE 发出 SET_COLLECTION_TYPE 待确认动作；NOOP 不发也不写入。
    """
    state = check_collection_state(subject_id, user, business)
    if state.get("error"):
        return {"error": True, "code": state["data"].get("code"),
                "message": state["data"].get("message", "检查收藏状态失败")}
    current = state["type"] if state["collected"] else None
    if state["collected"] and current == target_type:
        return {
            "action": "NOOP",
            "subjectId": subject_id,
            "subjectName": subject_name,
            "currentType": current,
            "targetType": target_type,
            "message": f"《{subject_name}》已在「{collection_type_label(target_type)}」中，无需重复设置",
        }
    action = "CHANGE" if state["collected"] else "ADD"
    emit_pending_action_set(SetCollectionTypePendingAction(
        type="SET_COLLECTION_TYPE",
        user_id=user.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=_SET_COLLECTION_TTL_SECONDS),
        subject_id=subject_id,
        subject_name=subject_name,
        target_type=target_type,
        current_type=current,
        action=action,
        action_id=secrets.token_hex(8),
    ))
    result = {
        "action": action,
        "subjectId": subject_id,
        "subjectName": subject_name,
        "currentType": current,
        "targetType": target_type,
    }
    if action == "CHANGE":
        result["message"] = f"将把《{subject_name}》从「{collection_type_label(current)}」改为「{collection_type_label(target_type)}」"
    else:
        result["message"] = f"将把《{subject_name}》加入「{collection_type_label(target_type)}」"
    return result


def build_collection_type_tools(business: BusinessGateway, retrieval: RetrieveSubjectsUseCase):
    @tool
    @tool_call_status(display_name="设置收藏类型")
    def set_subject_collection(
            collection_type: CollectionType,
            title: str = "",
            subject_id: int | None = None,
            user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
        """按单个番剧标题把它设置为指定收藏类型并预览（不写入）。

        collection_type：1=想看 2=看过 3=在看(追番) 4=搁置 5=抛弃，必须由用户措辞映射，不确定时先澄清；
        title：原始标题（勿改写为「第2季」等语义变体）；用户明确给出番剧ID时传 subject_id。
        返回 preview.action=ADD/CHANGE 表示进入待确认预览，仍需用户明确确认后才写入；
        NOOP 表示已在目标类型无需写入；needsSelection 时必须展示候选并等待用户选择。
        注意：普通「加入想看」应使用 resolve_subject_by_title（幂等不覆盖），本工具用于显式设置/变更类型。"""
        err = require_user(user)
        if err:
            return err
        # 新的写入解析取代任何陈旧的待确认/待选择状态（只清理本地状态，不改业务数据）。
        emit_pending_action_clear()
        outcome = resolve_candidates(title, subject_id, user, business, retrieval)
        return finalize_resolution(
            outcome,
            user,
            preview_one=lambda only, u: build_collection_type_preview(
                only["subjectId"], only["name"], collection_type, u, business
            ),
            collection_type=collection_type,
        )

    @tool
    @tool_call_status(display_name="确认设置收藏类型")
    def execute_set_collection_type(
            pending: Annotated[SetCollectionTypePendingAction | None, InjectedState("pending_action")] = None,
            user: Annotated[UserInfo | None, InjectedState("user")] = None,
            write_confirmed: Annotated[bool, InjectedState("write_confirmed")] = False) -> dict:
        """确认把预览过的番剧设置为目标收藏类型。只处理系统注入的待确认动作，不接受模型自造参数；
        仅当用户在当前回合明确确认（服务端 write_confirmed 标志）时才写入，否则拒绝。
        写入由 Business /save 完成，已收藏且无变化会返回 409 并如实告知。"""
        gate = require_confirmed_write(
            user=user, pending=pending, expected_type="SET_COLLECTION_TYPE",
            write_confirmed=write_confirmed,
        )
        if gate is not None:
            return gate
        result = business.save_collection(
            pending.subject_id, collection_type=pending.target_type, token=user.token
        )
        if isinstance(result, dict) and result.get("error"):
            code = result.get("code")
            if code is None:
                # 基础设施错误：写入结果不确定，保留待确认动作供重试，不宣称成功
                return {"error": True, "retryable": True,
                        "message": result.get("message", "写入失败，请稍后再试")}
            if code == 409:
                emit_pending_action_clear()
                return {"state": "ALREADY_COLLECTED", "subjectId": pending.subject_id,
                        "subjectName": pending.subject_name, "targetType": pending.target_type,
                        "message": f"《{pending.subject_name}》已在「{collection_type_label(pending.target_type)}」中"}
            # 404（条目不存在）等确定性失败：清理状态并如实报错
            emit_pending_action_clear()
            return {"error": True, "code": code, "message": result.get("message", "写入失败")}
        emit_pending_action_clear()
        return {"state": "SAVED", "action": pending.action, "subjectId": pending.subject_id,
                "subjectName": pending.subject_name, "targetType": pending.target_type,
                "currentType": pending.current_type}

    @tool
    @tool_call_status(display_name="取消设置收藏类型")
    def cancel_set_collection_type() -> dict:
        """取消当前待确认的收藏类型设置，只清理本地待确认状态，不修改后端数据。"""
        emit_pending_action_clear()
        return {"cancelled": True}

    return [set_subject_collection, execute_set_collection_type, cancel_set_collection_type]
