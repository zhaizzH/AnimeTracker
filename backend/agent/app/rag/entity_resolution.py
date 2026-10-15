"""实体解析：类型化实体 ID 经业务侧 /resolve 的安全解析（从 retrieval.py 拆出，move-only）。"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from app.rag.schemas import RetrievalQuery

EntityResolveLookup = Callable[..., dict | list]

def is_error(response: Any) -> bool:
    return isinstance(response, Mapping) and bool(response.get("error"))

def resolve_entity_subject_ids(
    query: RetrievalQuery,
    *,
    token: str | None,
    resolve_lookup: EntityResolveLookup | None,
) -> tuple[list[int] | None, str | None]:
    """在触碰索引前先通过业务侧解析类型化实体 ID。

    解析响应只保留安全的 Subject ID。在本服务中，实体 ID
    绝不会变成 Redis 表达式或 SQL 片段。
    多个实体过滤条件是取交集，并保留业务侧对第一个过滤器的确定性顺序。
    """
    requested = [
        ("PERSON", query.person_ids),
        ("CHARACTER", query.character_ids),
        ("ACTOR", query.actor_ids),
        ("RELATION_SUBJECT", query.relation_subject_ids),
    ]
    if not any(ids for _, ids in requested):
        return None, None
    if resolve_lookup is None:
        return [], "entity_resolution_unavailable"

    allowed: list[int] | None = None
    for entity_type, entity_ids in requested:
        if not entity_ids:
            continue
        try:
            response = resolve_lookup(entity_type, list(entity_ids), token=token)
        except Exception:
            return [], "entity_resolution_unavailable"
        if is_error(response):
            return [], "entity_resolution_unavailable"
        resolved, valid = safe_resolved_subject_ids(response)
        if not valid:
            return [], "entity_resolution_unavailable"
        if allowed is None:
            allowed = resolved
        else:
            resolved_set = set(resolved)
            allowed = [subject_id for subject_id in allowed if subject_id in resolved_set]
        if not allowed:
            return [], None
    return allowed or [], None

def safe_resolved_subject_ids(response: Any) -> tuple[list[int], bool]:
    """仅从 /resolve 提取活动的、非 NSFW 的动画 Subject。"""
    if isinstance(response, list):
        # 直接列表是 HttpBusinessGateway 归一化后的成功响应。
        # Redis 协议数组在此无效。
        if response and isinstance(response[0], int):
            return [], False
        rows = response
    elif isinstance(response, Mapping):
        rows = response.get("items")
        if rows is None:
            rows = response.get("content")
        if rows is None:
            rows = response.get("data")
        if not isinstance(rows, list):
            return [], False
    else:
        return [], False
    subject_ids: list[int] = []
    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            return [], False
        raw_id = row.get("subjectId", row.get("subject_id", row.get("id")))
        if isinstance(raw_id, bool):
            return [], False
        try:
            subject_id = int(raw_id)
        except (TypeError, ValueError):
            return [], False
        if subject_id <= 0 or not is_safe_subject_response(row):
            return [], False
        if subject_id not in seen:
            seen.add(subject_id)
            subject_ids.append(subject_id)
    return subject_ids, True

def is_safe_subject_response(item: Mapping[str, Any]) -> bool:
    try:
        if int(item.get("type") or 0) != 2 or item.get("nsfw") is not False:
            return False
        # 业务侧把 import_status 暴露为派生字段 `active`；
        # 缺失时失败即闭合，因为实体过滤绝不能因权威响应不完整
        # 而扩大候选集。
        if item.get("active") is not True:
            return False
        if "importStatus" in item and int(item.get("importStatus") or 0) != 1:
            return False
        if "import_status" in item and int(item.get("import_status") or 0) != 1:
            return False
    except (TypeError, ValueError):
        return False
    return True
