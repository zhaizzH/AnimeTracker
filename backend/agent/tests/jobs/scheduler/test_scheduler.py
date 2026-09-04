"""调度器单元测试。

验证 due_all_jobs 时间窗口、重叠保护、进程重启行为。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from jobs.scheduler.main import (
    ImportScheduler,
    JobScheduler,
    JobType,
    ScheduledImport,
    ScheduledJob,
    due_all_jobs,
    due_jobs,
    next_all_run_at,
    next_run_at,
    SHANGHAI,
)


def _at(hour: int, minute: int = 0, *, weekday: int | None = None, day: int = 1, month: int = 9) -> datetime:
    """构造 Asia/Shanghai 时间点的辅助函数。weekday=None 时不调整日期。"""
    base = datetime(2026, month, day, hour, minute, tzinfo=SHANGHAI)
    if weekday is not None:
        current_weekday = base.weekday()
        delta = (weekday - current_weekday) % 7
        base = base + timedelta(days=delta)
    return base


class TestDueJobs:
    def test_import_at_03_00(self):
        now = _at(3, 0)
        jobs = due_jobs(now)
        assert len(jobs) == 1
        assert jobs[0].mode == "recent"

    def test_weekly_import_sunday_04_00(self):
        # 周日 weekday=6
        now = _at(4, 0, weekday=6)
        jobs = due_jobs(now)
        assert any(j.mode == "weekly_since" for j in jobs)

    def test_quarterly_import_jan_1st_05_00(self):
        now = _at(5, 0, day=1, month=1)
        jobs = due_jobs(now)
        assert any(j.mode == "quarterly_full" for j in jobs)

    def test_no_jobs_at_random_time(self):
        now = _at(14, 30)
        assert due_jobs(now) == []


class TestDueAllJobs:
    def test_indexer_at_02_00_with_version(self):
        now = _at(2, 0)
        jobs = due_all_jobs(now, index_version="v2026-09")
        assert any(j.job_type == JobType.INDEXER for j in jobs)

    def test_indexer_not_scheduled_without_version(self):
        now = _at(2, 0)
        jobs = due_all_jobs(now, index_version="")
        assert not any(j.job_type == JobType.INDEXER for j in jobs)

    def test_backfill_at_06_00(self):
        now = _at(6, 0)
        jobs = due_all_jobs(now)
        assert any(j.job_type == JobType.BACKFILL for j in jobs)

    def test_backfill_args_include_batch_size(self):
        now = _at(6, 0)
        jobs = due_all_jobs(now)
        backfill = next(j for j in jobs if j.job_type == JobType.BACKFILL)
        assert "--batch-size" in backfill.args

    def test_import_at_03_included_in_all(self):
        now = _at(3, 0)
        jobs = due_all_jobs(now)
        assert any(j.job_type == JobType.IMPORT for j in jobs)


class TestNextRunAt:
    def test_returns_future_time(self):
        now = datetime(2026, 9, 3, 10, 0, tzinfo=SHANGHAI)
        result = next_run_at(now)
        assert result > now

    def test_next_all_includes_all_types(self):
        now = datetime(2026, 9, 3, 10, 0, tzinfo=SHANGHAI)
        result = next_all_run_at(now, index_version="v1")
        assert "import" in result
        assert "indexer" in result
        assert "backfill" in result


class TestJobScheduler:
    def test_starts_indexer_at_02(self):
        started: list[ScheduledJob] = []

        def fake_run(job: ScheduledJob) -> int:
            started.append(job)
            return 0

        scheduler = JobScheduler(index_version="v2026-09", run_job=fake_run)
        now = _at(2, 0)
        scheduler.run_due(now)
        assert any(j.job_type == JobType.INDEXER for j in started)

    def test_overlap_protection_skips_running_job(self):
        call_count = 0

        class FakeProcess:
            def poll(self):
                return None  # 仍在运行

        def fake_run(job: ScheduledJob):
            nonlocal call_count
            call_count += 1
            return FakeProcess()

        scheduler = JobScheduler(index_version="v2026-09", run_job=fake_run)
        now = _at(2, 0)
        scheduler.run_due(now)
        assert call_count == 1

        # 同一分钟再次调用不会启动新实例
        scheduler.run_due(now)
        assert call_count == 1

        # 下一天同一时间，前一次仍在运行 → 重叠保护
        next_day = now + timedelta(days=1)
        scheduler.run_due(next_day)
        assert call_count == 1  # 被跳过

    def test_completed_job_allows_next_schedule(self):
        class FakeProcess:
            """首次 poll 即返回 0，模拟任务在两次调度间完成。"""

            def poll(self):
                return 0

        processes: list[FakeProcess] = []

        def fake_run(job: ScheduledJob):
            p = FakeProcess()
            processes.append(p)
            return p

        scheduler = JobScheduler(index_version="v2026-09", run_job=fake_run)
        now = _at(2, 0)
        scheduler.run_due(now)
        assert len(processes) == 1

        # 下一天：_poll_completed 发现已完成 → 移除 → 无重叠 → 启动新任务
        next_day = now + timedelta(days=1)
        scheduler.run_due(next_day)
        assert len(processes) == 2

    def test_deduplication_same_minute(self):
        call_count = 0

        def fake_run(job: ScheduledJob) -> int:
            nonlocal call_count
            call_count += 1
            return 0

        scheduler = JobScheduler(index_version="v2026-09", run_job=fake_run)
        now = _at(2, 0)
        scheduler.run_due(now)
        scheduler.run_due(now)
        assert call_count == 1

    def test_running_jobs_property(self):
        class FakeProcess:
            def poll(self):
                return None

        def fake_run(job: ScheduledJob):
            return FakeProcess()

        scheduler = JobScheduler(index_version="v2026-09", run_job=fake_run)
        now = _at(2, 0)
        scheduler.run_due(now)
        assert "indexer" in scheduler.running_jobs


class TestImportSchedulerBackwardCompat:
    def test_import_scheduler_still_works(self):
        executed: list[ScheduledImport] = []

        def fake_run(job: ScheduledImport) -> int:
            executed.append(job)
            return 0

        scheduler = ImportScheduler(run_importer=fake_run)
        now = _at(3, 0)
        scheduler.run_due(now)
        assert len(executed) == 1
        assert executed[0].mode == "recent"
