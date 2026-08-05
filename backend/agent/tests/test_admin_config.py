import json

import pytest
from fastapi import HTTPException

import app.api.admin_config as admin_config
from app.schemas.admin_config import PromptUpdateRequest


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


@pytest.fixture
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(admin_config, "_redis", lambda: r)
    return r


def test_list_prompts_returns_four_managed():
    out = admin_config.list_prompts()
    assert [p.promptKey for p in out] == list(admin_config.MANAGED_PROMPT_KEYS)


def test_update_prompt_persists_and_triggers_refresh(monkeypatch, fake_redis):
    called = []
    monkeypatch.setattr(admin_config, "refresh_agent_prompt_snapshot", lambda k: called.append(k))
    admin_config.update_prompt("client_search_agent_prompt", PromptUpdateRequest(promptContent="NEW"))
    key = admin_config.PROMPT_REDIS_KEY_TEMPLATE.format("client_search_agent_prompt")
    assert json.loads(fake_redis.store[key])["promptContent"] == "NEW"
    assert called == ["client_search_agent_prompt"]


def test_reset_prompt_removes_redis(monkeypatch, fake_redis):
    key = admin_config.PROMPT_REDIS_KEY_TEMPLATE.format("client_search_agent_prompt")
    fake_redis.store[key] = json.dumps({"promptContent": "X"})
    monkeypatch.setattr(admin_config, "refresh_agent_prompt_snapshot", lambda k: None)
    out = admin_config.reset_prompt("client_search_agent_prompt")
    assert key not in fake_redis.store
    assert out.promptContent != "X"
    assert out.promptContent != ""


def test_unknown_key_raises_404():
    with pytest.raises(HTTPException) as exc:
        admin_config.get_prompt("nope")
    assert exc.value.status_code == 404
