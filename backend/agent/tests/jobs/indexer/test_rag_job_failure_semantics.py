"""IndexJobRepository（`job` 表 `type='RAG_INDEX'`）的失败/claim 语义。

回归背景：三张 job 表合并成单表后，原先用 `status='RETRY'` vs `'FAILED'` 区分
「可重试 / 终态」的做法被折叠为单一 `FAILED` + `next_retry_at`。若 claim 谓词把
`next_retry_at IS NULL` 也算作可领，则终态失败（`mark_failed`、退避耗尽的
`mark_retry`、lease 回收耗尽的 `mark_retry`）会被**无退避地**重试到 `max_attempts`，
非可重试错误也会白烧 5 次 embedding 配额。

裁决规则：`FAILED` + `next_retry_at IS NULL` = 终态；`FAILED` + 未来时间 = 待重试。
"""

from __future__ import annotations

from datetime import datetime

from jobs.indexer.repository import IndexJobRepository, MAX_ATTEMPTS

_NOW = datetime(2026, 9, 3, 12, 0, 0)


class _FakeResult:
    def __init__(self, rowcount: int = 1):
        self.rowcount = rowcount


class _FakeMappingResult:
    def __init__(self, rows: list[dict]):
        self._rows = rows
        self.rowcount = len(rows)

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, rows: list[dict] | None = None):
        self.calls: list[tuple[str, dict]] = []
        self._rows = rows or []

    def begin(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, stmt, params=None):
        sql = str(stmt.text) if hasattr(stmt, "text") else str(stmt)
        self.calls.append((sql, params or {}))
        if "FOR UPDATE SKIP LOCKED" in sql:
            return _FakeMappingResult(self._rows)
        return _FakeResult(1)

    def close(self):
        pass


def _repo(session: _FakeSession) -> IndexJobRepository:
    return IndexJobRepository(session, now=lambda: _NOW)


def _claim_sql(session: _FakeSession) -> str:
    return next(sql for sql, _ in session.calls if "FOR UPDATE SKIP LOCKED" in sql)


class TestTerminalFailureIsNotReclaimable:
    def test_claim_predicate_rejects_null_next_retry_at(self):
        """claim 谓词不得把 `next_retry_at IS NULL` 当作可领。

        谓词本身由 MySQL 求值，fake session 不会真正过滤，因此这里断言 SQL 形状。
        """
        session = _FakeSession()
        _repo(session).claim_batch("v1", 10)

        sql = _claim_sql(session)
        assert "next_retry_at IS NULL" not in sql, (
            "claim 把 next_retry_at IS NULL 视为可领，会让 mark_failed 的终态任务无退避重试"
        )
        assert "next_retry_at <= :now" in sql

    def test_claim_is_scoped_to_rag_index_type(self):
        """合并后必须按 type 隔离，否则会误领其他队列的任务。"""
        session = _FakeSession()
        _repo(session).claim_batch("v1", 10)

        assert "type='RAG_INDEX'" in _claim_sql(session)

    def test_mark_failed_writes_terminal_null_retry(self):
        session = _FakeSession()
        _repo(session).mark_failed(1, error=RuntimeError("boom"), lease_updated_at=_NOW)

        sql, _ = session.calls[-1]
        assert "status='FAILED'" in sql
        assert "next_retry_at=NULL" in sql, "mark_failed 必须写终态（NULL），否则会被立即重领"


class TestRetryBackoff:
    def test_mark_retry_schedules_future_retry(self):
        session = _FakeSession()
        _repo(session).mark_retry(1, attempts=1, error=RuntimeError("boom"), lease_updated_at=_NOW)

        _, values = session.calls[-1]
        assert values["next_retry_at"] is not None
        assert values["next_retry_at"] > _NOW, "可重试失败必须退避，不能立即到期"

    def test_mark_retry_exhausted_writes_terminal_null(self):
        session = _FakeSession()
        _repo(session).mark_retry(
            1, attempts=MAX_ATTEMPTS, error=RuntimeError("boom"), lease_updated_at=_NOW
        )

        _, values = session.calls[-1]
        assert values["next_retry_at"] is None, "退避耗尽后应为终态"


class TestLeaseRecovery:
    def test_recovered_rows_are_scheduled_due_not_null(self):
        """过期 lease 回收后，未耗尽的行必须写 `next_retry_at=:now`（非 NULL）才能被重领。

        claim 谓词改成 `next_retry_at <= :now` 之后，回收分支如果再写 NULL，
        被回收的任务就会永久卡住。耗尽行写 NULL 是终态，由 `attempts < max_attempts` 排除。
        """
        session = _FakeSession()
        _repo(session).claim_batch("v1", 10)

        lease_sql = next(sql for sql, _ in session.calls if "LEASE_EXPIRED" in sql)
        assert "next_retry_at=CASE WHEN attempts >= :max_attempts THEN NULL ELSE :now END" in lease_sql
        assert "type='RAG_INDEX'" in lease_sql


class TestClaimReturnsDueJobs:
    def test_claimed_row_is_marked_running(self):
        session = _FakeSession(rows=[{
            "id": 7, "subject_id": 42, "index_version": "v1", "content_hash": "abc", "attempts": 0,
        }])
        jobs = _repo(session).claim_batch("v1", 10)

        assert len(jobs) == 1
        assert jobs[0].subject_id == 42
        assert jobs[0].attempts == 1
        claim_update = next(
            sql for sql, _ in session.calls if sql.startswith("UPDATE job SET status='RUNNING'")
        )
        assert claim_update
