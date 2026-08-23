from importer.main import _sample_ids, parse_args


def test_sample_ids_use_requested_strata_and_limit():
    items = (
        [(i, "1989-01-01") for i in range(1, 80)]
        + [(i, "2000-01-01") for i in range(100, 220)]
        + [(i, "2015-01-01") for i in range(300, 480)]
        + [(i, "2024-01-01") for i in range(500, 750)]
    )

    selected, distribution = _sample_ids(items, limit=500, strata=(50, 100, 150, 200))

    assert len(selected) == 500
    assert distribution == {"before_1990": 50, "1990_2009": 100, "2010_2019": 150, "2020_plus": 200}


def test_sample_ids_borrows_from_adjacent_strata_when_short():
    selected, distribution = _sample_ids([(1, "1980-01-01"), (2, "2024-01-01"), (3, "2024-01-01")], limit=3, strata=(2, 0, 0, 1))

    assert selected == [1, 2, 3]
    assert distribution == {"before_1990": 1, "1990_2009": 0, "2010_2019": 0, "2020_plus": 2}


def test_sample_mode_and_limit_are_internal_cli_options():
    args = parse_args(["--mode", "sample", "--limit", "500"])

    assert args.mode == "sample"
    assert args.limit == 500


def test_import_errors_are_redacted_from_record_and_logs(caplog, monkeypatch):
    from importer import main
    from importer.db import complete_import_record

    secret = "mysql://root:password@db/?token=eyJ.secret.jwt Authorization: Bearer abcdef"
    assert "password" not in main.sanitize_import_error(RuntimeError(secret))
    assert "eyJ.secret.jwt" not in main.sanitize_import_error(RuntimeError(secret))
    assert "abcdef" not in main.sanitize_import_error(RuntimeError(secret))

    class Session:
        def __init__(self):
            self.params = None

        def execute(self, _, params):
            self.params = params

        def rollback(self):
            pass

    session = Session()
    complete_import_record(session, 1, 0, "FAILED", RuntimeError(secret))
    assert "password" not in session.params["error_message"]
    assert "eyJ.secret.jwt" not in session.params["error_message"]
    assert "abcdef" not in session.params["error_message"]

    class Client:
        def get_subject(self, _):
            raise RuntimeError(secret)

    with caplog.at_level("ERROR"):
        assert main.import_single_subject(Client(), Session(), 42, False) == main.OUTCOME_FAILURE
    assert "password" not in caplog.text
    assert "eyJ.secret.jwt" not in caplog.text
    assert "abcdef" not in caplog.text


def test_resume_query_uses_sqlalchemy_text_with_real_session():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session
    from importer.main import OUTCOME_SKIPPED, import_single_subject

    engine = create_engine("sqlite://")
    with Session(engine) as session:
        session.execute(text("CREATE TABLE subject (id INTEGER, bangumi_id INTEGER, import_status INTEGER)"))
        session.execute(text("INSERT INTO subject VALUES (7, 42, 1)"))
        session.commit()

        class Client:
            def get_subject(self, _):
                raise AssertionError("resume should not fetch")

        assert import_single_subject(Client(), session, 42, True) == OUTCOME_SKIPPED
