"""导入触发 API：后台运行 importer，进程生命周期由本模块管理。

Java 管理端 `/api/admin/import/run` 转发至此；importer 仍可作为独立 CLI 运行。
"""
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.admin_config import require_admin
from importer.db import fail_stale_running_records as _flip_running, get_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/agent/import", dependencies=[Depends(require_admin)])

AGENT_ROOT = Path(__file__).resolve().parents[2]
IMPORTER_SCRIPT = AGENT_ROOT / "importer" / "main.py"

MODES = ("full", "season", "recent", "since")

# ponytail: 单进程门禁 = 存活子进程；agent 多实例部署时此约束不成立（与旧 Java 实现同级假设）
_lock = threading.Lock()
_proc: subprocess.Popen | None = None


def _db_session() -> Session:
    return Session(get_engine(
        os.getenv("DB_HOST", "127.0.0.1"), int(os.getenv("DB_PORT", "3306")),
        os.getenv("DB_USER", "root"), os.getenv("DB_PASSWORD", ""),
        os.getenv("DB_NAME", "anime_tracker"),
    ))


def _sweep_stale_records():
    """无存活导入进程时，把遗留 RUNNING 记录翻 FAILED（进程硬退兜底）。"""
    try:
        with _db_session() as db:
            _flip_running(db)
            db.commit()
    except Exception as exc:  # DB 不可用时仅告警，不阻塞导入
        logger.warning("清理孤立导入记录失败: %s", exc)


def _sweep():
    global _proc
    with _lock:
        if _proc is not None and _proc.poll() is not None:
            _proc = None
        if _proc is None:
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


@router.post("/run")
def run_import(mode: str, key: str | None = None, since: str | None = None,
               workers: int | None = None):
    _sweep()
    if mode not in MODES:
        raise HTTPException(status_code=400, detail="mode 必须是 full / season / recent / since")
    if mode == "season" and not key:
        raise HTTPException(status_code=400, detail="season 模式需要 key")
    if mode == "since" and not since:
        raise HTTPException(status_code=400, detail="since 模式需要 since")

    args = ["--mode", mode]
    if key:
        args += ["--key", key]
    if since:
        args += ["--since", since]
    if workers is not None:
        args += ["--workers", str(workers)]

    with _lock:
        if _proc is not None and _proc.poll() is None:
            raise HTTPException(status_code=409, detail="已有导入任务运行中")
        _spawn(args)

    logger.info("已触发导入: %s", " ".join(args))
    return {"ok": True}
