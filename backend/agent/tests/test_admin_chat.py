import jwt

from fastapi.testclient import TestClient

from app.config import settings


def test_admin_chat_requires_token():
    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/admin/agent/chat/sessions")
        assert resp.status_code == 401


def test_admin_chat_rejects_non_admin():
    from main import app

    token = jwt.encode({"userId": 1, "role": "USER"}, settings.jwt_secret, algorithm="HS256")
    with TestClient(app) as client:
        resp = client.get(
            "/api/admin/agent/chat/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
