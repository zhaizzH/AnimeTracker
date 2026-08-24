from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.deps import verify_token
from app.api.schemas.admin_config import ModelConfig, PromptOut, PromptUpdateRequest
from app.chat.user import UserInfo

router = APIRouter(prefix="/api/admin/agent")


def require_admin(authorization: str | None = Header(None)) -> UserInfo:
    """管理端点鉴权：本地验签 + 校验 ADMIN 角色（纵深防御）。"""
    user = verify_token(authorization)
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="无权限")
    return user


def _admin_service(request: Request):
    return request.app.state.admin_config_service


@router.get("/prompts", dependencies=[Depends(require_admin)])
def list_prompts(request: Request):
    return [PromptOut(**item) for item in _admin_service(request).list_prompts()]


@router.get("/prompts/{key}", dependencies=[Depends(require_admin)])
def get_prompt(key: str, request: Request):
    try:
        return PromptOut(**_admin_service(request).get_prompt(key))
    except KeyError:
        raise HTTPException(status_code=404, detail="无效的提示词 key")


@router.post("/prompts/{key}/update", dependencies=[Depends(require_admin)])
def update_prompt(key: str, body: PromptUpdateRequest, request: Request):
    try:
        return PromptOut(**_admin_service(request).update_prompt(key, body.promptContent))
    except KeyError:
        raise HTTPException(status_code=404, detail="无效的提示词 key")


@router.post("/prompts/{key}/reset", dependencies=[Depends(require_admin)])
def reset_prompt(key: str, request: Request):
    try:
        return PromptOut(**_admin_service(request).reset_prompt(key))
    except KeyError:
        raise HTTPException(status_code=404, detail="无效的提示词 key")


@router.get("/config", dependencies=[Depends(require_admin)])
def get_config(request: Request):
    return ModelConfig(**_admin_service(request).get_model_config())


@router.post("/config/update", dependencies=[Depends(require_admin)])
def update_config(body: ModelConfig, request: Request):
    cfg = body.model_dump(exclude_none=True)
    try:
        return ModelConfig(**_admin_service(request).update_model_config(cfg))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
