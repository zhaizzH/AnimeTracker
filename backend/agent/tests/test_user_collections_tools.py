from app.agent.client.domain import user_collections_tools as uct
from app.schemas.auth import UserInfo


def _user():
    return UserInfo(user_id=7, username="", role="USER", token="tok123")


def test_get_my_collections_sends_token_and_type(monkeypatch):
    captured = {}

    def fake_call(method, path, params=None, token=None):
        captured.update(method=method, path=path, params=params, token=token)
        return {"content": [{"id": 1}], "total": 1}

    monkeypatch.setattr("app.agent.client.domain.user_collections_tools.call_api", fake_call)

    result = uct.get_my_collections.func(type=2, page=1, size=20, user=_user())

    assert result["total"] == 1
    assert captured["token"] == "tok123"
    assert captured["path"] == "/api/user/collections"
    assert captured["params"]["type"] == 2


def test_get_my_collections_omits_type_when_zero(monkeypatch):
    captured = {}

    def fake_call(method, path, params=None, token=None):
        captured.update(params=params)
        return {"content": [], "total": 0}

    monkeypatch.setattr("app.agent.client.domain.user_collections_tools.call_api", fake_call)

    uct.get_my_collections.func(type=0, user=_user())
    assert "type" not in captured["params"]


def test_get_my_watch_profile_compacts(monkeypatch):
    def fake_call(method, path, params=None, token=None):
        return {"content": [{
            "type": 3, "epStatus": 5,
            "subject": {"name": "番A", "nameCn": "", "type": 2, "score": 8.5, "eps": 24},
        }], "total": 1}

    monkeypatch.setattr("app.agent.client.domain.user_collections_tools.call_api", fake_call)

    profile = uct.get_my_watch_profile.func(cap=50, user=_user())

    assert profile[0]["name"] == "番A"
    assert profile[0]["score"] == 8.5
    assert profile[0]["my_progress"] == 5


def test_get_my_watch_profile_empty_when_no_collections(monkeypatch):
    def fake_call(method, path, params=None, token=None):
        return {"content": [], "total": 0}

    monkeypatch.setattr("app.agent.client.domain.user_collections_tools.call_api", fake_call)

    assert uct.get_my_watch_profile.func(user=_user()) == []


def test_get_my_watch_profile_passes_error_through(monkeypatch):
    def fake_call(method, path, params=None, token=None):
        return {"error": True, "message": "登录已过期，请重新登录"}

    monkeypatch.setattr("app.agent.client.domain.user_collections_tools.call_api", fake_call)

    assert uct.get_my_watch_profile.func(user=_user()) == {"error": True, "message": "登录已过期，请重新登录"}
