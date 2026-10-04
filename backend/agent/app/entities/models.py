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
    CreditType,
    DetailStatus,
    EntityKind,
    ImageStorageStatus,
    JobStatus,
    JobType,
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
    """subject_person_credit 表行映射（主创关系单表）。

    已解析时 person_id 填 FK 且 name 为 None；未解析时 person_id 为 None 且 name 存占位名。
    """

    id: int
    subject_id: int
    person_id: int | None
    name: str | None
    credit_type: CreditType = CreditType.PERSON
    role: str = ""
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
class Job:
    """job 表行映射（统一任务队列）。"""

    id: int
    type: JobType
    entity_kind: EntityKind
    entity_id: int
    index_version: str = ""
    content_hash: str = ""
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_attempts: int = 5
    next_retry_at: datetime | None = None
    last_error_code: str | None = None
    last_error_message: str | None = None
    payload_json: str | None = None
    claimed_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
