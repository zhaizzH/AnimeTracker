import jwt

from app.api.deps import verify_token
from app.config import settings


def test_verify_token_passes_through_raw_token():
    token = jwt.encode({"userId": 7, "role": "USER"}, settings.jwt_secret, algorithm="HS256")
    user = verify_token(f"Bearer {token}")
    assert user.user_id == 7
    assert user.role == "USER"
    assert user.token == token
