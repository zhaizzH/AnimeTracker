from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import os
from statistics import quantiles
import time
import threading
from typing import Any

from dotenv import load_dotenv
import redis
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
from sqlalchemy.orm import Session

from app.shared.observability import log_event

from app.adapters.llm.embeddings import DashScopeEmbeddingClient, EmbeddingRateLimited, EmbeddingUnavailable
from app.adapters.redis.subject_index import RedisSubjectIndex, SubjectIndexDocument
from app.rag.profile import build_subject_profile
from app.rag.schemas import SubjectProfile, SubjectProfileSource
from jobs.importer.db import get_engine
from jobs.indexer.report import build_capacity_report, physical_available_memory, write_report
from jobs.indexer.repository import IndexJob, IndexJobRepository, IndexSubject, RUNNING_LEASE_SECONDS


LEASE_HEARTBEAT_SECONDS = min(60, RUNNING_LEASE_SECONDS // 3)


@dataclass(frozen=True)
class IndexBatchResult:
    claimed: int
    indexed: int
    retried: int
    failed: int
    api_calls: int
    input_characters: int
    durations_ms: tuple[float, ...] = ()


def run_batch(
    *,
    limit: int,
    index_version: str,
    repository: IndexJobRepository,
    embedding_client: Any,
    redis_index: RedisSubjectIndex,
) -> IndexBatchResult:
    """每批至多 10 条；仅在 Redis 写入成功后确认 MySQL 的 INDEXED。"""
    jobs = repository.claim_batch(index_version, min(limit, 10))
    if not jobs:
        return IndexBatchResult(0, 0, 0, 0, 0, 0)
    try:
        redis_index.ensure_version(index_version)
    except Exception as exc:
        if _is_unavailable(exc):
            retry_error = EmbeddingUnavailable("redis unavailable")
            retried = 0
            for job in jobs:
                if repository.mark_retry(
                    job.id, attempts=job.attempts, error=retry_error, lease_updated_at=job.lease_updated_at,
                ):
                    retried += 1
            return IndexBatchResult(len(jobs), 0, retried, 0, 0, 0)
        failed = 0
        for job in jobs:
            if repository.mark_failed(job.id, error=exc, lease_updated_at=job.lease_updated_at):
                failed += 1
        return IndexBatchResult(len(jobs), 0, 0, failed, 0, 0)
    try:
        subjects = [repository.load_subject(job) for job in jobs]
        profiles = [_profile(subject, job) for subject, job in zip(subjects, jobs)]
    except Exception as exc:
        failed = 0
        for job in jobs:
            if repository.mark_failed(job.id, error=exc, lease_updated_at=job.lease_updated_at):
                failed += 1
        return IndexBatchResult(len(jobs), 0, 0, failed, 0, 0)

    texts = [profile.text for profile in profiles]
    started = time.monotonic()
    lease_keeper = _LeaseHeartbeat(repository, jobs)
    lease_keeper.start()
    try:
        vectors = embedding_client.embed_documents(texts)
    except (EmbeddingRateLimited, EmbeddingUnavailable) as exc:
        jobs, lost_job_ids = lease_keeper.stop()
        retried = 0
        for job in jobs:
            if job.id not in lost_job_ids and repository.mark_retry(
                job.id, attempts=job.attempts, error=exc, lease_updated_at=job.lease_updated_at,
            ):
                retried += 1
        return IndexBatchResult(len(jobs), 0, retried, 0, 1, sum(map(len, texts)))
    except Exception as exc:
        jobs, lost_job_ids = lease_keeper.stop()
        failed = 0
        for job in jobs:
            if job.id not in lost_job_ids and repository.mark_failed(job.id, error=exc, lease_updated_at=job.lease_updated_at):
                failed += 1
        return IndexBatchResult(len(jobs), 0, 0, failed, 1, sum(map(len, texts)))
    jobs, lost_job_ids = lease_keeper.stop()

    if len(vectors) != len(jobs):
        error = ValueError("embedding response 条数不匹配")
        failed = 0
        for job in jobs:
            if job.id not in lost_job_ids and repository.mark_failed(
                job.id, error=error, lease_updated_at=job.lease_updated_at,
            ):
                failed += 1
        return IndexBatchResult(len(jobs), 0, 0, failed, 1, sum(map(len, texts)))

    elapsed_ms = (time.monotonic() - started) * 1000
    indexed = retried = failed = 0
    for job, subject, profile, vector in zip(jobs, subjects, profiles, vectors):
        if job.id in lost_job_ids:
            continue
        document = _document(subject, job, profile, vector)
        try:
            redis_index.write(document)
        except Exception as exc:
            if _is_unavailable(exc):
                if repository.mark_retry(
                    job.id, attempts=job.attempts, error=EmbeddingUnavailable("redis unavailable"),
                    lease_updated_at=job.lease_updated_at,
                ):
                    retried += 1
            else:
                if repository.mark_failed(job.id, error=exc, lease_updated_at=job.lease_updated_at):
                    failed += 1
            continue
        if repository.mark_indexed(job.id, lease_updated_at=job.lease_updated_at):
            indexed += 1
    return IndexBatchResult(len(jobs), indexed, retried, failed, 1, sum(map(len, texts)), (elapsed_ms,))


def _profile(subject: IndexSubject, job: IndexJob) -> SubjectProfile:
    built = build_subject_profile(
        SubjectProfileSource(
            title=subject.title,
            summary=subject.summary,
            aliases=subject.aliases,
            meta_tags=subject.meta_tags,
            trusted_tags=subject.trusted_tags,
            credits=subject.credits,
            relations=subject.relations,
        ),
        "text-embedding-v4",
        1024,
    )
    return SubjectProfile(text=built.text, content_hash=job.content_hash, schema_version=built.schema_version)


def _document(subject: IndexSubject, job: IndexJob, profile: SubjectProfile, vector: list[float]) -> SubjectIndexDocument:
    return SubjectIndexDocument(
        subject_id=subject.subject_id,
        index_version=job.index_version,
        profile=profile,
        vector=vector,
        title=subject.title,
        aliases=subject.aliases,
        summary=subject.summary,
        meta_tags=subject.meta_tags,
        trusted_tags=subject.trusted_tags,
        credits=subject.credits,
        year=subject.year,
        quarter=subject.quarter,
        score=subject.score,
        rating_total=subject.rating_total,
        collection_total=subject.collection_total,
        air_status=subject.air_status,
        type=subject.type,
        nsfw=subject.nsfw,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RAG indexer")
    parser.add_argument("--index-version", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    load_dotenv()
    engine = get_engine(
        os.getenv("DB_HOST", "127.0.0.1"), int(os.getenv("DB_PORT", "3306")),
        os.getenv("DB_USER", "root"), os.getenv("DB_PASSWORD", ""), os.getenv("DB_NAME", "anime_tracker"),
    )
    client = redis.Redis.from_url(os.getenv("RAG_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    before_memory = int(client.info("memory").get("used_memory", 0))
    with Session(engine) as session:
        repository = IndexJobRepository(session, lease_session_factory=lambda: Session(engine))
        embedding_client = DashScopeEmbeddingClient(os.getenv("DASHSCOPE_API_KEY", ""))
        index = RedisSubjectIndex(client)
        remaining = max(0, args.limit)
        batches: list[IndexBatchResult] = []
        while remaining:
            result = run_batch(
                limit=min(remaining, 10),
                index_version=args.index_version,
                repository=repository,
                embedding_client=embedding_client,
                redis_index=index,
            )
            batches.append(result)
            remaining -= result.claimed
            if result.claimed == 0:
                break
    total = _combine(batches)
    log_event("rag.index.completed", indexVersion=args.index_version, dimensions=1024, candidateCount=total.indexed, filteredCount=total.failed + total.retried, success=total.failed == 0)
    if args.report:
        after_memory = int(client.info("memory").get("used_memory", 0))
        report = build_capacity_report(
            sample_bytes=max(0, after_memory - before_memory),
            sample_count=total.indexed,
            catalog_count=20_000,
            redis_used_memory=after_memory,
            available_bytes=physical_available_memory(),
        )
        write_report(
            args.report,
            report,
            api_calls=total.api_calls,
            input_characters=total.input_characters,
            indexed=total.indexed,
            retried=total.retried,
            failed=total.failed,
            p50_ms=_percentile(total.durations_ms, 50),
            p95_ms=_percentile(total.durations_ms, 95),
            redis_used_memory_before=before_memory,
            redis_used_memory_after=after_memory,
            redis_memory_delta=max(0, after_memory - before_memory),
            indexVersion=args.index_version,
            embeddingContract={"provider": "dashscope", "model": "text-embedding-v4", "dimensions": 1024, "profileVersion": "subject-profile-v1"},
        )
    return 0


def _combine(batches: list[IndexBatchResult]) -> IndexBatchResult:
    return IndexBatchResult(
        claimed=sum(item.claimed for item in batches),
        indexed=sum(item.indexed for item in batches),
        retried=sum(item.retried for item in batches),
        failed=sum(item.failed for item in batches),
        api_calls=sum(item.api_calls for item in batches),
        input_characters=sum(item.input_characters for item in batches),
        durations_ms=tuple(duration for item in batches for duration in item.durations_ms),
    )


def _percentile(values: tuple[float, ...], percentile: int) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return quantiles(values, n=100, method="inclusive")[percentile - 1]


def _is_unavailable(error: Exception) -> bool:
    return isinstance(error, (ConnectionError, RedisConnectionError, RedisTimeoutError, OSError)) or "unavailable" in str(error).lower()


class _LeaseHeartbeat:
    """使用独立 Session 周期续租，避免长 embedding 调用误触发崩溃回收。"""

    def __init__(
        self,
        repository: IndexJobRepository,
        jobs: list[IndexJob],
        *,
        interval_seconds: float = LEASE_HEARTBEAT_SECONDS,
        stop_timeout_seconds: float = 5,
    ):
        self._repository = repository
        self._jobs = list(jobs)
        self._lost_job_ids: set[int] = set()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._interval_seconds = interval_seconds
        self._stop_timeout_seconds = stop_timeout_seconds
        self._lock = threading.Lock()

    def start(self) -> None:
        if not getattr(self._repository, "supports_lease_heartbeat", False):
            return
        self._thread = threading.Thread(target=self._run, name="rag-index-lease", daemon=True)
        self._thread.start()

    def stop(self) -> tuple[list[IndexJob], set[int]]:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self._stop_timeout_seconds)
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                # 有不可中断的数据库调用时，主线程放弃最终状态写回；后台恢复后也会看到 stop。
                self._lost_job_ids.update(job.id for job in self._jobs)
            return list(self._jobs), set(self._lost_job_ids)

    def _run(self) -> None:
        while not self._stop.wait(self._interval_seconds):
            with self._lock:
                jobs = list(enumerate(self._jobs))
                lost_job_ids = set(self._lost_job_ids)
            for position, job in jobs:
                if job.id in lost_job_ids:
                    continue
                try:
                    renewed = self._repository.renew_lease(job.id, lease_updated_at=job.lease_updated_at)
                except Exception:
                    renewed = None
                if self._stop.is_set():
                    return
                with self._lock:
                    if self._stop.is_set():
                        return
                    if renewed is None:
                        self._lost_job_ids.add(job.id)
                    else:
                        self._jobs[position] = replace(job, lease_updated_at=renewed)


if __name__ == "__main__":
    raise SystemExit(main())
