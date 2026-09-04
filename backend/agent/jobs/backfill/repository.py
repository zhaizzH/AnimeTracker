"""entity_detail_job 的 MySQL 仓储实现。

提供 claim/lease、重试退避、checkpoint、暂停/恢复和失败报告。
遵循 indexer repository 相同的 lease 模式：
- claim 使用 FOR UPDATE SKIP LOCKED 避免多 worker 竞争
- lease 通过 updated_at 时间戳实现超时回收
- 失败使用指数退避，超过 max_attempts 后标记 ABANDONED
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from sqlalchemy import text

from app.entities.enums import EntityKind, JobStatus


MAX_ATTEMPTS = 5
LEASE_SECONDS = 10 * 60  # 10 分钟 lease


@dataclass(frozen=True)
class DetailJob:
    """一条待处理的详情回填任务。"""

    id: int
    entity_kind: EntityKind
    entity_id: int
    source_id: int
    status: JobStatus
    attempts: int
    max_attempts: int
    checkpoint_json: str | None = None


@dataclass(frozen=True)
class BackfillReport:
    """回填覆盖率与失败统计。"""

    total_jobs: int
    completed: int
    pending: int
    failed: int
    abandoned: int
    coverage_pct: float
    failure_reasons: dict[str, int]


class EntityDetailJobRepository:
    """entity_detail_job 表的读写边界。"""

    def __init__(
        self,
        session,
        *,
        now: Callable[[], datetime] = datetime.now,
        lease_seconds: int = LEASE_SECONDS,
    ):
        self._session = session
        self._now = now
        self._lease_seconds = lease_seconds

    def enqueue(self, entity_kind: EntityKind, entity_id: int, source_id: int) -> None:
        """幂等入队：已存在则更新 source_id，不重复创建。"""
        now = _dt(self._now())
        self._session.execute(
            text(
                "INSERT INTO entity_detail_job (entity_kind, entity_id, source_id, status, attempts, created_at, updated_at) "
                "VALUES (:entity_kind, :entity_id, :source_id, 'PENDING', 0, :now, :now) "
                "ON DUPLICATE KEY UPDATE source_id=:source_id, updated_at=:now"
            ),
            {"entity_kind": str(entity_kind), "entity_id": entity_id, "source_id": source_id, "now": now},
        )

    def claim_batch(self, batch_size: int = 5) -> list[DetailJob]:
        """认领一批待处理任务。

        选取 PENDING 或 FAILED（且 next_retry_at <= now）的任务，
        使用 FOR UPDATE SKIP LOCKED 避免多 worker 竞争。
        """
        if batch_size < 1:
            return []
        capped = min(batch_size, 20)
        now = _dt(self._now())
        with self._session.begin():
            # 回收过期 lease
            self._session.execute(
                text(
                    "UPDATE entity_detail_job SET "
                    "status=CASE WHEN attempts >= max_attempts THEN 'ABANDONED' ELSE 'FAILED' END, "
                    "last_error_code='LEASE_EXPIRED', last_error_message='backfill worker lease expired', "
                    "next_retry_at=CASE WHEN attempts >= max_attempts THEN NULL ELSE :now END, "
                    "updated_at=:now WHERE status='CLAIMED' AND updated_at <= :lease_before"
                ),
                {"now": now, "lease_before": now - timedelta(seconds=self._lease_seconds)},
            )
            rows = self._session.execute(
                text(
                    "SELECT id, entity_kind, entity_id, source_id, status, attempts, max_attempts, checkpoint_json "
                    "FROM entity_detail_job "
                    "WHERE (status='PENDING' OR (status='FAILED' AND (next_retry_at IS NULL OR next_retry_at <= :now))) "
                    "AND attempts < max_attempts "
                    "ORDER BY id LIMIT :limit FOR UPDATE SKIP LOCKED"
                ),
                {"now": now, "limit": capped},
            ).mappings().all()
            jobs: list[DetailJob] = []
            for row in rows:
                job_id = int(row["id"])
                attempts = int(row["attempts"]) + 1
                self._session.execute(
                    text(
                        "UPDATE entity_detail_job SET status='CLAIMED', attempts=:attempts, "
                        "claimed_at=:now, next_retry_at=NULL, updated_at=:now WHERE id=:id"
                    ),
                    {"id": job_id, "attempts": attempts, "now": now},
                )
                jobs.append(
                    DetailJob(
                        id=job_id,
                        entity_kind=EntityKind(row["entity_kind"]),
                        entity_id=int(row["entity_id"]),
                        source_id=int(row["source_id"]),
                        status=JobStatus.CLAIMED,
                        attempts=attempts,
                        max_attempts=int(row["max_attempts"]),
                        checkpoint_json=row["checkpoint_json"],
                    )
                )
        return jobs

    def mark_completed(self, job_id: int, *, source_hash: str) -> None:
        """在调用方当前事务中标记任务完成，并更新实体状态。"""
        now = _dt(self._now())
        self._session.execute(
            text(
                "UPDATE entity_detail_job SET status='COMPLETED', source_hash=:source_hash, "
                "completed_at=:now, last_error_code=NULL, last_error_message=NULL, updated_at=:now "
                "WHERE id=:id AND status='CLAIMED'"
            ),
            {"id": job_id, "source_hash": source_hash, "now": now},
        )
        job_row = self._session.execute(
            text("SELECT entity_kind, entity_id FROM entity_detail_job WHERE id=:id"),
            {"id": job_id},
        ).mappings().one()
        kind = str(job_row["entity_kind"])
        if kind not in ("PERSON", "CHARACTER"):
            raise ValueError(f"不支持的 entity_kind: {kind}")
        table = "person" if kind == "PERSON" else "character"
        self._session.execute(
            text(f"UPDATE `{table}` SET detail_status='COMPLETE', source_fetched_at=:now, updated_at=:now WHERE id=:id"),
            {"id": int(job_row["entity_id"]), "now": now},
        )

    def mark_failed(self, job_id: int, *, error_code: str, error_message: str) -> None:
        """标记失败并设置指数退避重试。"""
        now = _dt(self._now())
        with self._session.begin():
            row = self._session.execute(
                text("SELECT attempts, max_attempts FROM entity_detail_job WHERE id=:id"),
                {"id": job_id},
            ).mappings().one()
            attempts = int(row["attempts"])
            max_attempts = int(row["max_attempts"])
            if attempts >= max_attempts:
                self._session.execute(
                    text(
                        "UPDATE entity_detail_job SET status='ABANDONED', last_error_code=:code, "
                        "last_error_message=:message, next_retry_at=NULL, updated_at=:now WHERE id=:id"
                    ),
                    {"id": job_id, "code": error_code[:64], "message": _sanitize(error_message)[:512], "now": now},
                )
            else:
                retry_at = now + timedelta(seconds=min(3600, 2**attempts * 60))
                self._session.execute(
                    text(
                        "UPDATE entity_detail_job SET status='FAILED', last_error_code=:code, "
                        "last_error_message=:message, next_retry_at=:retry_at, updated_at=:now WHERE id=:id"
                    ),
                    {"id": job_id, "code": error_code[:64], "message": _sanitize(error_message)[:512], "retry_at": retry_at, "now": now},
                )

    def save_checkpoint(self, job_id: int, checkpoint: dict) -> None:
        """保存回填断点。"""
        now = _dt(self._now())
        self._session.execute(
            text(
                "UPDATE entity_detail_job SET checkpoint_json=CAST(:checkpoint AS JSON), updated_at=:now WHERE id=:id"
            ),
            {"id": job_id, "checkpoint": json.dumps(checkpoint), "now": now},
        )

    def pause(self, entity_kind: EntityKind | None = None) -> int:
        """暂停所有 PENDING 任务（设为 status='PENDING' 但 next_retry_at 远未来）。"""
        now = _dt(self._now())
        far_future = now + timedelta(days=365)
        if entity_kind:
            result = self._session.execute(
                text(
                    "UPDATE entity_detail_job SET next_retry_at=:far, updated_at=:now "
                    "WHERE entity_kind=:kind AND status IN ('PENDING', 'FAILED')"
                ),
                {"far": far_future, "now": now, "kind": str(entity_kind)},
            )
        else:
            result = self._session.execute(
                text(
                    "UPDATE entity_detail_job SET next_retry_at=:far, updated_at=:now "
                    "WHERE status IN ('PENDING', 'FAILED')"
                ),
                {"far": far_future, "now": now},
            )
        return getattr(result, "rowcount", 0) or 0

    def resume(self, entity_kind: EntityKind | None = None) -> int:
        """恢复暂停的任务。"""
        now = _dt(self._now())
        if entity_kind:
            result = self._session.execute(
                text(
                    "UPDATE entity_detail_job SET next_retry_at=NULL, updated_at=:now "
                    "WHERE entity_kind=:kind AND status IN ('PENDING', 'FAILED') AND next_retry_at > :now"
                ),
                {"now": now, "kind": str(entity_kind)},
            )
        else:
            result = self._session.execute(
                text(
                    "UPDATE entity_detail_job SET next_retry_at=NULL, updated_at=:now "
                    "WHERE status IN ('PENDING', 'FAILED') AND next_retry_at > :now"
                ),
                {"now": now},
            )
        return getattr(result, "rowcount", 0) or 0

    def generate_report(self) -> BackfillReport:
        """生成回填覆盖率与失败原因报告。"""
        rows = self._session.execute(
            text(
                "SELECT status, COUNT(*) AS cnt FROM entity_detail_job GROUP BY status"
            ),
        ).mappings().all()
        counts: dict[str, int] = {str(r["status"]): int(r["cnt"]) for r in rows}
        total = sum(counts.values())
        completed = counts.get("COMPLETED", 0)
        failure_rows = self._session.execute(
            text(
                "SELECT last_error_code, COUNT(*) AS cnt FROM entity_detail_job "
                "WHERE status IN ('FAILED', 'ABANDONED') AND last_error_code IS NOT NULL "
                "GROUP BY last_error_code ORDER BY cnt DESC LIMIT 20"
            ),
        ).mappings().all()
        failure_reasons = {str(r["last_error_code"]): int(r["cnt"]) for r in failure_rows}
        return BackfillReport(
            total_jobs=total,
            completed=completed,
            pending=counts.get("PENDING", 0),
            failed=counts.get("FAILED", 0),
            abandoned=counts.get("ABANDONED", 0),
            coverage_pct=(completed / total * 100) if total > 0 else 0.0,
            failure_reasons=failure_reasons,
        )


def compute_source_hash(data: dict) -> str:
    """计算来源数据的确定性哈希。"""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _dt(value: datetime) -> datetime:
    return value.replace(microsecond=0)


def _sanitize(message: str) -> str:
    """脱敏错误信息。"""
    message = re.sub(r"[\x00-\x1f\x7f]", " ", message)
    message = re.sub(r"(?i)\bauthorization\s*:\s*bearer\s+[^\s,;]+", "Authorization: Bearer ***", message)
    message = re.sub(r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*[^\s,;]+", "***", message)
    return message
