"""``app.api.deps.verify_token`` 的回归测试。

背景：business（Java/JJWT）以 ``Keys.hmacShaKeyFor`` 按密钥字节长度自动选
HMAC 算法，agent 侧若把 ``algorithms`` 硬编码为 ``["HS256"]``，则生产强密钥
（64 字节 → HS512）签发的 token 会全部验签失败，AI 对话整体 401。
本测试锁定「三种 HMAC 算法均须放行」这一契约。
"""

from __future__ import annotations

import jwt
import pytest

from app.api.deps import verify_token

# 覆盖 JJWT 的三档阈值：>=32B→HS256，>=48B→HS384，>=64B→HS512
SECRET_AND_ALG = [
    ("s" * 32, "HS256"),
    ("s" * 48, "HS384"),
    ("s" * 64, "HS512"),
]

@pytest.mark.parametrize("secret,alg", SECRET_AND_ALG)
def test_accepts_every_hmac_alg_jjwt_may_pick(monkeypatch, secret, alg):
    """business 可能签发的三种 HMAC 算法，agent 都必须验签通过。"""
    monkeypatch.setattr("app.api.deps.settings.jwt_secret", secret)
    token = jwt.encode({"userId": 7, "role": "ADMIN"}, secret, algorithm=alg)

    user = verify_token(authorization=f"Bearer {token}")

    assert user.user_id == 7
    assert user.role == "ADMIN"

def test_rejects_token_signed_with_other_secret(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.jwt_secret", "s" * 64)
    token = jwt.encode({"userId": 7}, "other" * 16, algorithm="HS512")

    with pytest.raises(Exception):
        verify_token(authorization=f"Bearer {token}")

def test_rejects_missing_or_malformed_header(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.jwt_secret", "s" * 64)

    for header in (None, "", "token-without-bearer"):
        with pytest.raises(Exception):
            verify_token(authorization=header)
