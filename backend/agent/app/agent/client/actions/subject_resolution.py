"""单标题「加入想看」的确定性解析链路。

安全边界（与 design.md / spec 一致）：
- 用户显式给出 subjectId 时跳过名称搜索，但仍必须经过 ``/api/client/subjects/batch`` 权威校验。
- 只有标题时先调用 Business ``/api/client/subjects/search``；只有 Business 成功且候选为空时才回退 RAG。
- Business/RAG 的基础设施错误、超时、坏响应绝不伪装成「无结果」，也不触发 RAG 回退。
- 归一化只做安全字符处理（NFKC、大小写折叠、标点分隔、空白折叠），绝不做「第二季/第2季」等语义转换。
- 所有候选进入预览前都经过 ``/batch`` 过滤 ``active=true``、``type=2``、``nsfw=false``，且 ``excludeCollected=false``。
- 唯一精确候选复用既有 ``build_wishlist_preview``；多个或歧义候选保存 ``SUBJECT_RESOLUTION`` 等待用户选择，绝不自动预览。
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.agent.client.actions.wishlist import build_wishlist_preview
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

# 归一化时被当作分隔符的安全标点（NFKC 之后全角多已折叠为半角）。
# 只处理字符层面，绝不映射任何语义变体。
_PUNCTUATION_RE = re.compile(
    r"[·・、,，.。!！?？~～\-—–‐_＿:：;；'\"’‘“”()（）\[\]【】{}｛｝<>《》|/\\+*=&^%$#@`]+"
)
_WHITESPACE_RE = re.compile(r"\s+")
_ORDINAL_RE = re.compile(r"\s*(?:第\s*)?(\d+)\s*(?:个|项|条|号)?\s*")


def normalize_title(value: Any) -> str:
    """安全标题归一化：NFKC + 大小写折叠 + 标点分隔 + 空白折叠 + 首尾清理。

    对查询和候选标题使用同一函数；不包含任何语义转换。
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = _PUNCTUATION_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _safe_subject_id(value: Any) -> int | None:
    """拒绝布尔、非数字、非正数和溢出转换；坏 ID 返回 None，不抛异常。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        subject_id = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return subject_id if subject_id > 0 else None


def _candidate_titles(item: dict) -> list[str]:
    titles: list[str] = []
    for key in ("name", "nameCn", "title"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            titles.append(value)
    aliases = item.get("aliases")
    if isinstance(aliases, list):
        for alias in aliases:
            if isinstance(alias, str) and alias.strip():
                titles.append(alias)
    return titles


def unique_exact_match_ids(query: Any, items: list[dict], id_key: str) -> tuple[list[int], bool]:
    """返回 (归一化后精确命中的去重 subjectId 列表, 是否唯一)。

    只有真实标题或工具证据中的别名可以命中；子串命中不算精确命中。
    """
    normalized_query = normalize_title(query)
    if not normalized_query:
        return [], False
    matched: list[int] = []
    seen: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        subject_id = _safe_subject_id(item.get(id_key))
        if subject_id is None or subject_id in seen:
            continue
        if any(normalize_title(title) == normalized_query for title in _candidate_titles(item)):
            seen.add(subject_id)
            matched.append(subject_id)
    return matched, len(matched) == 1


def dedup_ids(ids: list[Any]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for raw in ids:
        subject_id = _safe_subject_id(raw)
        if subject_id is None or subject_id in seen:
            continue
        seen.add(subject_id)
        ordered.append(subject_id)
    return ordered


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


def _as_index(choice: Any, count: int) -> int | None:
    """把序号选择解析为 0-based 下标；越界或非序号返回 None。"""
    number: int | None = None
    if isinstance(choice, bool):
        return None
    if isinstance(choice, int):
        number = choice
    elif isinstance(choice, str):
        match = _ORDINAL_RE.fullmatch(choice)
        if match:
            number = int(match.group(1))
    if number is None or not (1 <= number <= count):
        return None
    return number - 1


def select_candidate(
    choice: Any,
    candidates: list[SubjectResolutionCandidate],
) -> tuple[SubjectResolutionCandidate | None, str | None]:
    """按序号或归一化后的唯一名称从服务端候选中选择；模型不能提交任意 subjectId。"""
    if not candidates:
        return None, "no_candidates"
    index = _as_index(choice, len(candidates))
    if index is not None:
        return candidates[index], None
    if isinstance(choice, str):
        normalized = normalize_title(choice)
        if normalized:
            matches = [c for c in candidates if normalize_title(c.subject_name) == normalized]
            if len(matches) == 1:
                return matches[0], None
            if len(matches) > 1:
                return None, "ambiguous_name"
    return None, "invalid_choice"


def _search_rows(response: Any) -> list[dict]:
    if isinstance(response, dict):
        content = response.get("content")
        rows = content if isinstance(content, list) else []
    elif isinstance(response, list):
        rows = response
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)]


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


def _resolution_action(user: UserInfo, query: str, survivors: list[dict]) -> SubjectResolutionPendingAction:
    return SubjectResolutionPendingAction(
        type="SUBJECT_RESOLUTION",
        user_id=user.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=_RESOLUTION_TTL_SECONDS),
        query=query,
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


def _is_expired(expires_at: datetime) -> bool:
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= now


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

        explicit_id = _safe_subject_id(subject_id)
        if explicit_id is not None:
            candidates = [{"subjectId": explicit_id, "name": "", "matchSource": "EXPLICIT", "matchType": "EXACT"}]
            exact_unique = True
            query = str(explicit_id)
        else:
            query = (title or "").strip()
            if not query:
                return {"resolved": False, "reason": "empty_query", "message": "没有找到匹配项"}
            stage = _business_lookup(query, user, business)
            if stage["error"] is not None:
                return stage["error"]
            candidates, exact_unique = stage["candidates"], stage["exact_unique"]
            if stage["empty"]:
                # 只有 Business 成功且空结果才回退 RAG
                stage = _rag_lookup(query, user, retrieval)
                if stage["error"] is not None:
                    return stage["error"]
                candidates, exact_unique = stage["candidates"], stage["exact_unique"]

        ids = dedup_ids([c["subjectId"] for c in candidates])
        if not ids:
            return {"resolved": False, "reason": "no_results", "message": "没有找到匹配项"}

        valid, batch_error = filter_authoritative(ids, business, user.token)
        if batch_error is not None:
            return batch_error

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
            return {"resolved": False, "reason": "no_valid_subject", "message": "没有找到匹配项"}

        if len(survivors) == 1 and exact_unique:
            only = survivors[0]
            preview = build_wishlist_preview(
                [{"subjectId": only["subjectId"], "subjectName": only["name"]}], user, business
            )
            if preview.get("error"):
                return preview
            if not preview.get("pendingItems"):
                # 已收藏或无可确认条目：清理刚才的 CLEAR 之外无需保留状态
                emit_pending_action_clear()
            return {"resolved": True, "matchType": "EXACT", "preview": preview}

        # 多个或歧义候选：只保存 SUBJECT_RESOLUTION，展示候选并暂停，绝不自动预览
        emit_pending_action_set(_resolution_action(user, query, survivors))
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
        preview = build_wishlist_preview(
            [{"subjectId": candidate.subject_id, "subjectName": name}], user, business
        )
        if preview.get("error"):
            return preview
        if not preview.get("pendingItems"):
            # 已收藏或无可确认条目：清理待选择状态，避免陈旧候选被复用
            emit_pending_action_clear()
        return {
            "resolved": True,
            "selected": {"subjectId": candidate.subject_id, "subjectName": name},
            "preview": preview,
        }

    return [resolve_subject_by_title, select_resolved_subject]


def _require_user(user: UserInfo | None) -> dict | None:
    if user is None:
        return {"error": True, "message": "用户上下文不可用"}
    return None
