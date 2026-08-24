"""导入触发 API：Java 管理端 `/api/admin/import/run` 转发至此。"""
from fastapi import APIRouter, Depends, HTTPException, Request

from app.admin.import_service import ImportAlreadyRunning, ImportService
from app.api.admin_config import require_admin

router = APIRouter(prefix="/api/admin/agent/import", dependencies=[Depends(require_admin)])


def get_import_service(request: Request) -> ImportService:
    return request.app.state.import_service


@router.post("/run")
def run_import(mode: str, key: str | None = None, since: str | None = None,
               workers: int | None = None,
               import_service: ImportService = Depends(get_import_service)):
    try:
        import_service.run(mode, key=key, since=since, workers=workers)
    except ImportAlreadyRunning:
        raise HTTPException(status_code=409, detail="已有导入任务运行中")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True}
