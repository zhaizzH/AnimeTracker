import httpx
import logging
from fastapi import Header, HTTPException

from app.config import settings
from app.schemas.auth import UserInfo

logger = logging.getLogger(__name__)


async def verify_token(authorization: str | None = Header(None)) -> UserInfo:
    """JWT 验证依赖注入 — 调用 Spring Boot 后端验证"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证失败")

    token = authorization[len("Bearer "):]
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.backend_base_url}/api/user/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="认证失败，请重新登录")

            data = resp.json()["data"]
            role = data.get("role", "USER")
            return UserInfo(
                user_id=data["id"],
                username=data.get("username", ""),
                role=role if role in ("USER", "ADMIN") else "USER",
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="认证服务暂时不可用，请稍后重试")
