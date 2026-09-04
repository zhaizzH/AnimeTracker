"""新实体仓储协议。

定义 Person/Character/关系/任务表的最小读写边界；
具体 MySQL 实现位于 app/adapters/mysql/ 或 jobs/ 内部。
importer 和 indexer 通过协议依赖倒置，不直接耦合 SQL 细节。
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from app.entities.enums import EntityKind, JobStatus
from app.entities.models import (
    Character,
    CharacterActor,
    CharacterAlias,
    EntityDetailJob,
    Person,
    PersonAlias,
    SearchIndexJob,
    SubjectCharacter,
    SubjectPersonCredit,
)


@runtime_checkable
class PersonRepository(Protocol):
    """Person 实体的 upsert 与查询边界。"""

    def upsert_person(self, bangumi_person_id: int, *, name: str, person_type: str, **fields) -> int:
        """插入或更新 person，返回本地 person.id。"""
        ...

    def find_by_bangumi_id(self, bangumi_person_id: int) -> Person | None:
        """按上游 ID 查找。"""
        ...

    def upsert_aliases(self, person_id: int, aliases: Sequence[tuple[str, str]]) -> None:
        """replace-set 语义写入别名：upsert 新集合，失效未出现项。"""
        ...


@runtime_checkable
class CharacterRepository(Protocol):
    """Character 实体的 upsert 与查询边界。"""

    def upsert_character(self, bangumi_character_id: int, *, name: str, character_type: str, **fields) -> int:
        """插入或更新 character，返回本地 character.id。"""
        ...

    def find_by_bangumi_id(self, bangumi_character_id: int) -> Character | None:
        """按上游 ID 查找。"""
        ...

    def upsert_aliases(self, character_id: int, aliases: Sequence[tuple[str, str]]) -> None:
        """replace-set 语义写入别名。"""
        ...


@runtime_checkable
class RelationRepository(Protocol):
    """Subject↔Person/Character/Actor 关系的事务性 replace-set 边界。"""

    def replace_credits(
        self, subject_id: int, credits: Sequence[dict]
    ) -> None:
        """完整响应后事务性替换 subject_person_credit；不完整响应不得调用。"""
        ...

    def replace_characters(
        self, subject_id: int, characters: Sequence[dict]
    ) -> None:
        """完整响应后事务性替换 subject_character。"""
        ...

    def replace_actors(
        self, subject_id: int, actors: Sequence[dict]
    ) -> None:
        """完整响应后事务性替换 character_actor（限定于该 subject）。"""
        ...

    def find_subjects_by_person(self, person_id: int) -> list[int]:
        """通过 person_id 查找关联的 subject_id 列表。"""
        ...

    def find_subjects_by_character(self, character_id: int) -> list[int]:
        """通过 character_id 查找关联的 subject_id 列表。"""
        ...


@runtime_checkable
class EntityDetailJobRepository(Protocol):
    """entity_detail_job 的 claim/lease/complete 边界。"""

    def enqueue(self, entity_kind: EntityKind, entity_id: int, source_id: int) -> None:
        """幂等入队：已存在则不重复创建。"""
        ...

    def claim_batch(self, batch_size: int, *, lease_seconds: int = 300) -> list[EntityDetailJob]:
        """认领一批待处理任务（PENDING/FAILED 且 next_retry_at <= now）。"""
        ...

    def mark_completed(self, job_id: int, *, source_hash: str) -> None:
        """标记任务完成。"""
        ...

    def mark_failed(self, job_id: int, *, error_code: str, error_message: str, retry_seconds: int) -> None:
        """标记失败并设置退避重试。"""
        ...

    def mark_abandoned(self, job_id: int, *, error_code: str, error_message: str) -> None:
        """超过最大尝试次数后放弃。"""
        ...


@runtime_checkable
class SearchIndexJobRepository(Protocol):
    """search_index_job 的 outbox 写入与消费边界。"""

    def enqueue(
        self,
        entity_kind: EntityKind,
        entity_id: int,
        index_version: str,
        content_hash: str,
        *,
        embedding_model: str,
        embedding_dimensions: int,
        profile_version: str = "v1",
    ) -> JobStatus:
        """幂等写入索引任务；hash 未变则返回 UNCHANGED 语义（不重复入队）。"""
        ...

    def claim_batch(self, batch_size: int, *, lease_seconds: int = 300) -> list[SearchIndexJob]:
        """认领一批待索引任务。"""
        ...

    def mark_completed(self, job_id: int) -> None:
        """标记索引完成。"""
        ...

    def mark_failed(self, job_id: int, *, error_code: str, error_message: str, retry_seconds: int) -> None:
        """标记失败并设置退避重试。"""
        ...

    def mark_tombstone(self, entity_kind: EntityKind, entity_id: int, index_version: str) -> None:
        """实体被删除时产生 tombstone 工作，消费者据此从索引中移除。"""
        ...
