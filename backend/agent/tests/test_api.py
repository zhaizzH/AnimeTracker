import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.api.deps import verify_token
from app.schemas.auth import UserInfo, AuthResult


@pytest.mark.asyncio
async def test_health_endpoint():
    """健康检查端点不需要认证"""
    from app.api.chat import router
    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/chat/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_list_sessions_no_auth():
    """未认证的请求返回 401"""
    from app.api.chat import router
    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/chat/sessions")
    assert resp.status_code == 401


class TestVerifyToken:
    @patch("app.api.deps.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"data": {"id": 1, "username": "test"}})
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp

        result = await verify_token("Bearer valid-token")
        assert result is not None
        assert result.user_id == 1
        assert result.username == "test"
        assert result.role == "USER"

    @patch("app.api.deps.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_verify_admin_token(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"data": {"id": 2, "username": "admin", "role": "ADMIN"}})
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp

        result = await verify_token("Bearer admin-token")
        assert result.role == "ADMIN"

    @patch("app.api.deps.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, mock_client):
        from fastapi import HTTPException
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp

        with pytest.raises(HTTPException) as exc_info:
            await verify_token("Bearer bad")
        assert exc_info.value.status_code == 401
