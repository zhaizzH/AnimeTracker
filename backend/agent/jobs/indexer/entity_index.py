"""Versioned Redis 8 Vector Set writer for all searchable entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from app.adapters.redis.vector_set import RedisVectorSet, safe_attributes
from app.entities.enums import EntityKind


ENTITY_KEY_PREFIX = "rag:vectors:"


@dataclass(frozen=True)
class EntityIndexDocument:
    entity_kind: EntityKind
    entity_id: int
    index_version: str
    profile: Any
    vector: Sequence[float]
    name: str
    aliases: Sequence[str] = ()
    summary: str = ""
    subject_id: int | None = None
    source_active: bool = True
    # Subject filters are evaluated inside the Vector Set.  Keep the same
    # public metadata on generic Subject jobs as on the legacy Subject writer;
    # otherwise ``.type == 2``/``.nsfw == false`` would reject every new row.
    type: int = 2
    nsfw: bool = False
    year: int | None = None
    quarter: int | None = None
    score: float | None = None
    rating_total: int | None = None
    collection_total: int | None = None
    air_status: str = ""


class RedisEntityIndex:
    """Write/delete SUBJECT, EPISODE, PERSON and CHARACTER Vector Set members."""

    def __init__(self, redis_client: Any, *, key_prefix: str = ENTITY_KEY_PREFIX, index_prefix: str = "idx:rag:entity:") -> None:
        self._redis = redis_client
        self._vectors = RedisVectorSet(redis_client, prefix=key_prefix)
        # Kept for diagnostics/backwards-compatible constructor callers.
        self._index_prefix = index_prefix

    def index_name(self, index_version: str) -> str:
        return self._vectors.key(EntityKind.SUBJECT, index_version)

    def vector_key(self, entity_kind: EntityKind, index_version: str) -> str:
        return self._vectors.key(entity_kind, index_version)

    def document_key(self, index_version: str, entity_kind: EntityKind, entity_id: int) -> str:
        return f"{self.vector_key(entity_kind, index_version)}:{entity_kind.value}:{int(entity_id)}"

    def ensure_version(self, index_version: str) -> str:
        self._vectors.ensure_version(index_version)
        return self.vector_key(EntityKind.SUBJECT, index_version)

    def write(self, document: EntityIndexDocument) -> None:
        if not isinstance(document.entity_kind, EntityKind):
            raise ValueError("entity_kind 必须是受支持的 EntityKind")
        profile_text = str(getattr(document.profile, "text", ""))
        content_hash = str(getattr(document.profile, "content_hash", ""))
        schema_version = str(getattr(document.profile, "schema_version", ""))
        if len(content_hash) != 64 or not schema_version or not profile_text:
            raise ValueError("profile 必须包含有效 text/content_hash/schema_version")
        attrs = safe_attributes(
            entity_kind=document.entity_kind,
            entity_id=document.entity_id,
            subject_id=document.subject_id,
            name=document.name,
            aliases=document.aliases,
            content_hash=content_hash,
            schema_version=schema_version,
            source_active=document.source_active,
            type=document.type,
            nsfw=document.nsfw,
            year=document.year,
            quarter=document.quarter,
            score=document.score,
            rating_total=document.rating_total,
            collection_total=document.collection_total,
            air_status=document.air_status,
        )
        self._vectors.add(document.entity_kind, document.entity_id, document.index_version, document.vector, attributes=attrs)

    def delete(self, index_version: str, entity_kind: EntityKind, entity_id: int) -> None:
        self._vectors.remove(entity_kind, entity_id, index_version)
