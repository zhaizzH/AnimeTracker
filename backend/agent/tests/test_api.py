import asyncio

from fastapi.testclient import TestClient


def test_health_endpoint():
    from main import app

    with TestClient(app) as client:
        resp = client.get("/api/client/agent/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
