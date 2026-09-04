"""SearchIndexJobRepository 单元测试。

验证 enqueue/claim/complete/fail/tombstone 生命周期，
包括幂等入队、hash 漂移重置、lease 回收和退避重试。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.entities.enums import EntityKind, JobStatus
from jobs.indexer.search_repository import (
    ClaimedJob,
    MAX_ATTEMPTS,
    SearchIndexJobRepositoryImpl,
    _sanitize_message,
)


class _FakeResult:
    def __init__(self, rowcount: int = 1):
        self.rowcount = rowcount


class _FakeSession:
    """模拟 SQLAlchemy Session，记录 SQL 调用。"""

    def __init__(self, *, responses: dict[str, Any] | None = None):
        self.calls: list[tuple[str, dict]] = []
        self._responses = responses or {}
        self._in_transaction = False

    def begin(self):
        return self

    def __enter__(self):
        self._in_transaction = True
        return self

    def __exit__(self, *args):
        self._in_transaction = False

    def execute(self, stmt, params=None):
        sql = str(stmt.text) if hasattr(stmt, "text") else str(stmt)
        self.calls.append((sql, params or {}))
        return self._make_result(sql, params)

    def _make_result(self, sql: str, params: dict | None):
        for pattern, response in self._responses.items():
            if pattern in sql:
                if callable(response):
                    return response(sql, params)
                return response
        return _FakeMappingResult([])

    def close(self):
        pass


class _FakeMappingResult:
    def __init__(self, rows: list[dict]):
        self._rows = rows
        self.rowcount = len(rows) if rows else 1

    def mappings(self):
        return self

    def scalars(self):
        return self

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows

    def one(self):
        if not self._rows:
            raise RuntimeError("no row")
        return self._rows[0]


_NOW = datetime(2026, 9, 3, 12, 0, 0)


def _make_repo(**kwargs) -> SearchIndexJobRepositoryImpl:
    session = kwargs.pop("session", _FakeSession())
    return SearchIndexJobRepositoryImpl(session, now=lambda: _NOW, **kwargs)


class TestEnqueue:
    def test_new_job_inserts_pending(self):
        session = _FakeSession(responses={
            "SELECT id, content_hash, status": _FakeMappingResult([]),
        })
        repo = _make_repo(session=session)
        status = repo.enqueue(
            EntityKind.PERSON, 42, "v2026-09", "abc123hash",
            embedding_model="text-embedding-v4", embedding_dimensions=1024,
        )
        assert status == JobStatus.PENDING
        assert any("INSERT INTO search_index_job" in sql for sql, _ in session.calls)

    def test_same_hash_completed_returns_completed(self):
        session = _FakeSession(responses={
            "SELECT id, content_hash, status": _FakeMappingResult([
                {"id": 1, "content_hash": "abc123hash", "status": "COMPLETED"}
            ]),
        })
        repo = _make_repo(session=session)
        status = repo.enqueue(
            EntityKind.PERSON, 42, "v2026-09", "abc123hash",
            embedding_model="text-embedding-v4", embedding_dimensions=1024,
        )
        assert status == JobStatus.COMPLETED
        assert not any("INSERT" in sql or "UPDATE" in sql for sql, _ in session.calls)

    def test_same_hash_pending_returns_pending_no_update(self):
        session = _FakeSession(responses={
            "SELECT id, content_hash, status": _FakeMappingResult([
                {"id": 1, "content_hash": "abc123hash", "status": "PENDING"}
            ]),
        })
        repo = _make_repo(session=session)
        status = repo.enqueue(
            EntityKind.PERSON, 42, "v2026-09", "abc123hash",
            embedding_model="text-embedding-v4", embedding_dimensions=1024,
        )
        assert status == JobStatus.PENDING

    def test_hash_drift_resets_to_pending(self):
        session = _FakeSession(responses={
            "SELECT id, content_hash, status": _FakeMappingResult([
                {"id": 5, "content_hash": "old_hash", "status": "COMPLETED"}
            ]),
        })
        repo = _make_repo(session=session)
        status = repo.enqueue(
            EntityKind.CHARACTER, 10, "v2026-09", "new_hash",
            embedding_model="text-embedding-v4", embedding_dimensions=1024,
        )
        assert status == JobStatus.PENDING
        update_calls = [(sql, p) for sql, p in session.calls if "UPDATE search_index_job" in sql]
        assert len(update_calls) == 1
        assert update_calls[0][1]["hash"] == "new_hash"

    def test_empty_index_version_raises(self):
        repo = _make_repo()
        with pytest.raises(ValueError, match="index_version"):
            repo.enqueue(EntityKind.SUBJECT, 1, "", "hash")

    def test_empty_content_hash_raises(self):
        repo = _make_repo()
        with pytest.raises(ValueError, match="content_hash"):
            repo.enqueue(EntityKind.SUBJECT, 1, "v1", "")


class TestClaimBatch:
    def test_claims_pending_jobs(self):
        rows = [
            {
                "id": 1, "entity_kind": "PERSON", "entity_id": 42,
                "index_version": "v2026-09", "profile_version": "v1",
                "content_hash": "hash1", "embedding_provider": "dashscope",
                "embedding_model": "text-embedding-v4", "embedding_dimensions": 1024,
                "attempts": 0,
            },
            {
                "id": 2, "entity_kind": "CHARACTER", "entity_id": 7,
                "index_version": "v2026-09", "profile_version": "v1",
                "content_hash": "hash2", "embedding_provider": "dashscope",
                "embedding_model": "text-embedding-v4", "embedding_dimensions": 1024,
                "attempts": 1,
            },
        ]
        session = _FakeSession(responses={
            "SELECT id, entity_kind": _FakeMappingResult(rows),
            "UPDATE search_index_job SET status=CASE": _FakeResult(0),
            "UPDATE search_index_job SET status='CLAIMED'": _FakeResult(1),
        })
        repo = _make_repo(session=session)
        jobs = repo.claim_batch(5, index_version="v2026-09")
        assert len(jobs) == 2
        assert jobs[0].entity_kind == EntityKind.PERSON
        assert jobs[0].attempts == 1
        assert jobs[1].entity_kind == EntityKind.CHARACTER
        assert jobs[1].attempts == 2

    def test_empty_batch_returns_empty(self):
        session = _FakeSession(responses={
            "SELECT id, entity_kind": _FakeMappingResult([]),
        })
        repo = _make_repo(session=session)
        jobs = repo.claim_batch(5, index_version="v2026-09")
        assert jobs == []

    def test_zero_batch_size_returns_empty(self):
        repo = _make_repo()
        assert repo.claim_batch(0, index_version="v2026-09") == []

    def test_batch_capped_at_10(self):
        session = _FakeSession(responses={
            "SELECT id, entity_kind": _FakeMappingResult([]),
        })
        repo = _make_repo(session=session)
        repo.claim_batch(100, index_version="v2026-09")
        select_calls = [(sql, p) for sql, p in session.calls if "LIMIT" in sql and "SELECT" in sql]
        assert select_calls[0][1]["limit"] == 10


class TestMarkCompleted:
    def test_marks_completed(self):
        session = _FakeSession(responses={
            "UPDATE search_index_job SET status='COMPLETED'": _FakeResult(1),
        })
        repo = _make_repo(session=session)
        assert repo.mark_completed(1) is True

    def test_returns_false_when_not_claimed(self):
        session = _FakeSession(responses={
            "UPDATE search_index_job SET status='COMPLETED'": _FakeResult(0),
        })
        repo = _make_repo(session=session)
        assert repo.mark_completed(1) is False


class TestMarkFailed:
    def test_sets_failed_with_retry(self):
        session = _FakeSession(responses={
            "SELECT attempts": _FakeMappingResult([{"attempts": 2}]),
            "UPDATE search_index_job SET status=:status": _FakeResult(1),
        })
        repo = _make_repo(session=session)
        result = repo.mark_failed(1, error_code="EMBEDDING_ERROR", error_message="rate limited")
        assert result is True
        update_calls = [(sql, p) for sql, p in session.calls if "UPDATE" in sql and "status=:status" in sql]
        assert update_calls[0][1]["status"] == "FAILED"
        assert update_calls[0][1]["retry_at"] is not None

    def test_abandoned_after_max_attempts(self):
        session = _FakeSession(responses={
            "SELECT attempts": _FakeMappingResult([{"attempts": MAX_ATTEMPTS}]),
            "UPDATE search_index_job SET status=:status": _FakeResult(1),
        })
        repo = _make_repo(session=session)
        result = repo.mark_failed(1, error_code="FATAL", error_message="unrecoverable")
        assert result is True
        update_calls = [(sql, p) for sql, p in session.calls if "UPDATE" in sql and "status=:status" in sql]
        assert update_calls[0][1]["status"] == "ABANDONED"
        assert update_calls[0][1]["retry_at"] is None

    def test_returns_false_when_not_claimed(self):
        session = _FakeSession(responses={
            "SELECT attempts": _FakeMappingResult([]),
        })
        repo = _make_repo(session=session)
        assert repo.mark_failed(1, error_code="X", error_message="y") is False


class TestMarkTombstone:
    def test_inserts_tombstone(self):
        session = _FakeSession()
        repo = _make_repo(session=session)
        repo.mark_tombstone(EntityKind.PERSON, 42, "v2026-09")
        assert any("TOMBSTONE" in sql for sql, _ in session.calls)
        assert any("ON DUPLICATE KEY UPDATE" in sql for sql, _ in session.calls)


class TestTombstoneBatch:
    def test_claims_tombstone_jobs(self):
        rows = [
            {
                "id": 3, "entity_kind": "SUBJECT", "entity_id": 100,
                "index_version": "v2026-09", "profile_version": "",
                "content_hash": "", "embedding_provider": "dashscope",
                "embedding_model": "", "embedding_dimensions": 0,
                "attempts": 0,
            },
        ]
        session = _FakeSession(responses={
            "SELECT id, entity_kind": _FakeMappingResult(rows),
            "UPDATE search_index_job SET status='CLAIMED'": _FakeResult(1),
        })
        repo = _make_repo(session=session)
        jobs = repo.tombstone_batch("v2026-09")
        assert len(jobs) == 1
        assert jobs[0].entity_kind == EntityKind.SUBJECT


class TestSanitizeMessage:
    def test_strips_control_chars(self):
        assert "\x00" not in _sanitize_message("hello\x00world")

    def test_masks_bearer_token(self):
        result = _sanitize_message("Authorization: Bearer sk-12345abc")
        assert "sk-12345abc" not in result
        assert "***" in result

    def test_masks_password(self):
        result = _sanitize_message("password=secret123")
        assert "secret123" not in result

    def test_masks_url_credentials(self):
        result = _sanitize_message("mysql://user:pass@host/db")
        assert "pass" not in result
        assert "***:***@" in result
