"""importer 子进程管理与导入触发（无 HTTP 语义）。

单一真相源：HTTP 端点（app/api/import_api）与 admin 领域工具（app/agent/admin/tools/import_tool）
都依赖本模块触发导入，保证单飞门禁被共享——否则工具与端点并发会开出双导入。
"""
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

from sqlalchemy.orm import Session

from importer.db import fail_stale_running_records as _flip_running, get_engine

logger = logging.getLogger(__name__)

AGENT_ROOT = Path(__file__).resolve().parents[2]
IMPORTER_SCRIPT = AGENT_ROOT / "importer" / "main.py"
IMPORTER_PID_FILE = IMPORTER_SCRIPT.parent / "importer.pid"

MODES = ("full", "season", "recent", "since")


class ImportAlreadyRunning(Exception):
    """已有导入子进程存活，触发被拒绝。"""


# ponytail: 单进程门禁 = 存活子进程；agent 多实例部署时此约束不成立（与旧 Java 实现同级假设）
_lock = threading.Lock()
_proc: subprocess.Popen | None = None


def db_session() -> Session:
    return Session(get_engine(
        os.getenv("DB_HOST", "127.0.0.1"), int(os.getenv("DB_PORT", "3306")),
        os.getenv("DB_USER", "root"), os.getenv("DB_PASSWORD", ""),
        os.getenv("DB_NAME", "anime_tracker"),
    ))


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


def _read_import_pid() -> int | None:
    try:
        return int(IMPORTER_PID_FILE.read_text().strip())
    except (OSError, ValueError):
        return None


def _orphan_import_running() -> bool:
    """worker 重启丢失 _proc 后，用 PID 文件判断导入子进程是否仍存活。"""
    pid = _read_import_pid()
    return pid is not None and _pid_alive(pid)


def _sweep_stale_records():
    """无存活导入进程时，把遗留 RUNNING 记录翻 FAILED（进程硬退兜底）。"""
    try:
        with db_session() as db:
            _flip_running(db)
            db.commit()
    except Exception as exc:  # DB 不可用时仅告警，不阻塞导入
        logger.warning("清理孤立导入记录失败: %s", exc)


def sweep_dead_processes():
    global _proc
    with _lock:
        if _proc is not None and _proc.poll() is not None:
            _proc = None
        if _proc is None and not _orphan_import_running():
            _sweep_stale_records()


def _spawn(args: list[str]):
    global _proc
    log_file = open(IMPORTER_SCRIPT.parent / "import.log", "ab")
    _proc = subprocess.Popen(
        [sys.executable, str(IMPORTER_SCRIPT), *args],
        cwd=AGENT_ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )


def run_import(mode: str, key: str | None = None, since: str | None = None,
               workers: int | None = None) -> None:
    sweep_dead_processes()
    if mode not in MODES:
        raise ValueError("mode 必须是 full / season / recent / since")
    if mode == "season" and not key:
        raise ValueError("season 模式需要 key")
    if mode == "since" and not since:
        raise ValueError("since 模式需要 since")

    args = ["--mode", mode]
    if key:
        args += ["--key", key]
    if since:
        args += ["--since", since]
    if workers is not None:
        args += ["--workers", str(workers)]

    with _lock:
        if _proc is not None and _proc.poll() is None:
            raise ImportAlreadyRunning("已有导入任务运行中")
        if _proc is None and _orphan_import_running():
            raise ImportAlreadyRunning("已有导入任务运行中")
        _spawn(args)

    logger.info("已触发导入: %s", " ".join(args))
