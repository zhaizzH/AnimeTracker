"""实体解析：名称与类型化实体 ID 经业务侧 /resolve 的安全解析（从 retrieval.py 拆出，move-only）。"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from app.rag.schemas import RetrievalQuery

EntityResolveLookup = Callable[..., dict | list]
EntityNameLookup = Callable[..., Any]

def is_error(response: Any) -> bool:
    return isinstance(response, Mapping) and bool(response.get("error"))

def resolve_entity_subject_ids(
    query: RetrievalQuery,
    *,
    token: str | None,
    resolve_lookup: EntityResolveLookup | None,
    name_matches: list[tuple[str, int]] | None = None,
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
    by_kind: dict[str, list[int]] = {"PERSON": [], "CHARACTER": [], "ACTOR": [], "RELATION_SUBJECT": []}
    for entity_type, entity_id in name_matches or []:
        by_kind[entity_type].append(entity_id)
    if not any(ids for _, ids in requested) and not any(by_kind.values()):
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
    # 未指定类型的名称可能同时匹配人物和角色。
    # 这些候选在名称约束内是 OR 关系；下方只对不同查询字段做 AND。
    if any(by_kind.values()):
        name_allowed: list[int] = []
        name_seen: set[int] = set()
        for entity_type, entity_ids in by_kind.items():
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
            for subject_id in resolved:
                if subject_id not in name_seen:
                    name_seen.add(subject_id)
                    name_allowed.append(subject_id)
        if allowed is None:
            allowed = name_allowed
        else:
            name_allowed_set = set(name_allowed)
            allowed = [subject_id for subject_id in allowed if subject_id in name_allowed_set]
        if not allowed:
            return [], None
    return allowed or [], None

def lookup_entity_name(
    query: RetrievalQuery,
    *,
    lookup: EntityNameLookup | None,
) -> tuple[list[tuple[str, int]], str | None]:
    """通过影子索引把面向用户的名称解析为类型化本地 ID。"""
    if not query.entity_name:
        return [], None
    if lookup is None:
        return [], "entity_resolution_unavailable"
    try:
        response = lookup(
            query.entity_name,
            entity_kind=query.entity_kind,
            limit=50,
        )
    except Exception:
        return [], "entity_resolution_unavailable"
    if isinstance(response, Mapping):
        response = response.get("items", response.get("matches", response.get("data")))
    if not isinstance(response, (list, tuple)):
        return [], "entity_resolution_unavailable"
    matches: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    allowed_kinds = {query.entity_kind} if query.entity_kind else {"PERSON", "CHARACTER", "ACTOR", "RELATION_SUBJECT"}
    for row in response:
        if isinstance(row, Mapping):
            raw_kind = row.get("entity_kind", row.get("entityType"))
            raw_id = row.get("entity_id", row.get("entityId"))
        else:
            raw_kind = getattr(row, "entity_kind", None)
            raw_id = getattr(row, "entity_id", None)
        kind = str(raw_kind or "").upper()
        if kind not in allowed_kinds or isinstance(raw_id, bool):
            return [], "entity_resolution_unavailable"
        try:
            entity_id = int(raw_id)
        except (TypeError, ValueError):
            return [], "entity_resolution_unavailable"
        if entity_id < 1:
            return [], "entity_resolution_unavailable"
        identity = (kind, entity_id)
        if identity not in seen:
            seen.add(identity)
            matches.append(identity)
    return matches, None

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
