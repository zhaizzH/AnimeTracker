"""候选匹配与选择：识别「唯一精确命中」、去重 ID 列表、按序号或名称从多候选中选择。

不接受子串命中、不接受自造 subject_id。
纯函数集合，无副作用。
"""

from __future__ import annotations

import re
from typing import Any

from app.agent.client.actions.title_normalizer import normalize_title
from app.chat.pending_action import SubjectResolutionCandidate

_ORDINAL_RE = re.compile(r"\s*(?:第\s*)?(\d+)\s*(?:个|项|条|号)?\s*")


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
