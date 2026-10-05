"""由业务侧负责的实体名称解析契约。

Redis Vector Set 没有词法名称索引，因此实体名称通过类型化业务接口解析；
本适配器是一层薄边界，防止调用方把特定存储的文本表达式重新引入 Agent 进程。
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
    """旧适配器的兼容名称；委托给类型化解析器。"""

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
            raise RuntimeError("Business 实体解析器响应无效")
        result: list[EntityNameMatch] = []
        for row in response:
            if isinstance(row, EntityNameMatch):
                match = row
            elif isinstance(row, dict):
                match = EntityNameMatch(str(row.get("entity_kind", row.get("entityType"))).upper(), int(row.get("entity_id", row.get("entityId"))))
            else:
                raise RuntimeError("Business 实体解析器数据行无效")
            if match.entity_id < 1:
                raise RuntimeError("Business 实体解析器实体 ID 无效")
            result.append(match)
        return result
