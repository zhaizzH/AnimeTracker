"""Tests for WebSocket connection manager."""

import pytest
import respx
from httpx import Response

from app.chat.manager import verify_token
from app.config import settings

BASE = settings.backend_base_url


@pytest.mark.asyncio
@respx.mock
async def test_verify_token_invalid():
    """Invalid token returns None."""
    route = respx.get(f"{BASE}/me").mock(Response(401))
    user_id = await verify_token("invalid-token")
    assert route.called
    assert user_id is None


@pytest.mark.asyncio
@respx.mock
async def test_verify_token_no_backend():
    """Backend unavailable returns None."""
    route = respx.get(f"{BASE}/me").mock(Response(500))
    user_id = await verify_token("some-token")
    assert route.called
    assert user_id is None
