from __future__ import annotations

import httpx

from app.agent import http


def test_call_api_posts_json_body_and_keeps_authorization(monkeypatch):
    captured: dict[str, object] = {}

    def fake_request(*_args, **kwargs):
        captured.update(kwargs)
        request = httpx.Request("POST", "https://test.invalid/api/client/subjects/batch")
        return httpx.Response(200, request=request, json={"data": {"items": []}})

    monkeypatch.setattr(http.httpx, "request", fake_request)

    assert http.call_api("POST", "/api/client/subjects/batch", token="secret", json_body={"subjectIds": [7]}) == {"items": []}
    assert captured["json"] == {"subjectIds": [7]}
    assert captured["headers"] == {"Authorization": "Bearer secret"}
