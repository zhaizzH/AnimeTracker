import json

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import verify_token
from app.core.prompt_sync import (
    MANAGED_PROMPT_KEYS,
    PROMPT_REDIS_KEY_TEMPLATE,
    load_managed_prompt,
    refresh_agent_prompt_snapshot,
)
from app.core.runtime_config import MODEL_CONFIG_KEY, get_runtime_model_config, set_runtime_model_config
from app.api.schemas.admin_config import ModelConfig, PromptOut, PromptUpdateRequest
from app.chat.user import UserInfo

router = APIRouter(prefix="/api/admin/agent")

# 托管 key -> 本地默认提示词文件（reset 后回退）
LOCAL_PROMPT_PATHS = {
    "client_gateway_prompt": "client/gateway_prompt.md",
    "client_search_agent_prompt": "client/search_agent_prompt.md",
    "client_discover_agent_prompt": "client/discover_agent_prompt.md",
    "client_recommend_agent_prompt": "client/recommend_agent_prompt.md",
    "admin_agent_prompt": "admin/admin_agent_prompt.md",
}


def _redis():
    import redis as redis_lib

    from app.config import settings

    return redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)


def require_admin(authorization: str | None = Header(None)) -> UserInfo:
    """管理端点鉴权：本地验签 + 校验 ADMIN 角色（纵深防御）。"""
    user = verify_token(authorization)
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="无权限")
    return user


def _effective_prompt(key: str) -> str:
    return load_managed_prompt(key, LOCAL_PROMPT_PATHS.get(key))


@router.get("/prompts", dependencies=[Depends(require_admin)])
def list_prompts():
    return [PromptOut(promptKey=k, promptContent=_effective_prompt(k)) for k in MANAGED_PROMPT_KEYS]


@router.get("/prompts/{key}", dependencies=[Depends(require_admin)])
def get_prompt(key: str):
    if key not in MANAGED_PROMPT_KEYS:
        raise HTTPException(status_code=404, detail="无效的提示词 key")
    return PromptOut(promptKey=key, promptContent=_effective_prompt(key))


@router.post("/prompts/{key}/update", dependencies=[Depends(require_admin)])
def update_prompt(key: str, body: PromptUpdateRequest):
    if key not in MANAGED_PROMPT_KEYS:
        raise HTTPException(status_code=404, detail="无效的提示词 key")
    _redis().set(
        PROMPT_REDIS_KEY_TEMPLATE.format(key),
        json.dumps({"promptKey": key, "promptContent": body.promptContent}),
    )
    refresh_agent_prompt_snapshot(key)
    return PromptOut(promptKey=key, promptContent=_effective_prompt(key))


@router.post("/prompts/{key}/reset", dependencies=[Depends(require_admin)])
def reset_prompt(key: str):
    if key not in MANAGED_PROMPT_KEYS:
        raise HTTPException(status_code=404, detail="无效的提示词 key")
    _redis().delete(PROMPT_REDIS_KEY_TEMPLATE.format(key))
    refresh_agent_prompt_snapshot(key)
    return PromptOut(promptKey=key, promptContent=_effective_prompt(key))


@router.get("/config", dependencies=[Depends(require_admin)])
def get_config():
    return ModelConfig(**(get_runtime_model_config() or {}))


@router.post("/config/update", dependencies=[Depends(require_admin)])
def update_config(body: ModelConfig):
    cfg = body.model_dump(exclude_none=True)
    if cfg.get("temperature") is not None and not (0 <= cfg["temperature"] <= 2):
        raise HTTPException(status_code=400, detail="temperature 需在 0~2 之间")
    if cfg.get("maxTokens") is not None and cfg["maxTokens"] <= 0:
        raise HTTPException(status_code=400, detail="maxTokens 需为正整数")
    set_runtime_model_config(cfg)
    return ModelConfig(**cfg)
