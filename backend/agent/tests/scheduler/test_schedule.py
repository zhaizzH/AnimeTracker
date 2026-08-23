from __future__ import annotations

from datetime import datetime, timedelta, timezone


SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")


def test_schedule_in_shanghai_timezone():
    from scheduler.main import due_jobs

    jobs = due_jobs(datetime(2026, 10, 1, 5, 0, tzinfo=SHANGHAI))

    assert [job.mode for job in jobs] == ["quarterly_full"]


def test_schedule_uses_recent_weekly_since_and_never_duplicates_a_minute():
    from scheduler.main import ImportScheduler

    calls = []
    scheduler = ImportScheduler(lambda job: calls.append(job) or 0)
    now = datetime(2026, 8, 23, 4, 0, tzinfo=SHANGHAI)  # Sunday

    assert [job.mode for job in scheduler.run_due(now)] == ["weekly_since"]
    assert scheduler.run_due(now) == []
    assert calls[0].args == ("--since", "2025-08-23")


def test_scheduler_runs_when_its_minute_starts_after_second_zero():
    from scheduler.main import due_jobs

    assert [job.mode for job in due_jobs(datetime(2026, 8, 23, 3, 0, 20, tzinfo=SHANGHAI))] == ["recent"]


def test_scheduler_logs_exit_code_and_next_run(monkeypatch, caplog):
    from scheduler.main import ImportScheduler, ScheduledImport

    monkeypatch.setattr("scheduler.main.next_run_at", lambda _now: datetime(2026, 8, 24, 3, 0, tzinfo=SHANGHAI))
    scheduler = ImportScheduler(lambda _job: 9)

    with caplog.at_level("INFO"):
        scheduler.execute(ScheduledImport("recent"), datetime(2026, 8, 23, 3, 0, tzinfo=SHANGHAI))

    assert '"exit_code": 9' in caplog.text
    assert '"next_run_at"' in caplog.text


def test_scheduler_does_not_block_on_long_import_and_logs_after_poll(monkeypatch, caplog):
    from scheduler.main import ImportScheduler, ScheduledImport

    class Process:
        def __init__(self):
            self.exit_code = None

        def poll(self):
            return self.exit_code

    process = Process()
    now = datetime(2026, 8, 23, 3, 0, tzinfo=SHANGHAI)
    scheduler = ImportScheduler(lambda _job: process)
    monkeypatch.setattr("scheduler.main.next_run_at", lambda _now: datetime(2026, 8, 24, 3, 0, tzinfo=SHANGHAI))

    with caplog.at_level("INFO"):
        assert scheduler.execute(ScheduledImport("recent"), now) is None
        assert "import_scheduler_finished" not in caplog.text
        scheduler.poll_completed(now)
        process.exit_code = 7
        scheduler.poll_completed(now)

    assert '"exit_code": 7' in caplog.text


def test_scheduler_starts_importer_with_popen(monkeypatch):
    from scheduler.main import ImportScheduler, ScheduledImport

    captured = {}
    process = object()
    monkeypatch.setattr("scheduler.main.subprocess.Popen", lambda command, cwd: captured.update(command=command, cwd=cwd) or process)

    assert ImportScheduler._start_importer(ScheduledImport("weekly_since", ("--since", "2025-08-23"))) is process
    assert captured["command"][-4:] == ["--mode", "since", "--since", "2025-08-23"]
