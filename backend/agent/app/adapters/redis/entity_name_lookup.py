"""Business-owned entity name resolution contract.

Redis Vector Set has no lexical name index. Entity names therefore resolve via
the typed Business endpoint; this adapter is a small boundary that prevents
callers from reintroducing storage-specific text expressions into the Agent process.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal


EntityNameKind = Literal["PERSON", "CHARACTER", "ACTOR", "RELATION_SUBJECT"]


@dataclass(frozen=True)
class EntityNameMatch:
    entity_kind: EntityNameKind
    entity_id: int


class RedisEntityNameLookup:
    """Compatibility name for the old adapter; delegates to a typed resolver."""

    def __init__(self, redis_client: Any = None, *, index_version: str = "", resolver: Callable[..., Any] | None = None, **_kwargs: Any) -> None:
        self._resolver = resolver
        self._index_version = index_version

    def lookup(self, entity_name: str, *, entity_kind: EntityNameKind | None = None, limit: int = 50) -> list[EntityNameMatch]:
        if not isinstance(entity_name, str) or not entity_name.strip() or len(entity_name.strip()) > 48:
            raise ValueError("entity_name 无效")
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        if self._resolver is None:
            raise RuntimeError("实体名称解析必须使用 Business typed resolver；Vector Set 不提供全文名称查询")
        response = self._resolver(entity_name.strip(), entity_kind=entity_kind, limit=min(limit, 50))
        if not isinstance(response, (list, tuple)):
            raise RuntimeError("Business entity resolver response invalid")
        result: list[EntityNameMatch] = []
        for row in response:
            if isinstance(row, EntityNameMatch):
                match = row
            elif isinstance(row, dict):
                match = EntityNameMatch(str(row.get("entity_kind", row.get("entityType"))).upper(), int(row.get("entity_id", row.get("entityId"))))
            else:
                raise RuntimeError("Business entity resolver row invalid")
            if match.entity_id < 1:
                raise RuntimeError("Business entity resolver entity id invalid")
            result.append(match)
        return result
