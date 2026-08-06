import httpx

from app.agent.client.domain import _http


def test_call_api_sends_bearer_header_and_unwraps_data(monkeypatch):
    captured = {}

    def fake_request(method, url, params=None, headers=None, timeout=None):
        captured.update(method=method, url=url, params=params, headers=headers)
        return httpx.Response(200, json={"code": 200, "data": {"total": 1}},
                              request=httpx.Request("GET", url))

    monkeypatch.setattr(_http.httpx, "request", fake_request)

    result = _http.call_api("GET", "/api/user/collections", params={"page": 1}, token="tok123")

    assert result == {"total": 1}
    assert captured["headers"]["Authorization"] == "Bearer tok123"
    assert captured["url"].endswith("/api/user/collections")


def test_call_api_maps_401_to_login_expired(monkeypatch):
    def fake_request(method, url, params=None, headers=None, timeout=None):
        return httpx.Response(401, json={"code": 401, "message": "no"},
                              request=httpx.Request("GET", url))

    monkeypatch.setattr(_http.httpx, "request", fake_request)

    assert _http.call_api("GET", "/x") == {"error": True, "message": "登录已过期，请重新登录"}


def test_call_api_maps_timeout(monkeypatch):
    def fake_request(method, url, params=None, headers=None, timeout=None):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(_http.httpx, "request", fake_request)

    assert _http.call_api("GET", "/x") == {"error": True, "message": "后端服务超时"}


def test_search_subjects_shape_preserved_and_no_token(monkeypatch):
    captured = {}

    def fake_call(method, path, params=None, token=None):
        captured.update(method=method, path=path, params=params, token=token)
        return {"content": [{"id": 1}]}

    monkeypatch.setattr("app.agent.client.domain.search.tools.call_api", fake_call)

    from app.agent.client.domain.search.tools import search_subjects

    result = search_subjects.invoke({"query": "鬼灭"})
    assert result == [{"id": 1}]
    assert captured["params"]["q"] == "鬼灭"
    assert captured["token"] is None
