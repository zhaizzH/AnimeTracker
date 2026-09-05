from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import re
from typing import Any, Callable

from sqlalchemy import text


MAX_ATTEMPTS = 5
RUNNING_LEASE_SECONDS = 15 * 60


@dataclass(frozen=True)
class IndexJob:
    id: int
    subject_id: int
    index_version: str
    content_hash: str
    attempts: int
    status: str
    lease_updated_at: datetime | None = None


@dataclass(frozen=True)
class IndexSubject:
    subject_id: int
    title: str
    summary: str
    aliases: tuple[str, ...]
    meta_tags: tuple[str, ...]
    trusted_tags: tuple[str, ...]
    credits: tuple[str, ...]
    relations: tuple[str, ...]
    year: int | None
    quarter: int | None
    score: float | None
    rating_total: int | None
    collection_total: int | None
    air_status: str
    type: int
    nsfw: bool


class IndexJobRepository:
    """MySQL 是索引进度的权威来源，Redis 从不反向决定任务状态。"""

    def __init__(
        self,
        session,
        *,
        now: Callable[[], datetime] = datetime.now,
        trusted_tag_min_count: int | None = None,
        lease_session_factory: Callable[[], Any] | None = None,
    ):
        self._session = session
        self._now = now
        self._lease_session_factory = lease_session_factory
        self._trusted_tag_min_count = trusted_tag_min_count if trusted_tag_min_count is not None else int(
            os.getenv("RAG_TRUSTED_TAG_MIN_COUNT", "100")
        )

    def claim_batch(self, index_version: str, limit: int) -> list[IndexJob]:
        if not index_version:
            raise ValueError("index_version 不能为空")
        if limit < 1:
            return []
        capped_limit = min(limit, 10)
        now = _datetime_seconds(self._now())
        with self._session.begin():
            self._session.execute(
                text(
                    "UPDATE rag_index_job SET "
                    "status=CASE WHEN attempts >= :max_attempts THEN 'FAILED' ELSE 'RETRY' END, "
                    "last_error_code='LEASE_EXPIRED', last_error_message='index worker lease expired', "
                    "next_retry_at=CASE WHEN attempts >= :max_attempts THEN NULL ELSE :now END, "
                    "updated_at=:now WHERE index_version=:index_version AND status='RUNNING' "
                    "AND updated_at <= :lease_before"
                ),
                {
                    "index_version": index_version,
                    "max_attempts": MAX_ATTEMPTS,
                    "now": now,
                    "lease_before": now - timedelta(seconds=RUNNING_LEASE_SECONDS),
                },
            )
            rows = self._session.execute(
                text(
                    "SELECT id, subject_id, index_version, content_hash, attempts "
                    "FROM rag_index_job WHERE index_version=:index_version AND "
                    "(status = 'PENDING' OR (status = 'RETRY' AND (next_retry_at IS NULL OR next_retry_at <= :now))) "
                    "ORDER BY id LIMIT :limit FOR UPDATE SKIP LOCKED"
                ),
                {"index_version": index_version, "now": now, "limit": capped_limit},
            ).mappings().all()
            jobs: list[IndexJob] = []
            for row in rows:
                attempts = int(row["attempts"]) + 1
                job_id = int(row["id"])
                self._session.execute(
                    text(
                        "UPDATE rag_index_job SET status='RUNNING', attempts=:attempts, "
                        "next_retry_at=NULL, updated_at=:now WHERE id=:id"
                    ),
                    {"id": job_id, "attempts": attempts, "now": now},
                )
                jobs.append(
                    IndexJob(
                        job_id, int(row["subject_id"]), str(row["index_version"]), str(row["content_hash"]),
                        attempts, "RUNNING", now,
                    )
                )
        return jobs

    def load_subject(self, job: IndexJob) -> IndexSubject:
        with self._session.begin():
            row = self._session.execute(
                text(
                    "SELECT s.id AS subject_id, s.name AS title, s.summary, "
                    "(SELECT GROUP_CONCAT(name ORDER BY name SEPARATOR '\\n') FROM subject_alias WHERE subject_id=s.id AND source_active=1) AS aliases, "
                    "(SELECT GROUP_CONCAT(name ORDER BY name SEPARATOR '\\n') FROM subject_meta_tag WHERE subject_id=s.id AND source_active=1) AS meta_tags, "
                    "(SELECT GROUP_CONCAT(CONCAT(role, '：', name) ORDER BY sort_order, name SEPARATOR '\\n') FROM subject_credit WHERE subject_id=s.id AND source_active=1) AS credits, "
                    "(SELECT GROUP_CONCAT(CONCAT(sr.relation, '：', related.name) ORDER BY related.name SEPARATOR '\\n') "
                    "FROM subject_relation sr JOIN subject related ON related.id=sr.related_subject_id WHERE sr.subject_id=s.id) AS relations, "
                    "YEAR(s.air_date) AS year, QUARTER(s.air_date) AS quarter, s.score, s.rating_total, s.collection_total, "
                    "CASE "
                    "WHEN s.air_date IS NULL THEN 'unknown' "
                    "WHEN s.air_date > CURDATE() THEN 'upcoming' "
                    "WHEN EXISTS (SELECT 1 FROM episode e WHERE e.subject_id=s.id AND e.status='NA') THEN 'airing' "
                    "ELSE 'finished' "
                    "END AS air_status, "
                    "s.type, s.nsfw FROM subject s WHERE s.id=:subject_id AND s.type=2 AND s.nsfw=0"
                ),
                {"subject_id": job.subject_id},
            ).mappings().one()
            trusted = self._session.execute(
                text(
                    "SELECT current_tag.name FROM subject_tag current_tag JOIN "
                    "(SELECT name, COUNT(DISTINCT subject_id) AS coverage, SUM(count) AS total_count FROM subject_tag GROUP BY name) stats "
                    "ON stats.name=current_tag.name WHERE current_tag.subject_id=:subject_id "
                    "AND CHAR_LENGTH(current_tag.name)<=24 AND stats.coverage>=3 AND stats.total_count>=:min_count "
                    "ORDER BY current_tag.name"
                ),
                {"subject_id": job.subject_id, "min_count": self._trusted_tag_min_count},
            ).scalars().all()
        return IndexSubject(
            int(row["subject_id"]),
            str(row["title"] or ""),
            str(row["summary"] or ""),
            _split(row["aliases"]),
            _split(row["meta_tags"]),
            tuple(str(item) for item in trusted),
            _split(row["credits"]),
            _split(row["relations"]),
            _optional_int(row["year"]),
            _optional_int(row["quarter"]),
            _optional_float(row["score"]),
            _optional_int(row["rating_total"]),
            _optional_int(row["collection_total"]),
            str(row["air_status"] or "unknown"),
            int(row["type"]),
            bool(row["nsfw"]),
        )

    def upsert_search_document(self, job: IndexJob, subject: IndexSubject, profile: Any) -> None:
        """Persist the MySQL lexical shadow before the Vector Set write.

        The projection is rebuildable and never becomes an authority source;
        keeping it in the same worker transaction boundary makes a failed
        Redis write retryable without losing the lexical half.
        """
        now = _datetime_seconds(self._now())
        aliases = "\n".join(subject.aliases)
        lexical_text = "\n".join((profile.text, subject.summary, *subject.meta_tags, *subject.credits, *subject.relations))
        with self._session.begin():
            self._session.execute(
                text(
                    "INSERT INTO search_document "
                    "(entity_kind, entity_id, index_version, profile_version, title, aliases, lexical_text, "
                    "content_hash, source_active, source_fetched_at, created_at, updated_at) "
                    "VALUES ('SUBJECT', :entity_id, :index_version, :profile_version, :title, :aliases, :lexical_text, "
                    ":content_hash, 1, :now, :now, :now) "
                    "ON DUPLICATE KEY UPDATE profile_version=VALUES(profile_version), title=VALUES(title), "
                    "aliases=VALUES(aliases), lexical_text=VALUES(lexical_text), content_hash=VALUES(content_hash), "
                    "source_active=1, source_fetched_at=VALUES(source_fetched_at), updated_at=VALUES(updated_at)"
                ),
                {
                    "entity_id": subject.subject_id,
                    "index_version": job.index_version,
                    "profile_version": profile.schema_version,
                    "title": subject.title[:255],
                    "aliases": aliases,
                    "lexical_text": lexical_text,
                    "content_hash": job.content_hash,
                    "now": now,
                },
            )

    @property
    def supports_lease_heartbeat(self) -> bool:
        return self._lease_session_factory is not None

    def renew_lease(self, job_id: int, *, lease_updated_at: datetime | None) -> datetime | None:
        """在独立短事务中续租；未匹配说明所有权已被回收。"""
        if lease_updated_at is None:
            return None
        now = _datetime_seconds(self._now())
        session = self._lease_session_factory() if self._lease_session_factory is not None else self._session
        try:
            with session.begin():
                result = session.execute(
                    text(
                        "UPDATE rag_index_job SET updated_at=:now WHERE id=:id AND status='RUNNING' "
                        "AND updated_at=:lease_updated_at"
                    ),
                    {"id": job_id, "now": now, "lease_updated_at": lease_updated_at},
                )
            return now if _updated(result) else None
        finally:
            if self._lease_session_factory is not None:
                session.close()

    def mark_indexed(self, job_id: int, *, lease_updated_at: datetime | None) -> bool:
        now = _datetime_seconds(self._now())
        with self._session.begin():
            result = self._session.execute(
                text(
                    "UPDATE rag_index_job SET status='INDEXED', indexed_at=:now, next_retry_at=NULL, "
                    "last_error_code=NULL, last_error_message=NULL, updated_at=:now WHERE id=:id "
                    "AND status='RUNNING' AND updated_at=:lease_updated_at"
                ),
                {"id": job_id, "now": now, "lease_updated_at": lease_updated_at},
            )
        return _updated(result)

    def mark_retry(self, job_id: int, *, attempts: int, error: Exception, lease_updated_at: datetime | None) -> bool:
        now = _datetime_seconds(self._now())
        code, message = _error_details(error)
        if attempts >= MAX_ATTEMPTS:
            status, retry_at = "FAILED", None
        else:
            status = "RETRY"
            retry_at = now + timedelta(seconds=min(3600, 2**attempts * 30))
        with self._session.begin():
            result = self._session.execute(
                text(
                    "UPDATE rag_index_job SET status=:status, last_error_code=:code, last_error_message=:message, "
                    "next_retry_at=:next_retry_at, updated_at=:now WHERE id=:id "
                    "AND status='RUNNING' AND updated_at=:lease_updated_at"
                ),
                {
                    "id": job_id, "status": status, "code": code, "message": message,
                    "next_retry_at": retry_at, "now": now, "lease_updated_at": lease_updated_at,
                },
            )
        return _updated(result)

    def mark_failed(self, job_id: int, *, error: Exception, lease_updated_at: datetime | None) -> bool:
        now = _datetime_seconds(self._now())
        code, message = _error_details(error)
        with self._session.begin():
            result = self._session.execute(
                text(
                    "UPDATE rag_index_job SET status='FAILED', last_error_code=:code, last_error_message=:message, "
                    "next_retry_at=NULL, updated_at=:now WHERE id=:id "
                    "AND status='RUNNING' AND updated_at=:lease_updated_at"
                ),
                {"id": job_id, "code": code, "message": message, "now": now, "lease_updated_at": lease_updated_at},
            )
        return _updated(result)


def _error_details(error: Exception) -> tuple[str, str]:
    message = re.sub(r"[\x00-\x1f\x7f]", " ", str(error))
    message = re.sub(r"(?i)\bauthorization\s*:\s*bearer\s+[^\s,;]+", "Authorization: Bearer ***", message)
    message = re.sub(r"(?i)\bbearer\s+[^\s,;]+", "Bearer ***", message)
    message = re.sub(r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*[^\s,;]+", "***", message)
    message = re.sub(r"//[^@/\s]*:[^@/\s]+@", "//***:***@", message)
    return type(error).__name__[:64], f"{type(error).__name__}: {message}"[:512]


def _split(value: object) -> tuple[str, ...]:
    return tuple(item for item in str(value or "").split("\n") if item)


def _optional_int(value: object) -> int | None:
    return None if value is None else int(value)


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def _datetime_seconds(value: datetime) -> datetime:
    return value.replace(microsecond=0)


def _updated(result: object) -> bool:
    rowcount = getattr(result, "rowcount", None)
    return rowcount is None or rowcount == 1
