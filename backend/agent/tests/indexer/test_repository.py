from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta

from indexer.repository import IndexJobRepository


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
    from indexer.repository import IndexJob

    repo.load_subject(IndexJob(7, 42, "v1", "a" * 64, 1, "RUNNING"))
    repo.mark_indexed(7)


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
    update_sql, update_params = next((sql, params) for sql, params in session.queries if "status='RUNNING'" in sql)
    assert update_params["id"] == 7
    assert update_params["attempts"] == 2
    assert "LIMIT :limit" in select_sql


def test_retry_stops_after_fifth_attempt_and_redacts_credentials():
    """若错误路径泄露 token 或第六次继续排队，索引任务会造成安全和成本事故。"""
    session = FakeSession(())
    repo = IndexJobRepository(session, now=lambda: datetime(2026, 8, 23, 12, 0, 0))

    repo.mark_retry(9, attempts=5, error=RuntimeError("Authorization: Bearer secret-token\n\x00"))
    repo.mark_retry(10, attempts=2, error=RuntimeError("server unavailable"))

    _, failed = next((sql, params) for sql, params in session.queries if params.get("id") == 9)
    _, retry = next((sql, params) for sql, params in session.queries if params.get("id") == 10)
    assert failed["status"] == "FAILED"
    assert "secret-token" not in failed["message"]
    assert "\n" not in failed["message"]
    assert "\x00" not in failed["message"]
    assert retry["status"] == "RETRY"
    assert retry["next_retry_at"] == datetime(2026, 8, 23, 12, 2, 0)
