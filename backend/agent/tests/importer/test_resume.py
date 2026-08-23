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
