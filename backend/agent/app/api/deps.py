import logging

import jwt
from fastapi import Header, HTTPException

from app.config import settings
from app.schemas.auth import UserInfo

logger = logging.getLogger(__name__)


def verify_token(authorization: str | None = Header(None)) -> UserInfo:
    """JWT 验证依赖注入 — 本地验签,不回调 Spring Boot,避免代理回路/线程饥饿。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证失败")

    token = authorization[len("Bearer "):]
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="认证失败，请重新登录")

    user_id = claims.get("userId")
    if user_id is None:
        raise HTTPException(status_code=401, detail="认证失败，请重新登录")

    role = str(claims.get("role") or "USER")
    return UserInfo(
        user_id=int(user_id),
        username="",
        role=role if role in ("USER", "ADMIN") else "USER",
    )
