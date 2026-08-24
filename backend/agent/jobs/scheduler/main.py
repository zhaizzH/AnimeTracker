"""使用 Asia/Shanghai 固定时间运行导入子进程。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import subprocess
import sys
import time


logger = logging.getLogger(__name__)
SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")


@dataclass(frozen=True)
class ScheduledImport:
    mode: str
    args: tuple[str, ...] = ()


def due_jobs(now: datetime) -> list[ScheduledImport]:
    """返回此分钟应执行的任务；调用方负责同分钟去重。"""
    local = now.astimezone(SHANGHAI)
    if local.hour == 3 and local.minute == 0:
        return [ScheduledImport("recent")]
    if local.hour == 4 and local.minute == 0 and local.weekday() == 6:
        return [ScheduledImport("weekly_since", ("--since", (local.date() - timedelta(days=365)).isoformat()))]
    if local.hour == 5 and local.minute == 0 and local.day == 1 and local.month in (1, 4, 7, 10):
        return [ScheduledImport("quarterly_full")]
    return []


def _candidate_after(now: datetime, hour: int, predicate) -> datetime:
    start = now.astimezone(SHANGHAI).replace(second=0, microsecond=0)
    for days in range(0, 370):
        date = (start + timedelta(days=days)).date()
        candidate = datetime(date.year, date.month, date.day, hour, tzinfo=SHANGHAI)
        if candidate > now and predicate(candidate):
            return candidate
    raise RuntimeError("cannot determine next scheduled import")


def next_run_at(now: datetime) -> datetime:
    """计算下一次任一导入任务，供结构化日志和运维观察使用。"""
    return min(
        _candidate_after(now, 3, lambda _candidate: True),
        _candidate_after(now, 4, lambda candidate: candidate.weekday() == 6),
        _candidate_after(now, 5, lambda candidate: candidate.day == 1 and candidate.month in (1, 4, 7, 10)),
    )


class ImportScheduler:
    def __init__(self, run_importer=None):
        self._run_importer = run_importer or self._start_importer
        self._executed_minutes: set[tuple[datetime, str]] = set()
        self._running: list[tuple[ScheduledImport, object]] = []

    def run_due(self, now: datetime) -> list[ScheduledImport]:
        self.poll_completed(now)
        jobs = []
        minute = now.astimezone(SHANGHAI).replace(second=0, microsecond=0)
        for job in due_jobs(now):
            key = (minute, job.mode)
            if key in self._executed_minutes:
                continue
            self._executed_minutes.add(key)
            self.execute(job, now)
            jobs.append(job)
        return jobs

    def execute(self, job: ScheduledImport, now: datetime) -> int | None:
        process = self._run_importer(job)
        if isinstance(process, int):
            self._log_finished(job, process, now)
            return process
        self._running.append((job, process))
        return None

    def poll_completed(self, now: datetime) -> None:
        still_running = []
        for job, process in self._running:
            exit_code = process.poll()
            if exit_code is None:
                still_running.append((job, process))
                continue
            self._log_finished(job, exit_code, now)
        self._running = still_running

    @staticmethod
    def _log_finished(job: ScheduledImport, exit_code: int, now: datetime) -> None:
        logger.info(json.dumps({
            "event": "import_scheduler_finished",
            "mode": job.mode,
            "exit_code": exit_code,
            "next_run_at": next_run_at(now).isoformat(),
        }, ensure_ascii=False))

    @staticmethod
    def _start_importer(job: ScheduledImport):
        importer_mode = {"recent": "recent", "weekly_since": "since", "quarterly_full": "full"}[job.mode]
        return subprocess.Popen(
            [sys.executable, "-m", "jobs.importer.main", "--mode", importer_mode, *job.args],
            cwd=Path(__file__).resolve().parent.parent,
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    scheduler = ImportScheduler()
    while True:
        now = datetime.now(SHANGHAI)
        scheduler.run_due(now)
        time.sleep(max(1, 60 - now.second))


if __name__ == "__main__":
    main()
