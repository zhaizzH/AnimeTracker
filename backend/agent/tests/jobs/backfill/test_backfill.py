"""entity_detail_job repository 与 backfill worker 单元测试。"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.entities.enums import EntityKind, JobStatus
from jobs.backfill.repository import (
    BackfillReport,
    DetailJob,
    EntityDetailJobRepository,
    compute_source_hash,
)


class _Result:
    def __init__(self, scalar_value=None, mappings_result=None, rowcount=1):
        self._scalar_value = scalar_value
        self._mappings_result = mappings_result or []
        self.rowcount = rowcount

    def scalar(self):
        return self._scalar_value

    def mappings(self):
        return self

    def one(self):
        return self._mappings_result[0] if self._mappings_result else {}

    def all(self):
        return self._mappings_result


class _Session:
    def __init__(self, claim_rows=None, report_rows=None, failure_rows=None, stale_rows=None):
        self.calls: list[tuple[str, dict]] = []
        self._claim_rows = claim_rows or []
        self._report_rows = report_rows or []
        self._failure_rows = failure_rows or []
        self._stale_rows = stale_rows or []
        self._call_index = 0
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement, values=None):
        sql = str(statement)
        self.calls.append((sql, values or {}))
        self._call_index += 1

        if "FOR UPDATE SKIP LOCKED" in sql:
            return _Result(mappings_result=self._claim_rows)
        if "GROUP BY status" in sql:
            return _Result(mappings_result=self._report_rows)
        if "last_error_code" in sql and "GROUP BY" in sql:
            return _Result(mappings_result=self._failure_rows)
        if "detail_status <> 'COMPLETE'" in sql:
            return _Result(mappings_result=self._stale_rows)
        if "SELECT attempts" in sql or "SELECT source_hash" in sql:
            return _Result(mappings_result=[{"attempts": 1, "max_attempts": 5, "source_hash": None}])
        if sql.strip().startswith("SELECT"):
            return _Result(mappings_result=[{"entity_kind": "PERSON", "entity_id": 1}])
        return _Result(rowcount=1)

    def begin(self):
        return _TransactionContext()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class _TransactionContext:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestComputeSourceHash:
    def test_deterministic(self):
        data = {"name": "Test", "id": 1}
        assert compute_source_hash(data) == compute_source_hash(data)

    def test_different_data_different_hash(self):
        assert compute_source_hash({"a": 1}) != compute_source_hash({"a": 2})

    def test_key_order_independent(self):
        assert compute_source_hash({"b": 2, "a": 1}) == compute_source_hash({"a": 1, "b": 2})


class TestEntityDetailJobRepository:
    def test_enqueue_inserts(self):
        session = _Session()
        repo = EntityDetailJobRepository(session)
        repo.enqueue(EntityKind.PERSON, 1, 100)
        assert len(session.calls) == 1
        sql, values = session.calls[0]
        assert "INSERT INTO entity_detail_job" in sql
        assert values["entity_kind"] == "PERSON"
        assert values["entity_id"] == 1
        assert values["source_id"] == 100

    def test_claim_batch_returns_jobs(self):
        session = _Session(claim_rows=[
            {"id": 1, "entity_kind": "PERSON", "entity_id": 10, "source_id": 100,
             "status": "PENDING", "attempts": 0, "max_attempts": 5, "checkpoint_json": None},
        ])
        repo = EntityDetailJobRepository(session)
        jobs = repo.claim_batch(5)
        assert len(jobs) == 1
        assert jobs[0].entity_kind == EntityKind.PERSON
        assert jobs[0].source_id == 100
        assert jobs[0].attempts == 1

    def test_claim_batch_empty(self):
        session = _Session(claim_rows=[])
        repo = EntityDetailJobRepository(session)
        jobs = repo.claim_batch(5)
        assert jobs == []

    def test_claim_batch_zero_size(self):
        session = _Session()
        repo = EntityDetailJobRepository(session)
        jobs = repo.claim_batch(0)
        assert jobs == []

    def test_mark_completed(self):
        session = _Session()
        repo = EntityDetailJobRepository(session)
        repo.mark_completed(1, source_hash="abc123")
        # 应当有 UPDATE entity_detail_job 和 UPDATE person 两条 SQL
        update_calls = [c for c in session.calls if "UPDATE" in c[0]]
        assert len(update_calls) >= 1
        assert any("COMPLETED" in c[0] for c in update_calls)

    def test_mark_failed_sets_retry(self):
        session = _Session()
        # 模拟 attempts < max_attempts
        session._claim_rows = []
        repo = EntityDetailJobRepository(session)
        # 需要 mock SELECT attempts 返回
        repo.mark_failed(1, error_code="HTTPError", error_message="404 Not Found")
        update_calls = [c for c in session.calls if "UPDATE" in c[0]]
        assert len(update_calls) >= 1

    def test_pause(self):
        session = _Session()
        repo = EntityDetailJobRepository(session)
        count = repo.pause()
        assert isinstance(count, int)
        assert any("next_retry_at" in c[0] for c in session.calls)

    def test_resume(self):
        session = _Session()
        repo = EntityDetailJobRepository(session)
        count = repo.resume()
        assert isinstance(count, int)
        assert any("next_retry_at=NULL" in c[0] for c in session.calls)

    def test_generate_report(self):
        session = _Session(
            report_rows=[
                {"status": "COMPLETED", "cnt": 80},
                {"status": "PENDING", "cnt": 15},
                {"status": "FAILED", "cnt": 3},
                {"status": "ABANDONED", "cnt": 2},
            ],
            failure_rows=[
                {"last_error_code": "HTTPError", "cnt": 3},
                {"last_error_code": "Timeout", "cnt": 2},
            ],
            stale_rows=[
                {"entity_kind": "PERSON", "cnt": 4},
                {"entity_kind": "CHARACTER", "cnt": 1},
            ],
        )
        repo = EntityDetailJobRepository(session)
        report = repo.generate_report()
        assert isinstance(report, BackfillReport)
        assert report.total_jobs == 100
        assert report.completed == 80
        assert report.coverage_pct == pytest.approx(80.0)
        assert report.failure_reasons["HTTPError"] == 3
        assert report.stale_entities == 5
        assert report.stale_by_kind == {"PERSON": 4, "CHARACTER": 1}
        assert report.as_dict()["coveragePct"] == pytest.approx(80.0)

    def test_save_checkpoint(self):
        session = _Session()
        repo = EntityDetailJobRepository(session)
        repo.save_checkpoint(1, {"offset": 50})
        assert any("checkpoint_json" in c[0] for c in session.calls)


class TestBackfillWorkerIntegration:
    """Worker 逻辑的集成测试（mock client + mock session）。"""

    def test_worker_processes_person_job(self):
        from unittest.mock import MagicMock, patch
        from jobs.backfill.worker import BackfillWorker

        session = _Session(claim_rows=[
            {"id": 1, "entity_kind": "PERSON", "entity_id": 10, "source_id": 100,
             "status": "PENDING", "attempts": 0, "max_attempts": 5, "checkpoint_json": None},
        ])
        repo = EntityDetailJobRepository(session)

        client = MagicMock()
        client.get_person.return_value = {
            "id": 100,
            "name": "Test Person",
            "summary": "A test person",
            "infobox": [{"key": "别名", "value": "TP"}],
            "images": {"large": "http://img.example.com/p.jpg"},
        }

        worker = BackfillWorker(
            client=client,
            repo=repo,
            session=session,
            batch_size=1,
            request_delay=0,
            max_batches=1,
        )
        stats = worker.run()
        assert stats["processed"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 0
        assert session.commits == 1
        client.get_person.assert_called_once_with(100)

    def test_worker_handles_failure_gracefully(self):
        from unittest.mock import MagicMock
        from jobs.backfill.worker import BackfillWorker

        session = _Session(claim_rows=[
            {"id": 2, "entity_kind": "CHARACTER", "entity_id": 20, "source_id": 200,
             "status": "PENDING", "attempts": 0, "max_attempts": 5, "checkpoint_json": None},
        ])
        repo = EntityDetailJobRepository(session)

        client = MagicMock()
        client.get_character.side_effect = RuntimeError("API timeout")

        worker = BackfillWorker(
            client=client,
            repo=repo,
            session=session,
            batch_size=1,
            request_delay=0,
            max_batches=1,
        )
        stats = worker.run()
        assert stats["processed"] == 1
        assert stats["failed"] == 1
        assert stats["completed"] == 0
        assert session.rollbacks == 1
        assert session.commits == 1
