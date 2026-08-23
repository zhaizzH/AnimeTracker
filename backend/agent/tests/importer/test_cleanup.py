from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json

import pytest


class FakeDatabase:
    def __init__(self):
        self.deleted: list[tuple[str, int]] = []
        self.begins = 0

    @contextmanager
    def begin(self):
        self.begins += 1
        yield self

    def execute(self, statement, params=None):
        sql = str(statement)
        if "database_fingerprint" in sql:
            return type("R", (), {"scalar": lambda _: "db-fingerprint"})()
        if sql.startswith("DELETE"):
            self.deleted.append((sql, params["id"]))
        return type("R", (), {})()


class FakeMinio:
    def __init__(self):
        self.deleted: list[str] = []

    def fingerprint(self):
        return "minio-fingerprint"

    def delete_object(self, object_name):
        self.deleted.append(object_name)


def report_payload():
    return {
        "generatedAt": "2026-08-23T00:00:00+00:00",
        "commit": "abc123",
        "dirty": False,
        "databaseFingerprint": "db-fingerprint",
        "minioFingerprint": "minio-fingerprint",
        "counts": {"NON_ANIME": 1, "UNREFERENCED_OBJECT": 1},
        "items": [
            {"category": "NON_ANIME", "action": "DELETE", "target": 7, "details": {}},
            {"category": "UNREFERENCED_OBJECT", "action": "DELETE", "target": "covers/orphan.jpg", "details": {}},
        ],
    }


def test_cleanup_requires_exact_digest_and_performs_zero_writes_on_mismatch(tmp_path):
    from importer.cleanup import ConfirmationMismatch, apply_cleanup_plan, write_cleanup_plan

    path = tmp_path / "quality.json"
    digest = write_cleanup_plan(report_payload(), path)
    db, minio = FakeDatabase(), FakeMinio()

    with pytest.raises(ConfirmationMismatch):
        apply_cleanup_plan(path, "wrong", db, minio, commit="abc123", dirty=False)

    assert db.deleted == []
    assert minio.deleted == []
    assert digest != "wrong"


def test_cleanup_refuses_changed_fingerprint_before_any_write(tmp_path):
    from importer.cleanup import ConfirmationMismatch, apply_cleanup_plan, write_cleanup_plan

    path = tmp_path / "quality.json"
    digest = write_cleanup_plan(report_payload(), path)
    db, minio = FakeDatabase(), FakeMinio()
    minio.fingerprint = lambda: "changed"

    with pytest.raises(ConfirmationMismatch):
        apply_cleanup_plan(path, digest, db, minio, commit="abc123", dirty=False)

    assert db.deleted == []
    assert minio.deleted == []


def test_cleanup_only_deletes_reported_targets_in_independent_transactions(tmp_path):
    from importer.cleanup import apply_cleanup_plan, write_cleanup_plan

    path = tmp_path / "quality.json"
    digest = write_cleanup_plan(report_payload(), path)
    db, minio = FakeDatabase(), FakeMinio()

    result = apply_cleanup_plan(path, digest, db, minio, commit="abc123", dirty=False)

    assert result.applied == 2
    assert db.begins == 1
    assert db.deleted == [("DELETE FROM subject WHERE id=:id", 7)]
    assert minio.deleted == ["covers/orphan.jpg"]


def test_cleanup_closes_the_read_transaction_before_starting_target_transactions(tmp_path):
    from importer.cleanup import apply_cleanup_plan, write_cleanup_plan

    class StrictDatabase(FakeDatabase):
        def __init__(self):
            super().__init__()
            self.read_transaction_open = False

        def execute(self, statement, params=None):
            if "database_fingerprint" in str(statement):
                self.read_transaction_open = True
            return super().execute(statement, params)

        @contextmanager
        def begin(self):
            if self.read_transaction_open:
                raise RuntimeError("read transaction was not closed")
            with super().begin() as session:
                yield session

        def commit(self):
            self.read_transaction_open = False

    path = tmp_path / "quality.json"
    digest = write_cleanup_plan(report_payload(), path)

    assert apply_cleanup_plan(path, digest, StrictDatabase(), FakeMinio(), commit="abc123", dirty=False).applied == 2


def test_cleanup_rejects_an_unrecognized_report_action_before_any_write(tmp_path):
    from importer.cleanup import ConfirmationMismatch, apply_cleanup_plan, write_cleanup_plan

    payload = report_payload()
    payload["items"][0]["action"] = "ERASE_EVERYTHING"
    path = tmp_path / "quality.json"
    content = json.dumps(payload, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    db, minio = FakeDatabase(), FakeMinio()

    with pytest.raises(ConfirmationMismatch):
        apply_cleanup_plan(path, digest, db, minio, commit="abc123", dirty=False)

    assert db.deleted == []
    assert minio.deleted == []
