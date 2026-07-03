"""
Agent 配置 API 路由

GET /api/config — 获取 Agent 配置信息
"""

from fastapi import APIRouter

from config import settings

router = APIRouter()


@router.get("/api/config")
async def get_agent_config():
    """获取 Agent 当前配置（不含敏感字段）"""
    return {
        "model": settings.LLM_MODEL,
        "temperature": settings.LLM_TEMPERATURE,
        "backend_api_base": settings.BACKEND_API_BASE,
    }
