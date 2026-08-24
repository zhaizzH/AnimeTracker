import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

from app.admin.import_service import ImportAlreadyRunning
from app.adapters.mysql.import_records import fail_stale_running_records, get_engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

AGENT_ROOT = Path(__file__).resolve().parents[3]
IMPORTER_SCRIPT = AGENT_ROOT / "jobs" / "importer" / "main.py"
IMPORTER_PID_FILE = IMPORTER_SCRIPT.parent / "importer.pid"


class SubprocessImportJobLauncher:
    def __init__(self) -> None:
        # PID 文件只协调本机子进程；多实例部署需要共享的任务协调器。
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None

    def _db_session(self) -> Session:
        return Session(get_engine(
            os.getenv("DB_HOST", "127.0.0.1"), int(os.getenv("DB_PORT", "3306")),
            os.getenv("DB_USER", "root"), os.getenv("DB_PASSWORD", ""),
            os.getenv("DB_NAME", "anime_tracker"),
        ))

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        """pid 对应进程是否存活。Windows 用 OpenProcess+GetExitCodeProcess；os.kill(pid,0) 在 win 上不可靠。"""
        if os.name == "nt":
            import ctypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            h = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return ctypes.get_last_error() == 5  # ERROR_ACCESS_DENIED -> 进程存在但无权打开
            try:
                code = ctypes.c_ulong()
                if not kernel32.GetExitCodeProcess(h, ctypes.byref(code)):
                    return True
                return code.value == 259  # STILL_ACTIVE
            finally:
                kernel32.CloseHandle(h)
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    @staticmethod
    def _read_import_pid() -> int | None:
        try:
            return int(IMPORTER_PID_FILE.read_text().strip())
        except (OSError, ValueError):
            return None

    def _orphan_import_running(self) -> bool:
        """worker 重启丢失 _proc 后，用 PID 文件判断导入子进程是否仍存活。"""
        pid = self._read_import_pid()
        return pid is not None and self._pid_alive(pid)

    def _sweep_stale_records(self) -> None:
        """无存活导入进程时，把遗留 RUNNING 记录翻 FAILED（进程硬退兜底）。"""
        try:
            with self._db_session() as db:
                fail_stale_running_records(db)
                db.commit()
        except Exception as exc:  # DB 不可用时仅告警，不阻塞导入
            logger.warning("清理孤立导入记录失败: %s", exc)

    def sweep_dead_processes(self) -> None:
        with self._lock:
            if self._proc is not None and self._proc.poll() is not None:
                self._proc = None
            if self._proc is None and not self._orphan_import_running():
                self._sweep_stale_records()

    def _spawn(self, args: list[str]) -> None:
        log_file = open(IMPORTER_SCRIPT.parent / "import.log", "ab")
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "jobs.importer.main", *args],
            cwd=AGENT_ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

    def start_import(
        self,
        mode: str,
        *,
        key: str | None = None,
        since: str | None = None,
        workers: int | None = None,
    ) -> None:
        self.sweep_dead_processes()

        args = ["--mode", mode]
        if key:
            args += ["--key", key]
        if since:
            args += ["--since", since]
        if workers is not None:
            args += ["--workers", str(workers)]

        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                raise ImportAlreadyRunning("已有导入任务运行中")
            if self._proc is None and self._orphan_import_running():
                raise ImportAlreadyRunning("已有导入任务运行中")
            self._spawn(args)

        logger.info("已触发导入: %s", " ".join(args))
