"""统一调度器：管理导入、索引和回填子进程的定时运行。

调度策略（Asia/Shanghai）：
- 导入 recent: 每日 03:00
- 导入 weekly_since: 每周日 04:00
- 导入 quarterly_full: 每季度首日 05:00
- 索引 indexer: 每日 02:00（导入完成后）
- 回填 backfill: 每日 06:00（低速批次）

重叠保护：同一 job_type 在前一次未完成时不启动新实例。
进程重启后不恢复上次中断的任务，等待下一个调度窗口。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time


logger = logging.getLogger(__name__)
SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")


class JobType(StrEnum):
    IMPORT = "import"
    INDEXER = "indexer"
    BACKFILL = "backfill"


@dataclass(frozen=True)
class ScheduledImport:
    """向后兼容的导入任务描述。"""

    mode: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScheduledJob:
    """通用调度任务描述。"""

    job_type: JobType
    mode: str = ""
    args: tuple[str, ...] = ()

    @classmethod
    def from_import(cls, imp: ScheduledImport) -> "ScheduledJob":
        return cls(job_type=JobType.IMPORT, mode=imp.mode, args=imp.args)


def due_jobs(now: datetime) -> list[ScheduledImport]:
    """返回此分钟应执行的导入任务（向后兼容）。"""
    local = now.astimezone(SHANGHAI)
    if local.hour == 3 and local.minute == 0:
        return [ScheduledImport("recent")]
    if local.hour == 4 and local.minute == 0 and local.weekday() == 6:
        return [ScheduledImport("weekly_since", ("--since", (local.date() - timedelta(days=365)).isoformat()))]
    if local.hour == 5 and local.minute == 0 and local.day == 1 and local.month in (1, 4, 7, 10):
        return [ScheduledImport("quarterly_full")]
    return []


def due_all_jobs(now: datetime, *, index_version: str = "") -> list[ScheduledJob]:
    """返回此分钟应执行的所有任务（导入 + 索引 + 回填）。"""
    local = now.astimezone(SHANGHAI)
    jobs: list[ScheduledJob] = []

    # 导入任务
    for imp in due_jobs(now):
        jobs.append(ScheduledJob.from_import(imp))

    # 索引任务：每日 02:00
    if local.hour == 2 and local.minute == 0 and index_version:
        jobs.append(ScheduledJob(
            job_type=JobType.INDEXER,
            mode="batch",
            args=("--index-version", index_version, "--limit", "500"),
        ))

    # 回填任务：每日 06:00（低速批次避免争用上游限速）
    if local.hour == 6 and local.minute == 0:
        batch_size = os.getenv("BACKFILL_BATCH_SIZE", "50")
        max_batches = os.getenv("BACKFILL_MAX_BATCHES", "10")
        jobs.append(ScheduledJob(
            job_type=JobType.BACKFILL,
            mode="batch",
            args=("--batch-size", batch_size, "--max-batches", max_batches, "--delay", "1.0"),
        ))

    return jobs


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


def next_all_run_at(now: datetime, *, index_version: str = "") -> dict[str, datetime]:
    """计算各类型任务的下次运行时间。"""
    result: dict[str, datetime] = {
        "import": next_run_at(now),
        "indexer": _candidate_after(now, 2, lambda _: True) if index_version else datetime.max.replace(tzinfo=SHANGHAI),
        "backfill": _candidate_after(now, 6, lambda _: True),
    }
    return result


class ImportScheduler:
    """向后兼容的导入调度器。"""

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
            cwd=Path(__file__).resolve().parents[2],
        )


class JobScheduler:
    """统一调度器：管理导入、索引和回填的重叠保护与子进程生命周期。"""

    def __init__(
        self,
        *,
        index_version: str = "",
        run_job=None,
    ):
        self._index_version = index_version or os.getenv("RAG_INDEX_VERSION", "")
        self._run_job = run_job or self._start_job
        self._executed_minutes: set[tuple[datetime, str, str]] = set()
        self._running: dict[str, tuple[ScheduledJob, Any]] = {}  # key = job_type

    def run_due(self, now: datetime) -> list[ScheduledJob]:
        """轮询完成状态，启动到期任务。"""
        self._poll_completed(now)
        started: list[ScheduledJob] = []
        minute = now.astimezone(SHANGHAI).replace(second=0, microsecond=0)

        for job in due_all_jobs(now, index_version=self._index_version):
            key = (minute, job.job_type.value, job.mode)
            if key in self._executed_minutes:
                continue
            # 重叠保护：同类型任务正在运行时跳过
            if job.job_type.value in self._running:
                logger.warning(json.dumps({
                    "event": "scheduler_overlap_skipped",
                    "job_type": job.job_type.value,
                    "mode": job.mode,
                }, ensure_ascii=False))
                continue
            self._executed_minutes.add(key)
            self._execute(job, now)
            started.append(job)
        return started

    def _execute(self, job: ScheduledJob, now: datetime) -> None:
        process = self._run_job(job)
        if isinstance(process, int):
            # 同步执行完毕
            self._log_finished(job, process, now)
        else:
            self._running[job.job_type.value] = (job, process)

    def _poll_completed(self, now: datetime) -> None:
        completed_keys: list[str] = []
        for key, (job, process) in self._running.items():
            exit_code = process.poll()
            if exit_code is not None:
                self._log_finished(job, exit_code, now)
                completed_keys.append(key)
        for key in completed_keys:
            del self._running[key]

    @property
    def running_jobs(self) -> dict[str, ScheduledJob]:
        return {key: job for key, (job, _) in self._running.items()}

    @staticmethod
    def _log_finished(job: ScheduledJob, exit_code: int, now: datetime) -> None:
        logger.info(json.dumps({
            "event": "scheduler_job_finished",
            "job_type": job.job_type.value,
            "mode": job.mode,
            "exit_code": exit_code,
            "next_runs": {k: v.isoformat() for k, v in next_all_run_at(now, index_version=os.getenv("RAG_INDEX_VERSION", "")).items()},
        }, ensure_ascii=False))

    @staticmethod
    def _start_job(job: ScheduledJob):
        module_map = {
            JobType.IMPORT: "jobs.importer.main",
            JobType.INDEXER: "jobs.indexer.main",
            JobType.BACKFILL: "jobs.backfill.main",
        }
        module = module_map[job.job_type]
        args: list[str] = [sys.executable, "-m", module]
        if job.job_type == JobType.IMPORT:
            importer_mode = {"recent": "recent", "weekly_since": "since", "quarterly_full": "full"}[job.mode]
            args.extend(["--mode", importer_mode, *job.args])
        else:
            args.extend(job.args)
        return subprocess.Popen(
            args,
            cwd=Path(__file__).resolve().parents[2],
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    index_version = os.getenv("RAG_INDEX_VERSION", "")
    scheduler = JobScheduler(index_version=index_version)
    logger.info(json.dumps({
        "event": "scheduler_started",
        "index_version": index_version,
        "next_runs": {k: v.isoformat() for k, v in next_all_run_at(datetime.now(SHANGHAI), index_version=index_version).items()},
    }, ensure_ascii=False))
    while True:
        now = datetime.now(SHANGHAI)
        scheduler.run_due(now)
        time.sleep(max(1, 60 - now.second))


if __name__ == "__main__":
    main()
