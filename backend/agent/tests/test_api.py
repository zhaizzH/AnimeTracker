import asyncio

from fastapi.testclient import TestClient


def test_health_endpoint(monkeypatch):
    from app.config import settings

    # 模拟 opencode key 已配、dashscope 未配的环境
    monkeypatch.setattr(settings, "dashscope_api_key", "")
    monkeypatch.setattr(settings, "opencode_api_key", "test-key")

    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/client/agent/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        # 任一 provider 可用即视为已配置（D8）
        assert body["llm_configured"] is True
