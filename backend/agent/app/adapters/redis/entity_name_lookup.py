"""受控的多实体名称解析适配器。

该适配器只读取 indexer 写入的实体 shadow index，不负责决定最终可展示的
Subject。返回的实体 ID 必须再次经过 Business ``evidence/resolve`` 权威关系
查询，避免 Redis 中的陈旧文档或不完整关系进入 Agent 上下文。
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal

from app.rag.retrieval import escape_redis_term


EntityNameKind = Literal["PERSON", "CHARACTER", "ACTOR"]
_MAX_NAME_LENGTH = 48
_MAX_RESULTS = 50
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class EntityNameMatch:
    entity_kind: EntityNameKind
    entity_id: int


class RedisEntityNameLookup:
    """在版本化实体索引中执行安全 TEXT 名称查询。"""

    def __init__(
        self,
        redis_client: Any,
        *,
        index_version: str,
        index_prefix: str = "idx:rag:entity:",
    ) -> None:
        if not _VERSION_PATTERN.fullmatch(index_version):
            raise ValueError("index_version 不能为空，且只能包含字母、数字、点、下划线或短横线")
        if not index_prefix or any(char.isspace() for char in index_prefix):
            raise ValueError("index_prefix 不能为空且不能包含空白")
        self._redis = redis_client
        self._index_name = f"{index_prefix}{index_version}"

    def lookup(
        self,
        entity_name: str,
        *,
        entity_kind: EntityNameKind | None = None,
        limit: int = _MAX_RESULTS,
    ) -> list[EntityNameMatch]:
        """按实体名称/别名查找候选实体，名称永远作为 TEXT 参数转义。"""
        normalized = _validate_name(entity_name)
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        limit = min(limit, _MAX_RESULTS)
        # ACTOR uses the same local person entity as PERSON, but its later
        # Business resolve path is different (character_actor relation).
        index_kinds = ("PERSON",) if entity_kind == "ACTOR" else ((entity_kind,) if entity_kind else ("PERSON", "CHARACTER"))
        kind_expression = "|".join(index_kinds)
        # Quoting the escaped term keeps whitespace inside the user term and
        # prevents a name from becoming a RediSearch operator/query fragment.
        text_term = escape_redis_term(normalized)
        expression = (
            f'(@name:("{text_term}")|@aliases:("{text_term}")) '
            f"@entity_kind:{{{kind_expression}}}"
        )
        raw = self._redis.execute_command(
            "FT.SEARCH",
            self._index_name,
            expression,
            "RETURN",
            "4",
            "entity_kind",
            "entity_id",
            "name",
            "aliases",
            "LIMIT",
            "0",
            str(limit),
            "DIALECT",
            "2",
        )
        matches = _parse_matches(raw, index_kinds)
        if entity_kind == "ACTOR":
            return [EntityNameMatch("ACTOR", match.entity_id) for match in matches]
        return matches


def _validate_name(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("entity_name 必须是字符串")
    normalized = value.strip()
    if not normalized or len(normalized) > _MAX_NAME_LENGTH or any(ord(char) < 0x20 for char in normalized):
        raise ValueError("entity_name 必须是 1-48 个可见字符")
    return normalized


def _parse_matches(raw: Any, allowed_kinds: tuple[EntityNameKind, ...]) -> list[EntityNameMatch]:
    if not isinstance(raw, (list, tuple)):
        raise ValueError("实体名称索引返回格式无效")
    if not raw:
        return []
    if not isinstance(raw[0], int) or isinstance(raw[0], bool):
        raise ValueError("实体名称索引返回格式无效")
    rows: list[EntityNameMatch] = []
    seen: set[tuple[str, int]] = set()
    for offset in range(1, len(raw), 2):
        if offset + 1 >= len(raw) or not isinstance(raw[offset + 1], (list, tuple)):
            raise ValueError("实体名称索引返回格式无效")
        fields = raw[offset + 1]
        values: dict[str, Any] = {}
        if len(fields) % 2:
            raise ValueError("实体名称索引返回字段无效")
        for index in range(0, len(fields), 2):
            key = _text(fields[index])
            values[key] = fields[index + 1]
        kind = _text(values.get("entity_kind", ""))
        if kind not in allowed_kinds:
            raise ValueError("实体名称索引返回了未请求的实体类型")
        raw_id = values.get("entity_id")
        if isinstance(raw_id, bool):
            raise ValueError("实体名称索引返回 ID 无效")
        try:
            entity_id = int(_text(raw_id))
        except (TypeError, ValueError):
            raise ValueError("实体名称索引返回 ID 无效") from None
        if entity_id < 1:
            raise ValueError("实体名称索引返回 ID 无效")
        identity = (kind, entity_id)
        if identity not in seen:
            seen.add(identity)
            rows.append(EntityNameMatch(kind, entity_id))
    return rows


def _text(value: Any) -> str:
    if value is None:
        return ""
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)
