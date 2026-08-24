from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta

from jobs.indexer.repository import IndexJobRepository


class Result:
    def __init__(self, rows=()):
        self._rows = list(rows)

    def mappings(self):
        return self

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.queries: list[tuple[str, dict]] = []

    @contextmanager
    def begin(self):
        yield self

    def execute(self, statement, params=None):
        sql = str(statement)
        self.queries.append((sql, params or {}))
        if "FOR UPDATE SKIP LOCKED" in sql:
            return Result(self.rows)
        return Result()


def test_loading_subject_closes_its_read_transaction_before_status_update():
    """若读取档案遗留事务，随后标记 INDEXED 会在 SQLAlchemy 中拒绝嵌套 begin。"""
    class SubjectResult(Result):
        def one(self):
            return self._rows[0]

        def scalars(self):
            return self

    class TransactionSession:
        def __init__(self):
            self.active = False

        @contextmanager
        def begin(self):
            if self.active:
                raise RuntimeError("transaction already active")
            self.active = True
            try:
                yield self
            finally:
                self.active = False

        def execute(self, statement, _=None):
            self.active = True
            sql = str(statement)
            if "FROM subject s" in sql:
                return SubjectResult([{
                    "subject_id": 42, "title": "测试", "summary": "", "aliases": None,
                    "meta_tags": None, "credits": None, "relations": None, "year": None, "quarter": None,
                    "score": None, "rating_total": None, "collection_total": None,
                    "air_status": "finished", "type": 2, "nsfw": False,
                }])
            return SubjectResult([])

    repo = IndexJobRepository(TransactionSession())
    from jobs.indexer.repository import IndexJob

    token = datetime(2026, 8, 23, 12, 0, 0)
    repo.load_subject(IndexJob(7, 42, "v1", "a" * 64, 1, "RUNNING", token))
    repo.mark_indexed(7, lease_updated_at=token)


def test_claim_batch_only_returns_due_jobs_and_marks_them_running():
    """若领取遗漏到期筛选或未增加 attempts，重试任务会被错误并发执行。"""
    session = FakeSession(
        [
            {
                "id": 7,
                "subject_id": 42,
                "index_version": "v1",
                "content_hash": "a" * 64,
                "attempts": 1,
            }
        ]
    )
    repo = IndexJobRepository(session, now=lambda: datetime(2026, 8, 23, 12, 0, 0))

    jobs = repo.claim_batch("v1", limit=99)

    assert [(job.status, job.attempts, job.index_version) for job in jobs] == [("RUNNING", 2, "v1")]
    select_sql = next(sql for sql, _ in session.queries if "FOR UPDATE SKIP LOCKED" in sql)
    assert "status = 'PENDING'" in select_sql
    assert "status = 'RETRY' AND (next_retry_at IS NULL OR next_retry_at <= :now)" in select_sql
    update_sql, update_params = next(
        (sql, params) for sql, params in session.queries if "status='RUNNING'" in sql and params.get("id") == 7
    )
    assert update_params["id"] == 7
    assert update_params["attempts"] == 2
    assert "LIMIT :limit" in select_sql


def test_claim_batch_recovers_expired_running_lease_before_claiming():
    """若进程在领取后崩溃，过期 RUNNING 必须在同一领取事务中恢复，不能永久卡住。"""
    session = FakeSession(
        [{"id": 8, "subject_id": 43, "index_version": "v1", "content_hash": "b" * 64, "attempts": 1}]
    )
    repo = IndexJobRepository(session, now=lambda: datetime(2026, 8, 23, 12, 0, 0))

    jobs = repo.claim_batch("v1", limit=10)

    recovery_position, recovery = next(
        (position, sql) for position, (sql, _) in enumerate(session.queries) if "LEASE_EXPIRED" in sql
    )
    claim_position = next(position for position, (sql, _) in enumerate(session.queries) if "FOR UPDATE SKIP LOCKED" in sql)
    assert recovery_position < claim_position
    assert "status='RUNNING'" in recovery
    assert "updated_at <= :lease_before" in recovery
    assert jobs[0].attempts == 2


def test_retry_stops_after_fifth_attempt_and_redacts_credentials():
    """若错误路径泄露 token 或第六次继续排队，索引任务会造成安全和成本事故。"""
    session = FakeSession(())
    repo = IndexJobRepository(session, now=lambda: datetime(2026, 8, 23, 12, 0, 0))

    token = datetime(2026, 8, 23, 12, 0, 0)
    repo.mark_retry(9, attempts=5, error=RuntimeError("Authorization: Bearer secret-token\n\x00"), lease_updated_at=token)
    repo.mark_retry(10, attempts=2, error=RuntimeError("server unavailable"), lease_updated_at=token)

    _, failed = next((sql, params) for sql, params in session.queries if params.get("id") == 9)
    _, retry = next((sql, params) for sql, params in session.queries if params.get("id") == 10)
    assert failed["status"] == "FAILED"
    assert "secret-token" not in failed["message"]
    assert "\n" not in failed["message"]
    assert "\x00" not in failed["message"]
    assert retry["status"] == "RETRY"
    assert retry["next_retry_at"] == datetime(2026, 8, 23, 12, 2, 0)


def test_error_redaction_hides_redis_url_secrets_for_empty_user_and_quoted_json_values():
    """若 redis://:secret@ 或 JSON 引号形式漏脱敏，任务错误列会持久化认证信息。"""
    session = FakeSession(())
    repo = IndexJobRepository(session)

    repo.mark_failed(
        12,
        error=RuntimeError('{"url":"redis://:empty-user-secret@cache:6379/0"} redis://user:"quoted-secret"@cache:6379/0'),
        lease_updated_at=datetime(2026, 8, 23, 12, 0, 0),
    )

    _, params = next((sql, params) for sql, params in session.queries if params.get("id") == 12)
    assert "empty-user-secret" not in params["message"]
    assert "quoted-secret" not in params["message"]


def test_renewed_running_lease_is_not_recovered_by_a_later_claim():
    """活跃 worker 续租后，即使批处理超过原始 15 分钟，也不能被另一 worker 回收。"""
    from jobs.indexer.repository import IndexJob

    class LeaseResult(Result):
        def __init__(self, *, rowcount=0, rows=()):
            super().__init__(rows)
            self.rowcount = rowcount

    class LeaseSession:
        def __init__(self, started_at):
            self.status = "RUNNING"
            self.updated_at = started_at

        @contextmanager
        def begin(self):
            yield self

        def execute(self, statement, params=None):
            sql = str(statement)
            params = params or {}
            if "last_error_code='LEASE_EXPIRED'" in sql:
                if self.status == "RUNNING" and self.updated_at <= params["lease_before"]:
                    self.status = "RETRY"
                return LeaseResult()
            if "SET updated_at=:now WHERE id=:id AND status='RUNNING'" in sql:
                if self.status == "RUNNING" and self.updated_at == params["lease_updated_at"]:
                    self.updated_at = params["now"]
                    return LeaseResult(rowcount=1)
                return LeaseResult(rowcount=0)
            if "FOR UPDATE SKIP LOCKED" in sql:
                return LeaseResult(rows=[])
            return LeaseResult()

    started = datetime(2026, 8, 23, 12, 0, 0)
    clock = [started]
    session = LeaseSession(started)
    repo = IndexJobRepository(session, now=lambda: clock[0])
    job = IndexJob(7, 42, "v1", "a" * 64, 1, "RUNNING", started)

    clock[0] = started + timedelta(minutes=10)
    renewed = repo.renew_lease(job.id, lease_updated_at=job.lease_updated_at)
    clock[0] = started + timedelta(minutes=20)
    repo.claim_batch("v1", limit=10)

    assert renewed == started + timedelta(minutes=10)
    assert session.status == "RUNNING"


def test_lost_lease_cannot_overwrite_newer_job_status():
    """旧 worker 失去租约后，mark_indexed 必须返回 False 且不覆盖新 worker 的状态。"""
    class LostLeaseResult(Result):
        rowcount = 0

    class LostLeaseSession(FakeSession):
        def execute(self, statement, params=None):
            sql = str(statement)
            self.queries.append((sql, params or {}))
            return LostLeaseResult()

    token = datetime(2026, 8, 23, 12, 0, 0)
    session = LostLeaseSession(())
    repo = IndexJobRepository(session)

    assert repo.mark_indexed(7, lease_updated_at=token) is False
    sql, params = session.queries[-1]
    assert "status='RUNNING' AND updated_at=:lease_updated_at" in sql
    assert params["lease_updated_at"] == token
