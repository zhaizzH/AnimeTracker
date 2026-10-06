import logging

import jwt
from fastapi import Header, HTTPException

from app.config import settings
from app.chat.user import UserInfo

logger = logging.getLogger(__name__)


def verify_token(authorization: str | None = Header(None)) -> UserInfo:
    """JWT 验证依赖注入 — 本地验签,不回调 Spring Boot,避免代理回路/线程饥饿。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证失败")

    token = authorization[len("Bearer "):]
    try:
        # JJWT 的 Keys.hmacShaKeyFor 按密钥字节长度自动选 HS256/HS384/HS512
        # （>=64B→HS512，>=48B→HS384，>=32B→HS256），business 侧签发算法随
        # jwt.secret 长度变化。此处必须同样放行三种，硬编码单一算法会让生产
        # 强密钥（64B→HS512）签发的 token 全部验签失败。
        claims = jwt.decode(token, settings.jwt_secret, algorithms=["HS256", "HS384", "HS512"])
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
        token=token,
    )
