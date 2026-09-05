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
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.shared.observability import log_event

from app.adapters.llm.embeddings import DashScopeEmbeddingClient, EmbeddingRateLimited, EmbeddingUnavailable
from app.adapters.mysql.import_records import get_engine
from app.adapters.redis.subject_index import RedisSubjectIndex, SubjectIndexDocument
from app.entities.enums import EntityKind
from app.rag.multi_profile import (
    CharacterProfileSource,
    EpisodeProfileSource,
    PersonProfileSource,
    ProfileResult,
    build_character_profile,
    build_episode_profile,
    build_person_profile,
)
from app.rag.profile import build_subject_profile
from app.rag.schemas import SubjectProfile, SubjectProfileSource
from jobs.indexer.entity_index import EntityIndexDocument, RedisEntityIndex
from jobs.indexer.entity_loader import MultiEntityLoader
from jobs.indexer.report import build_capacity_report, physical_available_memory, write_report
from jobs.indexer.repository import IndexJob, IndexJobRepository, IndexSubject, RUNNING_LEASE_SECONDS
from jobs.indexer.search_repository import ClaimedJob, SearchIndexJobRepositoryImpl


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


def run_search_batch(
    *,
    limit: int,
    index_version: str,
    repository: SearchIndexJobRepositoryImpl,
    entity_loader: MultiEntityLoader,
    legacy_repository: IndexJobRepository,
    embedding_client: Any,
    redis_index: RedisEntityIndex,
) -> IndexBatchResult:
    """消费通用 search_index_job，并保留旧 Subject 队列的独立生命周期。

    ``search_index_job`` 的 Subject 任务写入通用实体索引；旧的
    ``rag_index_job`` 仍由 :func:`run_batch` 写入在线 Subject alias。两条队列
    不共享状态，避免新索引失败时误标记旧任务完成。
    """
    remaining = min(max(limit, 0), 10)
    if remaining == 0:
        return IndexBatchResult(0, 0, 0, 0, 0, 0)

    claimed = indexed = retried = failed = api_calls = input_characters = 0
    durations: list[float] = []

    # Tombstone 不需要 embedding，优先处理以避免失效实体长期留在 shadow index。
    try:
        tombstones = repository.tombstone_batch(index_version, remaining)
    except Exception as exc:
        return _search_batch_error(repository, (), exc)
    claimed += len(tombstones)
    remaining -= len(tombstones)
    for job in tombstones:
        try:
            deactivate = getattr(repository, "deactivate_search_document", None)
            if callable(deactivate):
                deactivate(job)
            redis_index.delete(index_version, job.entity_kind, job.entity_id)
            if repository.mark_completed(job.id, claimed_at=job.claimed_at):
                indexed += 1
        except Exception as exc:
            if _mark_search_failure(repository, job, exc):
                if _is_retryable(exc):
                    retried += 1
                else:
                    failed += 1

    if remaining == 0:
        return IndexBatchResult(claimed, indexed, retried, failed, api_calls, input_characters)

    try:
        jobs = repository.claim_batch(remaining, index_version=index_version)
    except Exception as exc:
        return _merge_result(
            IndexBatchResult(claimed, indexed, retried, failed, api_calls, input_characters),
            _search_batch_error(repository, (), exc),
        )
    claimed += len(jobs)
    if not jobs:
        return IndexBatchResult(claimed, indexed, retried, failed, api_calls, input_characters)

    try:
        redis_index.ensure_version(index_version)
    except Exception as exc:
        for job in jobs:
            if _mark_search_failure(repository, job, exc):
                if _is_retryable(exc):
                    retried += 1
                else:
                    failed += 1
        return IndexBatchResult(claimed, indexed, retried, failed, api_calls, input_characters)

    loaded: list[tuple[ClaimedJob, EntityIndexDocument, str]] = []
    for job in jobs:
        try:
            profile, document = _load_search_document(job, entity_loader, legacy_repository)
        except Exception as exc:
            if _is_missing_entity(exc):
                try:
                    redis_index.delete(index_version, job.entity_kind, job.entity_id)
                    if repository.mark_completed(job.id, claimed_at=job.claimed_at):
                        indexed += 1
                except Exception as delete_exc:
                    if _mark_search_failure(repository, job, delete_exc):
                        if _is_retryable(delete_exc):
                            retried += 1
                        else:
                            failed += 1
                continue
            if _mark_search_failure(repository, job, exc):
                if _is_retryable(exc):
                    retried += 1
                else:
                    failed += 1
            continue

        # 绝不把实时 profile 写在旧 hash 下；enqueue 会将当前 claimed job
        # 原子重置为新 hash 的 pending 任务，下一轮再重新生成 embedding。
        if profile.content_hash != job.content_hash:
            try:
                repository.enqueue(
                    job.entity_kind,
                    job.entity_id,
                    job.index_version,
                    profile.content_hash,
                    embedding_model=job.embedding_model or "text-embedding-v4",
                    embedding_dimensions=job.embedding_dimensions or 1024,
                    profile_version=profile.schema_version,
                )
                retried += 1
            except Exception as exc:
                if _mark_search_failure(repository, job, exc):
                    if _is_retryable(exc):
                        retried += 1
                    else:
                        failed += 1
            continue
        loaded.append((job, document, profile.text))

    if not loaded:
        return IndexBatchResult(claimed, indexed, retried, failed, api_calls, input_characters)

    texts = [text_value for _, _, text_value in loaded]
    started = time.monotonic()
    api_calls = 1
    input_characters = sum(map(len, texts))
    try:
        vectors = embedding_client.embed_documents(texts)
    except Exception as exc:
        for job, _, _ in loaded:
            if _mark_search_failure(repository, job, exc):
                if _is_retryable(exc):
                    retried += 1
                else:
                    failed += 1
        return IndexBatchResult(claimed, indexed, retried, failed, api_calls, input_characters)

    if len(vectors) != len(loaded):
        error = ValueError("embedding response 条数不匹配")
        for job, _, _ in loaded:
            if _mark_search_failure(repository, job, error):
                failed += 1
        return IndexBatchResult(claimed, indexed, retried, failed, api_calls, input_characters)

    durations.append((time.monotonic() - started) * 1000)
    for (job, document, _), vector in zip(loaded, vectors):
        try:
            upsert = getattr(repository, "upsert_search_document", None)
            if callable(upsert):
                upsert(job, document)
            redis_index.write(
                EntityIndexDocument(
                    entity_kind=document.entity_kind,
                    entity_id=document.entity_id,
                    index_version=document.index_version,
                    profile=document.profile,
                    vector=vector,
                    name=document.name,
                    aliases=document.aliases,
                    summary=document.summary,
                    subject_id=document.subject_id,
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
            )
            if repository.mark_completed(job.id, claimed_at=job.claimed_at):
                indexed += 1
        except Exception as exc:
            if _mark_search_failure(repository, job, exc):
                if _is_retryable(exc):
                    retried += 1
                else:
                    failed += 1
    return IndexBatchResult(
        claimed, indexed, retried, failed, api_calls, input_characters, tuple(durations)
    )


class _MissingEntity(Exception):
    """任务仍存在但事实实体已经被标记为 inactive 或删除。"""


def _search_batch_error(
    repository: SearchIndexJobRepositoryImpl,
    jobs: tuple[ClaimedJob, ...],
    error: Exception,
) -> IndexBatchResult:
    """把批级错误转换为可观测的失败结果，不伪造已认领数量。"""
    failed = 0
    retried = 0
    for job in jobs:
        if _mark_search_failure(repository, job, error):
            if _is_retryable(error):
                retried += 1
            else:
                failed += 1
    # claim 本身失败时没有 job 可标记，返回非零 failed 供 CLI/报告 fail closed。
    if not jobs:
        failed = 1
    return IndexBatchResult(len(jobs), 0, retried, failed, 0, 0)


def _merge_result(left: IndexBatchResult, right: IndexBatchResult) -> IndexBatchResult:
    """合并 tombstone 与普通任务阶段的批次统计。"""
    return IndexBatchResult(
        claimed=left.claimed + right.claimed,
        indexed=left.indexed + right.indexed,
        retried=left.retried + right.retried,
        failed=left.failed + right.failed,
        api_calls=left.api_calls + right.api_calls,
        input_characters=left.input_characters + right.input_characters,
        durations_ms=left.durations_ms + right.durations_ms,
    )


def _mark_search_failure(
    repository: SearchIndexJobRepositoryImpl,
    job: ClaimedJob,
    error: Exception,
) -> bool:
    code = "REDIS_UNAVAILABLE" if _is_retryable(error) else type(error).__name__[:64]
    return repository.mark_failed(
        job.id,
        error_code=code,
        error_message=str(error),
        claimed_at=job.claimed_at,
    )


def _is_missing_entity(error: Exception) -> bool:
    return isinstance(error, (_MissingEntity, NoResultFound))


def _is_retryable(error: Exception) -> bool:
    if isinstance(error, (EmbeddingRateLimited, EmbeddingUnavailable, RedisConnectionError, RedisTimeoutError, ConnectionError, OSError)):
        return True
    message = str(error).lower()
    return any(token in message for token in ("unavailable", "timeout", "temporarily", "rate limit"))


def _load_search_document(
    job: ClaimedJob,
    entity_loader: MultiEntityLoader,
    legacy_repository: IndexJobRepository,
) -> tuple[ProfileResult | SubjectProfile, EntityIndexDocument]:
    model = job.embedding_model or "text-embedding-v4"
    dimensions = job.embedding_dimensions or 1024
    if job.entity_kind is EntityKind.SUBJECT:
        subject = legacy_repository.load_subject(
            IndexJob(
                id=job.id,
                subject_id=job.entity_id,
                index_version=job.index_version,
                content_hash=job.content_hash,
                attempts=job.attempts,
                status="RUNNING",
                lease_updated_at=job.claimed_at,
            )
        )
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
            model,
            dimensions,
        )
        profile = SubjectProfile(
            text=built.text,
            content_hash=built.content_hash,
            schema_version=built.schema_version,
        )
        document = EntityIndexDocument(
            entity_kind=job.entity_kind,
            entity_id=job.entity_id,
            index_version=job.index_version,
            profile=profile,
            vector=(),
            name=subject.title,
            aliases=subject.aliases,
            summary=subject.summary,
            subject_id=subject.subject_id,
            type=subject.type,
            nsfw=subject.nsfw,
            year=subject.year,
            quarter=subject.quarter,
            score=subject.score,
            rating_total=subject.rating_total,
            collection_total=subject.collection_total,
            air_status=subject.air_status,
        )
        return profile, document

    if job.entity_kind is EntityKind.PERSON:
        person = entity_loader.load_person(job.entity_id)
        if person is None:
            raise _MissingEntity
        profile = build_person_profile(
            PersonProfileSource(
                name=person.name,
                person_type=person.person_type,
                aliases=person.aliases,
                summary=person.summary,
                career=person.career,
                representative_works=person.representative_works,
            ),
            model,
            dimensions,
        )
        document = EntityIndexDocument(
            entity_kind=job.entity_kind,
            entity_id=job.entity_id,
            index_version=job.index_version,
            profile=profile,
            vector=(),
            name=person.name,
            aliases=person.aliases,
            summary=person.summary,
        )
        return profile, document

    if job.entity_kind is EntityKind.CHARACTER:
        character = entity_loader.load_character(job.entity_id)
        if character is None:
            raise _MissingEntity
        profile = build_character_profile(
            CharacterProfileSource(
                name=character.name,
                character_type=character.character_type,
                aliases=character.aliases,
                summary=character.summary,
                appearances=character.appearances,
                voice_actors=character.voice_actors,
            ),
            model,
            dimensions,
        )
        document = EntityIndexDocument(
            entity_kind=job.entity_kind,
            entity_id=job.entity_id,
            index_version=job.index_version,
            profile=profile,
            vector=(),
            name=character.name,
            aliases=character.aliases,
            summary=character.summary,
        )
        return profile, document

    if job.entity_kind is EntityKind.EPISODE:
        episode = entity_loader.load_episode(job.entity_id)
        if episode is None:
            raise _MissingEntity
        profile = build_episode_profile(
            EpisodeProfileSource(
                subject_title=episode.subject_title,
                sort=episode.sort,
                name=episode.name,
                name_cn=episode.name_cn,
                description=episode.description,
                airdate=episode.airdate,
            ),
            model,
            dimensions,
        )
        aliases = (episode.name,) if episode.name and episode.name != episode.name_cn else ()
        document = EntityIndexDocument(
            entity_kind=job.entity_kind,
            entity_id=job.entity_id,
            index_version=job.index_version,
            profile=profile,
            vector=(),
            name=episode.name_cn or episode.name,
            aliases=aliases,
            summary=episode.description,
            subject_id=episode.subject_id,
        )
        return profile, document
    raise ValueError(f"不支持的实体类型: {job.entity_kind}")


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
            upsert = getattr(repository, "upsert_search_document", None)
            if callable(upsert):
                upsert(job, subject, profile)
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
    parser.add_argument(
        "--queue",
        choices=("both", "legacy", "search"),
        default="both",
        help="消费旧 rag_index_job、新 search_index_job 或两者（默认 both）",
    )
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
        embedding_client = DashScopeEmbeddingClient(os.getenv("DASHSCOPE_API_KEY", ""))
        batches: list[IndexBatchResult] = []
        if args.queue in ("both", "search"):
            search_repository = SearchIndexJobRepositoryImpl(
                session, lease_session_factory=lambda: Session(engine)
            )
            multi_loader = MultiEntityLoader(session)
            entity_index = RedisEntityIndex(client)
            remaining = max(0, args.limit)
            while remaining:
                result = run_search_batch(
                    limit=min(remaining, 10),
                    index_version=args.index_version,
                    repository=search_repository,
                    entity_loader=multi_loader,
                    legacy_repository=IndexJobRepository(session),
                    embedding_client=embedding_client,
                    redis_index=entity_index,
                )
                batches.append(result)
                remaining -= result.claimed
                if result.claimed == 0:
                    break

        if args.queue in ("both", "legacy"):
            repository = IndexJobRepository(session, lease_session_factory=lambda: Session(engine))
            index = RedisSubjectIndex(client)
            remaining = max(0, args.limit)
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
            embeddingContract={"provider": "dashscope", "model": "text-embedding-v4", "dimensions": 1024, "profileVersion": "mixed-entity-v1"},
        )
    # 可重试任务仍返回成功；终态失败或批级错误必须让调度器感知并 fail closed。
    return 1 if total.failed else 0


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
