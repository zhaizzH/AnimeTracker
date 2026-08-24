from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import threading

from app.adapters.llm.embeddings import EmbeddingRateLimited
from app.rag.profile import build_subject_profile
from app.rag.schemas import SubjectProfileSource
from jobs.indexer.main import _LeaseHeartbeat, _profile, run_batch
from jobs.indexer.repository import IndexJob, IndexSubject
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError


@dataclass
class FakeEmbedding:
    vector: list[float] | None = None
    error: Exception | None = None
    calls: list[list[str]] | None = None

    def __post_init__(self):
        self.calls = []

    def embed_documents(self, texts):
        self.calls.append(list(texts))
        if self.error:
            raise self.error
        return [self.vector or [0.0] * 1024 for _ in texts]


class FakeIndex:
    def __init__(self, error: Exception | None = None, ensure_error: Exception | None = None):
        self.error = error
        self.ensure_error = ensure_error
        self.written = []
        self.versions = []

    def ensure_version(self, version):
        self.versions.append(version)
        if self.ensure_error:
            raise self.ensure_error

    def write(self, document):
        if self.error:
            raise self.error
        self.written.append(document)

    def activate(self, _):
        raise AssertionError("worker must not activate alias")


class FakeRepo:
    def __init__(self, jobs):
        self.jobs = jobs
        self.indexed = []
        self.retries = []
        self.failed = []

    def claim_batch(self, version, limit):
        assert limit == 10
        assert version == "v1"
        return self.jobs

    def load_subject(self, job):
        return IndexSubject(job.subject_id, "测试动画", "简介", (), (), (), (), (), 2024, 4, 8.0, 30, 40, "airing", 2, False)

    def mark_indexed(self, job_id, *, lease_updated_at=None):
        self.indexed.append(job_id)
        return True

    def mark_retry(self, job_id, *, attempts, error, lease_updated_at=None):
        self.retries.append((job_id, attempts, type(error).__name__))
        return True

    def mark_failed(self, job_id, *, error, lease_updated_at=None):
        self.failed.append((job_id, type(error).__name__))
        return True


def _job(attempts=1):
    return IndexJob(7, 42, "v1", "a" * 64, attempts, "RUNNING", datetime(2026, 8, 23, 12, 0, 0))


def test_index_profile_uses_the_same_stable_fields_as_importer_profile():
    """若索引器漏掉关系或替换标题，content_hash 对应的向量文本会发生漂移。"""
    subject = IndexSubject(
        42, "原始标题", "简介", ("别名",), ("TV",), ("治愈",), ("导演：甲",), ("续集：乙",),
        2024, 4, 8.0, 30, 40, "airing", 2, False,
    )
    job = _job()

    actual = _profile(subject, job)
    expected = build_subject_profile(
        SubjectProfileSource(
            title="原始标题", summary="简介", aliases=("别名",), meta_tags=("TV",),
            trusted_tags=("治愈",), credits=("导演：甲",), relations=("续集：乙",),
        ),
        "text-embedding-v4", 1024,
    )

    assert actual.text == expected.text


def test_worker_indexes_only_after_redis_write_and_never_activates_alias():
    """若先写 INDEXED，Redis 失败后 MySQL 会错误声称检索资料可用。"""
    repo = FakeRepo([_job()])
    embedding = FakeEmbedding()
    index = FakeIndex()

    result = run_batch(limit=500, index_version="v1", repository=repo, embedding_client=embedding, redis_index=index)

    assert result.indexed == 1
    assert repo.indexed == [7]
    assert len(index.written) == 1
    assert embedding.calls == [["标题：测试动画\n简介：简介"]]
    assert index.versions == ["v1"]


def test_worker_marks_rate_limited_job_for_retry_without_redis_write():
    """若 429 被标记 FAILED 或仍写 Redis，恢复任务会永久丢失或产生无效数据。"""
    repo = FakeRepo([_job(attempts=3)])
    index = FakeIndex()

    result = run_batch(
        limit=10,
        index_version="v1",
        repository=repo,
        embedding_client=FakeEmbedding(error=EmbeddingRateLimited("429")),
        redis_index=index,
    )

    assert result.retried == 1
    assert repo.retries == [(7, 3, "EmbeddingRateLimited")]
    assert index.written == []
    assert repo.indexed == []


def test_worker_keeps_mysql_job_unindexed_when_redis_is_unavailable():
    """若 Redis 故障后仍 INDEXED，后续重跑会跳过真正未索引的条目。"""
    repo = FakeRepo([_job()])

    result = run_batch(
        limit=10,
        index_version="v1",
        repository=repo,
        embedding_client=FakeEmbedding(),
        redis_index=FakeIndex(error=ConnectionError("redis unavailable")),
    )

    assert result.indexed == 0
    assert result.retried == 1
    assert repo.indexed == []
    assert repo.retries == [(7, 1, "EmbeddingUnavailable")]


def test_worker_retries_claimed_jobs_when_creating_redis_version_is_unavailable():
    """若 FT.CREATE 失败后任务仍 RUNNING，崩溃恢复无法再次领取它。"""
    repo = FakeRepo([_job()])

    result = run_batch(
        limit=10,
        index_version="v1",
        repository=repo,
        embedding_client=FakeEmbedding(),
        redis_index=FakeIndex(ensure_error=RedisConnectionError("connection refused")),
    )

    assert result.retried == 1
    assert repo.retries == [(7, 1, "EmbeddingUnavailable")]


def test_worker_retries_claimed_jobs_when_redis_socket_times_out():
    """若 Redis socket timeout 被标记 FAILED，暂时网络抖动会永久丢失索引任务。"""
    repo = FakeRepo([_job()])

    result = run_batch(
        limit=10,
        index_version="v1",
        repository=repo,
        embedding_client=FakeEmbedding(),
        redis_index=FakeIndex(error=RedisTimeoutError("Timeout reading from socket")),
    )

    assert result.retried == 1
    assert repo.retries == [(7, 1, "EmbeddingUnavailable")]


def test_worker_does_not_count_indexed_when_it_loses_the_lease_before_confirmation():
    """旧 worker 失去租约时不得把 Redis 旧写入确认成 MySQL INDEXED。"""
    class LostLeaseRepo(FakeRepo):
        def mark_indexed(self, job_id, *, lease_updated_at=None):
            self.indexed.append(job_id)
            return False

    repo = LostLeaseRepo([_job()])
    result = run_batch(limit=10, index_version="v1", repository=repo, embedding_client=FakeEmbedding(), redis_index=FakeIndex())

    assert result.indexed == 0
    assert repo.indexed == [7]


def test_worker_does_not_count_ensure_failure_when_lost_lease_blocks_retry_update():
    """FT.CREATE 失败后若 lease 已丢失，结果不能谎报已转 RETRY。"""
    class LostLeaseRepo(FakeRepo):
        def mark_retry(self, job_id, *, attempts, error, lease_updated_at=None):
            self.retries.append((job_id, attempts, type(error).__name__))
            return False

    repo = LostLeaseRepo([_job()])
    result = run_batch(
        limit=10, index_version="v1", repository=repo, embedding_client=FakeEmbedding(),
        redis_index=FakeIndex(ensure_error=RedisConnectionError("connection refused")),
    )

    assert result.retried == 0
    assert repo.retries == [(7, 1, "EmbeddingUnavailable")]


def test_worker_does_not_count_profile_failure_when_lost_lease_blocks_failed_update():
    """资料读取失败时 lease 已丢失，结果不能谎报已转 FAILED。"""
    class LostLeaseRepo(FakeRepo):
        def load_subject(self, job):
            raise RuntimeError("profile read failed")

        def mark_failed(self, job_id, *, error, lease_updated_at=None):
            self.failed.append((job_id, type(error).__name__))
            return False

    repo = LostLeaseRepo([_job()])
    result = run_batch(limit=10, index_version="v1", repository=repo, embedding_client=FakeEmbedding(), redis_index=FakeIndex())

    assert result.failed == 0
    assert repo.failed == [(7, "RuntimeError")]


def test_heartbeat_stop_marks_jobs_lost_when_a_renew_call_cannot_finish_in_time():
    """停止等待超时后，主线程必须放弃最终状态写回，不能与后台续租竞争。"""
    entered = threading.Event()
    release = threading.Event()

    class BlockingRepo:
        supports_lease_heartbeat = True

        def renew_lease(self, _job_id, *, lease_updated_at):
            entered.set()
            release.wait(1)
            return lease_updated_at

    keeper = _LeaseHeartbeat(BlockingRepo(), [_job()], interval_seconds=0, stop_timeout_seconds=0.01)
    keeper.start()
    assert entered.wait(0.2)

    _, lost_job_ids = keeper.stop()
    release.set()

    assert lost_job_ids == {7}
