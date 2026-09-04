"""通用 search_index_job 仓储实现。

支持 SUBJECT/EPISODE/PERSON/CHARACTER 多实体类型的索引任务管理。
与旧 rag_index_job (仅 Subject) 共存；新实体走 search_index_job，
Subject 仍可通过旧 repository 处理以保持向后兼容。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import re
from typing import Any, Callable

from sqlalchemy import text

from app.entities.enums import EntityKind, JobStatus
from app.entities.models import SearchIndexJob


MAX_ATTEMPTS = 5
RUNNING_LEASE_SECONDS = 15 * 60
DEFAULT_LEASE_SECONDS = int(os.getenv("SEARCH_INDEX_LEASE_SECONDS", "300"))


@dataclass(frozen=True)
class ClaimedJob:
    """认领后的任务快照，包含 lease 标记。"""

    id: int
    entity_kind: EntityKind
    entity_id: int
    index_version: str
    profile_version: str
    content_hash: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    attempts: int
    status: JobStatus
    claimed_at: datetime | None = None


class SearchIndexJobRepositoryImpl:
    """search_index_job 的 MySQL 实现。

    遵循 claim/lease/complete/fail/tombstone 生命周期，
    与 IndexJobRepository (rag_index_job) 模式一致。
    """

    def __init__(
        self,
        session,
        *,
        now: Callable[[], datetime] = datetime.now,
        lease_session_factory: Callable[[], Any] | None = None,
    ):
        self._session = session
        self._now = now
        self._lease_session_factory = lease_session_factory

    def enqueue(
        self,
        entity_kind: EntityKind,
        entity_id: int,
        index_version: str,
        content_hash: str,
        *,
        embedding_model: str = "text-embedding-v4",
        embedding_dimensions: int = 1024,
        profile_version: str = "v1",
    ) -> JobStatus:
        """幂等写入索引任务；hash 未变返回 COMPLETED（不重复入队）。"""
        if not index_version:
            raise ValueError("index_version 不能为空")
        if not content_hash:
            raise ValueError("content_hash 不能为空")
        now = _datetime_seconds(self._now())
        with self._session.begin():
            existing = self._session.execute(
                text(
                    "SELECT id, content_hash, status FROM search_index_job "
                    "WHERE entity_kind=:kind AND entity_id=:entity_id AND index_version=:version"
                ),
                {"kind": str(entity_kind), "entity_id": entity_id, "version": index_version},
            ).mappings().first()

            if existing is not None:
                if str(existing["content_hash"]) == content_hash and str(existing["status"]) == "COMPLETED":
                    return JobStatus.COMPLETED
                if str(existing["content_hash"]) == content_hash and str(existing["status"]) in ("PENDING", "CLAIMED"):
                    return JobStatus.PENDING
                # hash 变化：重新入队
                self._session.execute(
                    text(
                        "UPDATE search_index_job SET content_hash=:hash, profile_version=:pv, "
                        "embedding_model=:model, embedding_dimensions=:dims, "
                        "status='PENDING', attempts=0, last_error_code=NULL, last_error_message=NULL, "
                        "next_retry_at=NULL, claimed_at=NULL, indexed_at=NULL, updated_at=:now "
                        "WHERE id=:id"
                    ),
                    {
                        "id": int(existing["id"]), "hash": content_hash, "pv": profile_version,
                        "model": embedding_model, "dims": embedding_dimensions, "now": now,
                    },
                )
                return JobStatus.PENDING

            self._session.execute(
                text(
                    "INSERT INTO search_index_job "
                    "(entity_kind, entity_id, index_version, profile_version, content_hash, "
                    "embedding_provider, embedding_model, embedding_dimensions, status, attempts, "
                    "max_attempts, created_at, updated_at) "
                    "VALUES (:kind, :entity_id, :version, :pv, :hash, "
                    "'dashscope', :model, :dims, 'PENDING', 0, "
                    ":max_attempts, :now, :now)"
                ),
                {
                    "kind": str(entity_kind), "entity_id": entity_id, "version": index_version,
                    "pv": profile_version, "hash": content_hash, "model": embedding_model,
                    "dims": embedding_dimensions, "max_attempts": MAX_ATTEMPTS, "now": now,
                },
            )
            return JobStatus.PENDING

    def claim_batch(
        self, batch_size: int, *, index_version: str, lease_seconds: int | None = None
    ) -> list[ClaimedJob]:
        """认领一批待索引任务，处理过期 lease 恢复。"""
        if batch_size < 1:
            return []
        capped = min(batch_size, 10)
        lease_sec = lease_seconds or DEFAULT_LEASE_SECONDS
        now = _datetime_seconds(self._now())
        with self._session.begin():
            # 回收过期 lease
            self._session.execute(
                text(
                    "UPDATE search_index_job SET "
                    "status=CASE WHEN attempts >= :max_attempts THEN 'FAILED' ELSE 'PENDING' END, "
                    "last_error_code='LEASE_EXPIRED', "
                    "last_error_message='search index worker lease expired', "
                    "next_retry_at=CASE WHEN attempts >= :max_attempts THEN NULL ELSE :now END, "
                    "updated_at=:now "
                    "WHERE index_version=:version AND status='CLAIMED' "
                    "AND updated_at <= :lease_before"
                ),
                {
                    "max_attempts": MAX_ATTEMPTS, "now": now,
                    "version": index_version,
                    "lease_before": now - timedelta(seconds=lease_sec),
                },
            )
            rows = self._session.execute(
                text(
                    "SELECT id, entity_kind, entity_id, index_version, profile_version, "
                    "content_hash, embedding_provider, embedding_model, embedding_dimensions, attempts "
                    "FROM search_index_job WHERE index_version=:version AND "
                    "(status='PENDING' OR (status='FAILED' AND attempts < :max_attempts "
                    "AND (next_retry_at IS NULL OR next_retry_at <= :now))) "
                    "ORDER BY id LIMIT :limit FOR UPDATE SKIP LOCKED"
                ),
                {"version": index_version, "max_attempts": MAX_ATTEMPTS, "now": now, "limit": capped},
            ).mappings().all()

            jobs: list[ClaimedJob] = []
            for row in rows:
                job_id = int(row["id"])
                attempts = int(row["attempts"]) + 1
                self._session.execute(
                    text(
                        "UPDATE search_index_job SET status='CLAIMED', attempts=:attempts, "
                        "claimed_at=:now, next_retry_at=NULL, updated_at=:now WHERE id=:id"
                    ),
                    {"id": job_id, "attempts": attempts, "now": now},
                )
                jobs.append(
                    ClaimedJob(
                        id=job_id,
                        entity_kind=EntityKind(str(row["entity_kind"])),
                        entity_id=int(row["entity_id"]),
                        index_version=str(row["index_version"]),
                        profile_version=str(row["profile_version"]),
                        content_hash=str(row["content_hash"]),
                        embedding_provider=str(row["embedding_provider"]),
                        embedding_model=str(row["embedding_model"]),
                        embedding_dimensions=int(row["embedding_dimensions"]),
                        attempts=attempts,
                        status=JobStatus.CLAIMED,
                        claimed_at=now,
                    )
                )
        return jobs

    def mark_completed(self, job_id: int, *, claimed_at: datetime | None = None) -> bool:
        """标记索引完成。"""
        now = _datetime_seconds(self._now())
        with self._session.begin():
            result = self._session.execute(
                text(
                    "UPDATE search_index_job SET status='COMPLETED', indexed_at=:now, "
                    "last_error_code=NULL, last_error_message=NULL, updated_at=:now "
                    "WHERE id=:id AND status='CLAIMED'"
                ),
                {"id": job_id, "now": now},
            )
        return _updated(result)

    def mark_failed(
        self, job_id: int, *, error_code: str, error_message: str, retry_seconds: int = 0
    ) -> bool:
        """标记失败并设置退避重试；超过最大次数则 ABANDONED。"""
        now = _datetime_seconds(self._now())
        with self._session.begin():
            row = self._session.execute(
                text("SELECT attempts FROM search_index_job WHERE id=:id AND status='CLAIMED'"),
                {"id": job_id},
            ).mappings().first()
            if row is None:
                return False
            attempts = int(row["attempts"])
            if attempts >= MAX_ATTEMPTS:
                status, next_retry = "ABANDONED", None
            else:
                status = "FAILED"
                next_retry = now + timedelta(seconds=retry_seconds or min(3600, 2**attempts * 30))
            result = self._session.execute(
                text(
                    "UPDATE search_index_job SET status=:status, last_error_code=:code, "
                    "last_error_message=:message, next_retry_at=:retry_at, updated_at=:now "
                    "WHERE id=:id AND status='CLAIMED'"
                ),
                {
                    "id": job_id, "status": status,
                    "code": error_code[:64], "message": _sanitize_message(error_message)[:512],
                    "retry_at": next_retry, "now": now,
                },
            )
        return _updated(result)

    def mark_tombstone(self, entity_kind: EntityKind, entity_id: int, index_version: str) -> None:
        """实体被删除时产生 tombstone 工作，消费者据此从索引中移除。"""
        now = _datetime_seconds(self._now())
        with self._session.begin():
            self._session.execute(
                text(
                    "INSERT INTO search_index_job "
                    "(entity_kind, entity_id, index_version, profile_version, content_hash, "
                    "embedding_provider, embedding_model, embedding_dimensions, status, attempts, "
                    "max_attempts, created_at, updated_at) "
                    "VALUES (:kind, :entity_id, :version, '', '', "
                    "'dashscope', '', 0, 'TOMBSTONE', 0, :max_attempts, :now, :now) "
                    "ON DUPLICATE KEY UPDATE status='TOMBSTONE', content_hash='', "
                    "updated_at=:now, last_error_code=NULL, last_error_message=NULL"
                ),
                {
                    "kind": str(entity_kind), "entity_id": entity_id,
                    "version": index_version, "max_attempts": MAX_ATTEMPTS, "now": now,
                },
            )

    def pending_count(self, index_version: str) -> int:
        """返回指定版本的待处理任务数量。"""
        with self._session.begin():
            row = self._session.execute(
                text(
                    "SELECT COUNT(*) AS cnt FROM search_index_job "
                    "WHERE index_version=:version AND status IN ('PENDING', 'FAILED')"
                ),
                {"version": index_version},
            ).mappings().first()
        return int(row["cnt"]) if row else 0

    def tombstone_batch(self, index_version: str, limit: int = 10) -> list[ClaimedJob]:
        """认领 tombstone 任务用于从索引中删除文档。"""
        if limit < 1:
            return []
        now = _datetime_seconds(self._now())
        with self._session.begin():
            rows = self._session.execute(
                text(
                    "SELECT id, entity_kind, entity_id, index_version, profile_version, "
                    "content_hash, embedding_provider, embedding_model, embedding_dimensions, attempts "
                    "FROM search_index_job WHERE index_version=:version AND status='TOMBSTONE' "
                    "ORDER BY id LIMIT :limit FOR UPDATE SKIP LOCKED"
                ),
                {"version": index_version, "limit": min(limit, 50)},
            ).mappings().all()
            jobs: list[ClaimedJob] = []
            for row in rows:
                job_id = int(row["id"])
                self._session.execute(
                    text(
                        "UPDATE search_index_job SET status='CLAIMED', updated_at=:now WHERE id=:id"
                    ),
                    {"id": job_id, "now": now},
                )
                jobs.append(
                    ClaimedJob(
                        id=job_id,
                        entity_kind=EntityKind(str(row["entity_kind"])),
                        entity_id=int(row["entity_id"]),
                        index_version=str(row["index_version"]),
                        profile_version=str(row["profile_version"]),
                        content_hash="",
                        embedding_provider=str(row["embedding_provider"]),
                        embedding_model=str(row["embedding_model"]),
                        embedding_dimensions=int(row["embedding_dimensions"]),
                        attempts=int(row["attempts"]),
                        status=JobStatus.CLAIMED,
                        claimed_at=now,
                    )
                )
        return jobs


def _sanitize_message(message: str) -> str:
    """移除控制字符和敏感凭据。"""
    result = re.sub(r"[\x00-\x1f\x7f]", " ", message)
    result = re.sub(r"(?i)\bauthorization\s*:\s*bearer\s+[^\s,;]+", "Authorization: Bearer ***", result)
    result = re.sub(r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*[^\s,;]+", "***", result)
    result = re.sub(r"//[^@/\s]*:[^@/\s]+@", "//***:***@", result)
    return result


def _datetime_seconds(value: datetime) -> datetime:
    return value.replace(microsecond=0)


def _updated(result: object) -> bool:
    rowcount = getattr(result, "rowcount", None)
    return rowcount is None or rowcount == 1
