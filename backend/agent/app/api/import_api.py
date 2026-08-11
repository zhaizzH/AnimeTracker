"""导入触发 API：Java 管理端 `/api/admin/import/run` 转发至此。

进程生命周期与触发逻辑在 app.core.import_runner（与 admin 领域工具共享单飞门禁）。
importer 仍可作为独立 CLI 运行。
"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.admin_config import require_admin
from app.core.import_runner import (
    ImportAlreadyRunning,
    run_import as _run_import,
)

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
