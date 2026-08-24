from __future__ import annotations

import httpx

from app.adapters import business_http


def test_http_business_gateway_posts_json_body_and_keeps_authorization(monkeypatch):
    captured: dict[str, object] = {}

    def fake_request(*_args, **kwargs):
        captured.update(kwargs)
        request = httpx.Request("POST", "https://test.invalid/api/client/subjects/batch")
        return httpx.Response(200, request=request, json={"data": {"items": []}})

    monkeypatch.setattr(business_http.httpx, "request", fake_request)

    gateway = business_http.HttpBusinessGateway("https://test.invalid")
    assert gateway.request("POST", "/api/client/subjects/batch", token="secret", json_body={"subjectIds": [7]}) == {
        "items": []
    }
    assert captured["json"] == {"subjectIds": [7]}
    assert captured["headers"] == {"Authorization": "Bearer secret"}
