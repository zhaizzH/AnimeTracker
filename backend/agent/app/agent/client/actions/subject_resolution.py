"""单标题「加入想看 / 设类型」的确定性解析入口。

输入标题或显式 ID，输出三种之一：错误 / 无匹配 / 唯一精确预览或 SUBJECT_RESOLUTION 待选择。
副作用：通过 ``emit_pending_action_set/clear`` 触发状态变更；自身不持久化。

职责拆分：
- 标题归一化 → ``title_normalizer.py``
- 候选匹配与选择 → ``candidate_matcher.py``
- Business /batch 权威校验 → ``subject_authority.py``
- 本文件只保留主流程编排与工具入口。

安全边界（与 design.md / spec 一致）：
- 用户显式给出 subjectId 时跳过名称搜索，但仍必须经过 ``/api/client/subjects/batch`` 权威校验。
- 只有标题时先调用 Business ``/api/client/subjects/search``；只有 Business 成功且候选为空时才回退 RAG。
- Business/RAG 的基础设施错误、超时、坏响应绝不伪装成「无结果」，也不触发 RAG 回退。
- 归一化只做安全字符处理，绝不做「第二季/第2季」等语义转换。
- 所有候选进入预览前都经过 ``/batch`` 过滤 ``active=true``、``type=2``、``nsfw=false``，且 ``excludeCollected=false``。
- 唯一精确候选复用既有 ``build_wishlist_preview``；多个或歧义候选保存 ``SUBJECT_RESOLUTION`` 等待用户选择，绝不自动预览。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.agent.client.actions.title_normalizer import normalize_title  # noqa: F401 — re-export 兼容
from app.agent.client.actions.candidate_matcher import (  # noqa: F401 — re-export 兼容
    dedup_ids,
    select_candidate,
    unique_exact_match_ids,
    _safe_subject_id,
)
from app.agent.client.actions.subject_authority import (  # noqa: F401 — re-export 兼容
    filter_authoritative,
    _display_name,
)
from app.agent.client.actions.wishlist import build_wishlist_preview
from app.agent.client.actions.collection_state import require_user as _require_user
from app.agent.client.actions.write_guard import is_expired as _is_expired
from app.agent.middleware import tool_call_status
from app.agent.ports import BusinessGateway
from app.chat.pending_action import (
    SubjectResolutionCandidate,
    SubjectResolutionPendingAction,
)
from app.chat.pending_events import emit_pending_action_clear, emit_pending_action_set
from app.chat.user import UserInfo
from app.rag.schemas import RetrievalQuery
from app.rag.use_case import RetrieveSubjectsUseCase

# 与既有待确认动作一致：复用 Agent Redis 键和 600 秒 TTL，不新增存储系统。
_RESOLUTION_TTL_SECONDS = 600
_MAX_RESOLUTION_CANDIDATES = 10
_SEARCH_SIZE = 15
_RAG_QUERY_MAX_LEN = 200


def _candidates_from_rows(
    rows: list[dict],
    id_key: str,
    source: str,
    match_type: str,
    only_ids: list[int] | None = None,
) -> list[dict]:
    wanted = set(only_ids) if only_ids is not None else None
    candidates: list[dict] = []
    seen: set[int] = set()
    for row in rows:
        subject_id = _safe_subject_id(row.get(id_key))
        if subject_id is None or subject_id in seen:
            continue
        if wanted is not None and subject_id not in wanted:
            continue
        seen.add(subject_id)
        candidates.append(
            {
                "subjectId": subject_id,
                "name": str(row.get("nameCn") or row.get("name") or row.get("title") or ""),
                "matchSource": source,
                "matchType": match_type,
            }
        )
    return candidates


def _business_lookup(title: str, user: UserInfo, business: BusinessGateway) -> dict:
    """Business 首查：唯一精确 → EXACT；非空无唯一精确 → 安全候选；成功空 → 触发 RAG 回退。"""
    try:
        response = business.search_subjects(title, token=user.token, size=_SEARCH_SIZE)
    except Exception:  # noqa: BLE001 - 基础设施错误不得伪装成无结果，也不回退 RAG
        return {"error": {"error": True, "message": "搜索番剧失败，请稍后再试"}}
    if isinstance(response, dict) and response.get("error"):
        return {
            "error": {
                "error": True,
                "code": response.get("code"),
                "message": response.get("message", "搜索番剧失败"),
            }
        }
    rows = _search_rows(response)
    matched_ids, exact_unique = unique_exact_match_ids(title, rows, "id")
    if exact_unique:
        return {
            "error": None,
            "candidates": _candidates_from_rows(rows, "id", "BUSINESS", "EXACT", matched_ids),
            "exact_unique": True,
            "empty": False,
        }
    if matched_ids:
        # 多个不同条目精确命中同名：歧义，保留命中项，绝不自动选中
        return {
            "error": None,
            "candidates": _candidates_from_rows(rows, "id", "BUSINESS", "CANDIDATE", matched_ids),
            "exact_unique": False,
            "empty": False,
        }
    if rows:
        # 成功非空但没有唯一精确命中：保留安全候选，不能当作空结果回退 RAG
        return {
            "error": None,
            "candidates": _candidates_from_rows(rows, "id", "BUSINESS", "CANDIDATE"),
            "exact_unique": False,
            "empty": False,
        }
    # 成功且空结果：允许 RAG 模糊回退
    return {"error": None, "candidates": [], "exact_unique": False, "empty": True}


def _rag_lookup(title: str, user: UserInfo, retrieval: RetrieveSubjectsUseCase) -> dict:
    """复用 rag_search_subjects 的 RetrieveSubjectsUseCase；不复制检索/证据逻辑。"""
    try:
        query = RetrievalQuery(semantic_query=title[:_RAG_QUERY_MAX_LEN])
    except Exception:  # noqa: BLE001 - 标题含非法控制字符或过长
        return {"error": {"error": True, "message": "标题包含非法字符或过长"}}
    try:
        result = retrieval.execute(query, mode="search", user=user)
    except Exception:  # noqa: BLE001 - RAG 异常按不可用处理，不伪装成无结果
        return {"error": {"error": True, "message": "名称解析暂时不可用，请稍后再试或直接提供番剧ID"}}
    if not isinstance(result, dict) or not result.get("available"):
        return {"error": {"error": True, "message": "名称解析暂时不可用，请稍后再试或直接提供番剧ID"}}
    items = result.get("items")
    rows = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
    matched_ids, exact_unique = unique_exact_match_ids(title, rows, "subjectId")
    if exact_unique:
        return {
            "error": None,
            "candidates": _candidates_from_rows(rows, "subjectId", "RAG", "EXACT", matched_ids),
            "exact_unique": True,
            "empty": False,
        }
    if matched_ids:
        return {
            "error": None,
            "candidates": _candidates_from_rows(rows, "subjectId", "RAG", "CANDIDATE", matched_ids),
            "exact_unique": False,
            "empty": False,
        }
    if rows:
        # 相似度最高但没有唯一标题/别名精确命中：作为候选展示，绝不自动预览
        return {
            "error": None,
            "candidates": _candidates_from_rows(rows, "subjectId", "RAG", "CANDIDATE"),
            "exact_unique": False,
            "empty": False,
        }
    return {"error": None, "candidates": [], "exact_unique": False, "empty": True}


def build_resolution_action(
    user: UserInfo,
    query: str,
    survivors: list[dict],
    collection_type: int | None = None,
) -> SubjectResolutionPendingAction:
    """构造 SUBJECT_RESOLUTION 待选择状态；collection_type 记录选中后要设置的目标类型。"""
    return SubjectResolutionPendingAction(
        type="SUBJECT_RESOLUTION",
        user_id=user.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=_RESOLUTION_TTL_SECONDS),
        query=query,
        collection_type=collection_type,
        candidates=[
            SubjectResolutionCandidate(
                subject_id=c["subjectId"],
                subject_name=c["name"],
                match_source=c["matchSource"],
                match_type=c["matchType"],
            )
            for c in survivors
        ],
    )


def resolve_candidates(
    title: str,
    subject_id: int | None,
    user: UserInfo,
    business: BusinessGateway,
    retrieval: RetrieveSubjectsUseCase,
) -> dict:
    """确定性标题解析：显式 ID / Business 首查 / 仅成功空结果回退 RAG / /batch 权威校验。

    返回归一化结果：
    - ``{"kind": "error", "response": {...}}``：基础设施错误或 RAG 不可用（不回退、不预览）。
    - ``{"kind": "no_match", "reason": str}``：无唯一有效候选。
    - ``{"kind": "ok", "survivors": [...], "exact_unique": bool, "query": str}``。
    """
    explicit_id = _safe_subject_id(subject_id)
    if explicit_id is not None:
        candidates = [{"subjectId": explicit_id, "name": "", "matchSource": "EXPLICIT", "matchType": "EXACT"}]
        exact_unique = True
        query = str(explicit_id)
    else:
        query = (title or "").strip()
        if not query:
            return {"kind": "no_match", "reason": "empty_query"}
        stage = _business_lookup(query, user, business)
        if stage["error"] is not None:
            return {"kind": "error", "response": stage["error"]}
        candidates, exact_unique = stage["candidates"], stage["exact_unique"]
        if stage["empty"]:
            # 只有 Business 成功且空结果才回退 RAG
            stage = _rag_lookup(query, user, retrieval)
            if stage["error"] is not None:
                return {"kind": "error", "response": stage["error"]}
            candidates, exact_unique = stage["candidates"], stage["exact_unique"]

    ids = dedup_ids([c["subjectId"] for c in candidates])
    if not ids:
        return {"kind": "no_match", "reason": "no_results"}

    valid, batch_error = filter_authoritative(ids, business, user.token)
    if batch_error is not None:
        return {"kind": "error", "response": batch_error}

    survivors: list[dict] = []
    seen: set[int] = set()
    for candidate in candidates:
        sid = candidate["subjectId"]
        if sid in seen or sid not in valid:
            continue
        seen.add(sid)
        enriched = dict(candidate)
        enriched["name"] = _display_name(valid[sid], candidate.get("name", ""))
        survivors.append(enriched)
    survivors = survivors[:_MAX_RESOLUTION_CANDIDATES]

    if not survivors:
        return {"kind": "no_match", "reason": "no_valid_subject"}
    return {"kind": "ok", "survivors": survivors, "exact_unique": exact_unique, "query": query}


def finalize_resolution(outcome: dict, user: UserInfo, *, preview_one, collection_type: int | None) -> dict:
    """把解析结果落地为：错误 / 无匹配 / 唯一精确预览 / SUBJECT_RESOLUTION 多候选。

    ``preview_one(only, user)`` 由调用方提供（想看或设类型），保证写入边界只有一处入口。
    调用方在此之前已 emit CLEAR；若唯一候选的预览未产生待确认动作（如已收藏/无需变更），
    最后的 CLEAR 即为最终状态，不会残留陈旧待确认动作。
    """
    if outcome["kind"] == "error":
        return outcome["response"]
    if outcome["kind"] == "no_match":
        return {"resolved": False, "reason": outcome["reason"], "message": "没有找到匹配项"}

    survivors, exact_unique, query = outcome["survivors"], outcome["exact_unique"], outcome["query"]
    if len(survivors) == 1 and exact_unique:
        preview = preview_one(survivors[0], user)
        if isinstance(preview, dict) and preview.get("error"):
            return preview
        return {"resolved": True, "matchType": "EXACT", "preview": preview}

    # 多个或歧义候选：只保存 SUBJECT_RESOLUTION，展示候选并暂停，绝不自动预览
    emit_pending_action_set(build_resolution_action(user, query, survivors, collection_type))
    return {
        "resolved": False,
        "reason": "multiple_candidates",
        "needsSelection": True,
        "message": "找到多个可能的番剧，请让用户选择",
        "candidates": [
            {
                "index": i + 1,
                "subjectId": c["subjectId"],
                "subjectName": c["name"],
                "matchSource": c["matchSource"],
            }
            for i, c in enumerate(survivors)
        ],
    }



def _search_rows(response: Any) -> list[dict]:
    if isinstance(response, dict):
        content = response.get("content")
        rows = content if isinstance(content, list) else []
    elif isinstance(response, list):
        rows = response
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)]


def _selection_message(code: str | None) -> str:
    if code == "ambiguous_name":
        return "候选名称不唯一，请按序号选择"
    return "选择无效，请按候选序号或唯一名称选择"


def build_subject_resolution_tools(business: BusinessGateway, retrieval: RetrieveSubjectsUseCase):
    @tool
    @tool_call_status(display_name="解析番剧标题")
    def resolve_subject_by_title(
            title: str = "",
            subject_id: int | None = None,
            user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
        """按单个番剧标题安全解析并预览加入「想看」。

        - 用户明确给出番剧ID时传 subject_id（跳过名称搜索，仍做权威校验）。
        - 只有标题时传 title（原始标题，勿改写为「第2季」等语义变体）。
        返回 preview 表示已进入既有加入想看预览，仍需用户明确确认；
        返回 needsSelection 时必须向用户展示候选并等待其选择，不得自行选中。"""
        err = _require_user(user)
        if err:
            return err
        # 新的标题解析始终取代任何陈旧的待确认/待选择状态（只清理本地状态，不改业务数据）。
        emit_pending_action_clear()
        outcome = resolve_candidates(title, subject_id, user, business, retrieval)
        return finalize_resolution(
            outcome,
            user,
            preview_one=lambda only, u: build_wishlist_preview(
                [{"subjectId": only["subjectId"], "subjectName": only["name"]}], u, business
            ),
            collection_type=None,
        )

    @tool
    @tool_call_status(display_name="选择候选番剧")
    def select_resolved_subject(
            choice: int | str,
            pending: Annotated[SubjectResolutionPendingAction | None, InjectedState("pending_action")] = None,
            user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
        """从系统展示的候选中选择一部番剧，再进入加入想看预览。

        choice: 候选序号（从 1 开始）或唯一候选名称；不接受自造 subjectId。
        选择只作用于系统注入的 SUBJECT_RESOLUTION 状态，并会重新做权威校验。"""
        err = _require_user(user)
        if err:
            return err
        if pending is None or getattr(pending, "type", None) != "SUBJECT_RESOLUTION":
            return {"error": True, "message": "没有待选择的番剧候选"}
        if pending.user_id != user.user_id:
            emit_pending_action_clear()
            return {"error": True, "message": "候选状态不属于当前用户"}
        if _is_expired(pending.expires_at):
            emit_pending_action_clear()
            return {"error": True, "message": "候选已过期，请重新发起请求"}

        candidate, code = select_candidate(choice, pending.candidates)
        if candidate is None:
            # 保留状态，允许用户重新选择
            return {"error": True, "reason": code, "message": _selection_message(code)}

        valid, batch_error = filter_authoritative([candidate.subject_id], business, user.token)
        if batch_error is not None:
            return batch_error
        if candidate.subject_id not in valid:
            emit_pending_action_clear()
            return {"error": True, "message": "该候选已不可用，请重新发起请求"}

        name = _display_name(valid[candidate.subject_id], candidate.subject_name)
        selected = {"subjectId": candidate.subject_id, "subjectName": name}
        target_type = getattr(pending, "collection_type", None)
        if target_type is None:
            # 09-16 想看链路：选中后进入既有加入想看预览
            preview = build_wishlist_preview(
                [{"subjectId": candidate.subject_id, "subjectName": name}], user, business
            )
            if preview.get("error"):
                return preview
            if not preview.get("pendingItems"):
                # 已收藏或无可确认条目：清理待选择状态，避免陈旧候选被复用
                emit_pending_action_clear()
            return {"resolved": True, "selected": selected, "preview": preview}

        # 设类型链路：选中后进入 SET_COLLECTION_TYPE 预览（延迟导入避免模块环）
        from app.agent.client.actions.collection_type import build_collection_type_preview

        preview = build_collection_type_preview(candidate.subject_id, name, target_type, user, business)
        if isinstance(preview, dict) and preview.get("error"):
            return preview
        if preview.get("action") == "NOOP":
            # 已在目标类型、无需写入：清理待选择状态
            emit_pending_action_clear()
        return {"resolved": True, "selected": selected, "preview": preview}

    return [resolve_subject_by_title, select_resolved_subject]


