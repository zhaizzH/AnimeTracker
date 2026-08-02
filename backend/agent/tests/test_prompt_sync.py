import json

import pytest

import app.core.prompt_sync as prompt_sync
from app.core.prompt_sync import (
    initialize_agent_prompt_snapshot,
    load_managed_prompt,
)


@pytest.fixture(autouse=True)
def _reset_snapshot():
    prompt_sync._PROMPT_SNAPSHOT = {}
    yield
    prompt_sync._PROMPT_SNAPSHOT = {}


def test_managed_prompt_falls_back_to_local():
    text = load_managed_prompt("client_search_agent_prompt", "client/search_agent_prompt.md")
    assert "搜索" in text


def test_redis_content_wins_when_present(monkeypatch):
    class FakeRedis:
        def get(self, key):
            return json.dumps({"promptContent": "REDIS-PROMPT", "promptKey": "client_search_agent_prompt"})

    monkeypatch.setattr(prompt_sync, "_get_redis", lambda: FakeRedis())
    initialize_agent_prompt_snapshot()
    assert load_managed_prompt("client_search_agent_prompt", "client/search_agent_prompt.md") == "REDIS-PROMPT"


def test_redis_down_falls_back_to_local(monkeypatch):
    def _boom():
        raise RuntimeError("redis down")

    monkeypatch.setattr(prompt_sync, "_get_redis", _boom)
    initialize_agent_prompt_snapshot()  # 不抛异常
    assert load_managed_prompt("client_search_agent_prompt", "client/search_agent_prompt.md") != ""


def test_non_managed_key_uses_local_only():
    text = load_managed_prompt("some_key", "client/recommend_agent_prompt.md")
    assert "推荐" in text
