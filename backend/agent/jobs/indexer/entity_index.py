"""通用多实体 Redis/RediSearch 写入器。

Subject 的在线检索仍使用 ``RedisSubjectIndex`` 和旧 alias；本模块只负责
``search_index_job`` 的 SUBJECT/EPISODE/PERSON/CHARACTER shadow 文档。这样
通用任务可以先被可靠消费，未来再按检索需求把实体索引接入查询规划器。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from redis.exceptions import ResponseError

from app.adapters.redis.subject_index import VECTOR_DIMENSIONS, vector_bytes
from app.entities.enums import EntityKind


ENTITY_INDEX_PREFIX = "idx:rag:entity:"
ENTITY_KEY_PREFIX = "rag:entity:"


@dataclass(frozen=True)
class EntityIndexDocument:
    """一个可重建的多实体 shadow 文档。"""

    entity_kind: EntityKind
    entity_id: int
    index_version: str
    profile: Any
    vector: Sequence[float]
    name: str
    aliases: Sequence[str] = ()
    summary: str = ""
    subject_id: int | None = None


class RedisEntityIndex:
    """为通用 search_index_job 提供版本化 HASH 写入和 tombstone 删除。"""

    def __init__(
        self,
        redis_client: Any,
        *,
        key_prefix: str = ENTITY_KEY_PREFIX,
        index_prefix: str = ENTITY_INDEX_PREFIX,
    ) -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._index_prefix = index_prefix

    def index_name(self, index_version: str) -> str:
        return f"{self._index_prefix}{_validate_version(index_version)}"

    def document_key(self, index_version: str, entity_kind: EntityKind, entity_id: int) -> str:
        version = _validate_version(index_version)
        if entity_id < 1:
            raise ValueError("entity_id 必须是正整数")
        return f"{self._key_prefix}{version}:{_kind_value(entity_kind)}:{entity_id}"

    def ensure_version(self, index_version: str) -> str:
        """创建通用实体索引；已存在时安全复用。"""
        version = _validate_version(index_version)
        name = self.index_name(version)
        prefix = f"{self._key_prefix}{version}:"
        try:
            self._redis.execute_command(
                "FT.CREATE",
                name,
                "ON",
                "HASH",
                "PREFIX",
                "1",
                prefix,
                "SCHEMA",
                "entity_kind",
                "TAG",
                "SEPARATOR",
                "|",
                "entity_id",
                "NUMERIC",
                "subject_id",
                "NUMERIC",
                "name",
                "TEXT",
                "aliases",
                "TEXT",
                "summary",
                "TEXT",
                "profile",
                "TEXT",
                "content_hash",
                "TAG",
                "schema_version",
                "TAG",
                "vector",
                "VECTOR",
                "FLAT",
                "6",
                "TYPE",
                "FLOAT32",
                "DIM",
                str(VECTOR_DIMENSIONS),
                "DISTANCE_METRIC",
                "COSINE",
            )
        except ResponseError as exc:
            if "exists" not in str(exc).lower():
                raise
        return name

    def write(self, document: EntityIndexDocument) -> None:
        """写入实体文档；向量维度和有限值由共享编码器验证。"""
        if not isinstance(document.entity_kind, EntityKind):
            raise ValueError("entity_kind 必须是受支持的 EntityKind")
        if document.entity_id < 1:
            raise ValueError("entity_id 必须是正整数")
        profile = document.profile
        profile_text = str(getattr(profile, "text", ""))
        content_hash = str(getattr(profile, "content_hash", ""))
        schema_version = str(getattr(profile, "schema_version", ""))
        if len(content_hash) != 64 or not schema_version:
            raise ValueError("profile 必须包含有效 content_hash/schema_version")
        mapping: dict[str, Any] = {
            "entity_kind": _kind_value(document.entity_kind),
            "entity_id": document.entity_id,
            "name": document.name,
            "aliases": _join(document.aliases),
            "summary": document.summary,
            "profile": profile_text,
            "content_hash": content_hash,
            "schema_version": schema_version,
            "vector": vector_bytes(document.vector),
        }
        if document.subject_id is not None:
            mapping["subject_id"] = document.subject_id
        self._redis.hset(
            self.document_key(document.index_version, document.entity_kind, document.entity_id),
            mapping=mapping,
        )

    def delete(self, index_version: str, entity_kind: EntityKind, entity_id: int) -> None:
        """删除指定版本的文档，重复删除保持幂等。"""
        self._redis.delete(self.document_key(index_version, entity_kind, entity_id))


def _kind_value(entity_kind: EntityKind) -> str:
    return entity_kind.value if isinstance(entity_kind, EntityKind) else str(entity_kind)


def _join(values: Sequence[str]) -> str:
    return " ".join(str(value) for value in values if str(value))


def _validate_version(index_version: str) -> str:
    if not index_version or ":" in index_version or any(char.isspace() for char in index_version):
        raise ValueError("index_version 不能为空、不能包含冒号或空白")
    return index_version
