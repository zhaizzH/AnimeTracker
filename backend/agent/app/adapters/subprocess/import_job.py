import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from app.admin.import_service import ImportAlreadyRunning
from app.adapters.mysql.import_records import fail_stale_running_records, get_engine
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

AGENT_ROOT = Path(__file__).resolve().parents[3]
IMPORTER_SCRIPT = AGENT_ROOT / "jobs" / "importer" / "main.py"
IMPORTER_PID_FILE = IMPORTER_SCRIPT.parent / "importer.pid"
IMPORT_LOCK_NAME = "animetracker:import"
# 子进程从 Popen 到拿锁写 RUNNING 记录的宽限窗口；窗口内即便查不到锁也拒绝并发
SPAWN_GRACE_SECONDS = 30.0

class SubprocessImportJobLauncher:
    def __init__(self) -> None:
        # PID 文件只协调本机子进程；多实例部署需要共享的任务协调器。
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None
        self._spawned_at = 0.0

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

    @classmethod
    def _orphan_import_running(cls) -> bool:
        """worker 重启丢失 _proc 后，用 PID 文件判断导入子进程是否仍存活。"""
        pid = cls._read_import_pid()
        return pid is not None and cls._pid_alive(pid)

    def _import_lock_held(self) -> bool:
        """子进程是否持有 MySQL 单飞锁 —— 导入是否真在运行的权威信号。

        debugpy 注入的子进程在 main() 返回后仍可能被 pydevd 非守护线程挂住，
        Popen.poll() 永远返回 None；进程存活不等于导入在跑。查询失败时保守
        返回 True（宁可拒绝，也不冒并发导入风险）。
        """
        try:
            with self._db_session() as db:
                return db.execute(
                    text("SELECT IS_USED_LOCK(:name)"), {"name": IMPORT_LOCK_NAME}
                ).scalar() is not None
        except Exception as exc:  # DB 不可用时保守拒绝
            logger.warning("查询导入锁失败: %s", exc)
            return True

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

    def _is_running_locked(self) -> bool:
        """判断是否已有导入在运行。以导入锁为准，进程存活仅作补充。

        句柄存活但导入锁已释放，说明子进程是失败的僵尸（调试器挂住、子进程
        卡在 atexit），丢弃句柄放行后续触发。
        """
        if self._proc is None or self._proc.poll() is not None:
            return self._orphan_import_running()
        if self._import_lock_held():
            return True
        if time.monotonic() - self._spawned_at < SPAWN_GRACE_SECONDS:
            return True  # 刚 spawn，子进程尚未写 RUNNING 记录 / 拿锁
        logger.warning("丢弃僵尸导入进程句柄 pid=%s（导入锁已释放）", self._proc.pid)
        self._proc = None
        return False

    def _spawn(self, args: list[str]) -> None:
        log_file = open(IMPORTER_SCRIPT.parent / "import.log", "ab")
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "jobs.importer.main", *args],
            cwd=AGENT_ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        self._spawned_at = time.monotonic()

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
            if self._is_running_locked():
                raise ImportAlreadyRunning("已有导入任务运行中")
            self._spawn(args)

        logger.info("已触发导入: %s", " ".join(args))
