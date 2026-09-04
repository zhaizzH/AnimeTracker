"""实体与任务相关枚举。

所有枚举值与 docs/database/db-schema.sql 中的 VARCHAR 字面量一一对应；
修改时必须同步 Schema、Java Entity 和本文件。
"""

from __future__ import annotations

from enum import StrEnum


class PersonType(StrEnum):
    """person.person_type"""

    PERSON = "PERSON"
    COMPANY = "COMPANY"
    GROUP = "GROUP"


class CharacterType(StrEnum):
    """character.character_type"""

    CHARACTER = "CHARACTER"
    ORGANIZATION = "ORGANIZATION"


class DetailStatus(StrEnum):
    """person.detail_status / character.detail_status"""

    SUMMARY_ONLY = "SUMMARY_ONLY"
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ImageStorageStatus(StrEnum):
    """person.image_storage_status / character.image_storage_status"""

    PENDING = "PENDING"
    STORED = "STORED"
    FAILED = "FAILED"
    ABSENT = "ABSENT"


class CreditRelation(StrEnum):
    """subject_person_credit.relation"""

    MAIN = "MAIN"
    SUB = "SUB"


class CharacterRelation(StrEnum):
    """subject_character.relation"""

    MAIN = "MAIN"
    SUPPORTING = "SUPPORTING"
    GUEST = "GUEST"


class ActorRelation(StrEnum):
    """character_actor.actor_relation"""

    VA = "VA"
    ACTOR = "ACTOR"


class EntityKind(StrEnum):
    """entity_detail_job.entity_kind / search_index_job.entity_kind"""

    SUBJECT = "SUBJECT"
    EPISODE = "EPISODE"
    PERSON = "PERSON"
    CHARACTER = "CHARACTER"


class JobStatus(StrEnum):
    """entity_detail_job.status / search_index_job.status 的通用状态。

    entity_detail_job 额外使用 RUNNING 和 ABANDONED；
    search_index_job 额外使用 TOMBSTONE。
    """

    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"
    TOMBSTONE = "TOMBSTONE"
