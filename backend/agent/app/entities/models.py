"""Person/Character 及关系表的领域数据模型。

所有模型为 frozen dataclass，与 docs/database/db-schema.sql 中的列一一对应。
不使用 ORM declarative base；持久化通过 repository 中的 raw SQL 完成。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.entities.enums import (
    ActorRelation,
    CharacterRelation,
    CharacterType,
    CreditRelation,
    DetailStatus,
    EntityKind,
    ImageStorageStatus,
    JobStatus,
    PersonType,
)


@dataclass(frozen=True)
class Person:
    """person 表行映射。"""

    id: int
    bangumi_person_id: int
    person_type: PersonType
    name: str
    summary: str | None = None
    career_json: str | None = None
    infobox_json: str | None = None
    image: str | None = None
    image_source_url: str | None = None
    image_storage_status: ImageStorageStatus = ImageStorageStatus.PENDING
    detail_status: DetailStatus = DetailStatus.SUMMARY_ONLY
    source_hash: str | None = None
    source_fetched_at: datetime | None = None
    last_seen_import_id: int | None = None
    source_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Character:
    """character 表行映射。"""

    id: int
    bangumi_character_id: int
    character_type: CharacterType
    name: str
    summary: str | None = None
    infobox_json: str | None = None
    image: str | None = None
    image_source_url: str | None = None
    image_storage_status: ImageStorageStatus = ImageStorageStatus.PENDING
    detail_status: DetailStatus = DetailStatus.SUMMARY_ONLY
    source_hash: str | None = None
    source_fetched_at: datetime | None = None
    last_seen_import_id: int | None = None
    source_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PersonAlias:
    """person_alias 表行映射。"""

    id: int
    person_id: int
    name: str
    language: str = "und"
    source: str = "infobox"
    source_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class CharacterAlias:
    """character_alias 表行映射。"""

    id: int
    character_id: int
    name: str
    language: str = "und"
    source: str = "infobox"
    source_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class SubjectPersonCredit:
    """subject_person_credit 表行映射。"""

    id: int
    subject_id: int
    person_id: int
    role: str
    relation: CreditRelation = CreditRelation.MAIN
    sort_order: int = 0
    source_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class SubjectCharacter:
    """subject_character 表行映射。"""

    id: int
    subject_id: int
    character_id: int
    relation: CharacterRelation = CharacterRelation.MAIN
    sort_order: int = 0
    source_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class CharacterActor:
    """character_actor 表行映射。"""

    id: int
    subject_id: int
    character_id: int
    person_id: int
    actor_relation: ActorRelation = ActorRelation.VA
    sort_order: int = 0
    source_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class EntityDetailJob:
    """entity_detail_job 表行映射。"""

    id: int
    entity_kind: EntityKind
    entity_id: int
    source_id: int
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_attempts: int = 5
    next_retry_at: datetime | None = None
    last_error_code: str | None = None
    last_error_message: str | None = None
    checkpoint_json: str | None = None
    source_hash: str | None = None
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class SearchIndexJob:
    """search_index_job 表行映射。"""

    id: int
    entity_kind: EntityKind
    entity_id: int
    index_version: str
    profile_version: str = "v1"
    content_hash: str = ""
    embedding_provider: str = "dashscope"
    embedding_model: str = ""
    embedding_dimensions: int = 1024
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_attempts: int = 5
    last_error_code: str | None = None
    last_error_message: str | None = None
    next_retry_at: datetime | None = None
    claimed_at: datetime | None = None
    indexed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
