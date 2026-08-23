from importer.repository import ImportCheckpoint


def test_checkpoint_round_trip_has_only_resume_fields():
    checkpoint = ImportCheckpoint("full", 10, 99, "digest")

    assert checkpoint.as_json() == {
        "mode": "full",
        "offset": 10,
        "lastSubjectId": 99,
        "scannedIdsSha256": "digest",
    }


def test_stale_heartbeat_query_marks_only_running_records():
    from importer.db import fail_stale_running_records

    class Session:
        def __init__(self):
            self.sql = ""

        def execute(self, statement, params):
            self.sql = str(statement)

    session = Session()
    fail_stale_running_records(session)

    assert "status = 'RUNNING'" in session.sql


def test_resume_skips_existing_subject_without_fetching_or_writing():
    from importer.main import OUTCOME_SKIPPED, import_single_subject

    class Result:
        def scalar(self):
            return 7

    class Session:
        def execute(self, *_):
            return Result()

        def rollback(self):
            raise AssertionError("existing subject must not start a write transaction")

    class Client:
        def get_subject(self, *_):
            raise AssertionError("existing subject must not be fetched again")

    assert import_single_subject(Client(), Session(), 42, resume=True) == OUTCOME_SKIPPED


def test_resume_checkpoint_continues_at_saved_batch_offset():
    from importer.main import _resume_batch_ids

    checkpoint = ImportCheckpoint("full", 2, 20, "")
    ids = [10, 20, 30, 40]
    checkpoint = ImportCheckpoint("full", 2, 20, _ids_sha256(ids))

    assert _resume_batch_ids(ids, checkpoint) == [30, 40]


def test_resume_checkpoint_rejects_changed_scan_snapshot():
    from importer.main import _resume_batch_ids

    checkpoint = ImportCheckpoint("full", 1, 10, "old-digest")

    import pytest

    with pytest.raises(ValueError, match="扫描结果"):
        _resume_batch_ids([10, 20], checkpoint)


def test_interrupted_record_reuses_checkpoint_and_continues_without_new_record():
    from importer.db import load_resume_record, resume_import_record
    from importer.main import _resume_batch_ids

    ids = [10, 20, 30]
    checkpoint = {
        "mode": "full",
        "offset": 1,
        "lastSubjectId": 10,
        "scannedIdsSha256": _ids_sha256(ids),
    }

    class Result:
        def mappings(self):
            return self

        def first(self):
            return {"id": 17, "checkpoint_json": checkpoint}

    class Session:
        def __init__(self):
            self.updates = []

        def execute(self, statement, params):
            self.updates.append((str(statement), params))
            return Result()

    session = Session()
    record_id, raw = load_resume_record(session, "full")
    resume_import_record(session, record_id)

    assert record_id == 17
    assert _resume_batch_ids(ids, ImportCheckpoint.from_json(raw)) == [20, 30]
    assert any("status='RUNNING'" in sql for sql, _ in session.updates)


def _ids_sha256(ids):
    import hashlib

    return hashlib.sha256(",".join(map(str, ids)).encode()).hexdigest()
