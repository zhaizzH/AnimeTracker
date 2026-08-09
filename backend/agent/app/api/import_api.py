"""导入触发 API：Java 管理端 `/api/admin/import/run` 转发至此。

进程生命周期与触发逻辑在 app.core.import_runner（与 admin 领域工具共享单飞门禁）。
importer 仍可作为独立 CLI 运行。
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.api.admin_config import require_admin
from app.core.import_runner import (
    ImportAlreadyRunning,
    db_session,
    run_import as _run_import,
    sweep_dead_processes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/agent/import", dependencies=[Depends(require_admin)])


@router.post("/run")
def run_import(mode: str, key: str | None = None, since: str | None = None,
               workers: int | None = None):
    try:
        _run_import(mode, key=key, since=since, workers=workers)
    except ImportAlreadyRunning:
        raise HTTPException(status_code=409, detail="已有导入任务运行中")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True}


@router.get("/status")
def import_status():
    """导入状态唯一权威：先按真实进程态翻孤儿 RUNNING，再返回总数与最近记录。

    Java 管理端 `/api/admin/import/status` 转发至此；前端每 5s 轮询。
    """
    sweep_dead_processes()
    with db_session() as db:
        total = db.execute(text("SELECT COUNT(*) FROM subject")).scalar() or 0
        rows = db.execute(text(
            "SELECT id, season_key, status, subject_count, started_at, completed_at, error_message "
            "FROM import_record ORDER BY started_at DESC LIMIT 10"
        )).mappings().all()
        records = [
            {
                "id": row["id"],
                "season": row["season_key"],
                "status": row["status"],
                "subjectCount": row["subject_count"],
                "startedAt": row["started_at"].isoformat() if row["started_at"] else None,
                "completedAt": row["completed_at"].isoformat() if row["completed_at"] else None,
                "errorMessage": row["error_message"],
            }
            for row in rows
        ]
    return {
        "lastImportedAt": next((r["completedAt"] for r in records if r["completedAt"]), None),
        "totalSubjects": total,
        "recentRecords": records,
    }
