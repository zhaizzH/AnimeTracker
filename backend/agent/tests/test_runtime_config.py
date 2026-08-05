import json

import pytest

import app.core.runtime_config as runtime_config
from app.core.runtime_config import get_runtime_model_config, set_runtime_model_config


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


@pytest.fixture
def fake_redis(monkeypatch):
    runtime_config._cache = {"ts": 0.0, "data": None}
    r = FakeRedis()
    monkeypatch.setattr(runtime_config, "_redis", lambda: r)
    return r


@pytest.fixture(autouse=True)
def _reset_cache_after_each_test():
    # 清除模块级缓存,避免污染同进程内后续测试文件(test_config.py)
    yield
    runtime_config._cache = {"ts": 0.0, "data": None}


def test_unset_returns_none(fake_redis):
    assert get_runtime_model_config() is None


def test_set_then_get(fake_redis):
    set_runtime_model_config({"model": "qwen-max", "temperature": 0.5})
    assert get_runtime_model_config()["model"] == "qwen-max"
    assert get_runtime_model_config()["temperature"] == 0.5


def test_cache_respected_within_ttl(fake_redis):
    get_runtime_model_config()  # 首次读入缓存（空）
    fake_redis.store[runtime_config.MODEL_CONFIG_KEY] = json.dumps({"model": "qwen-plus"})
    # 缓存未过期,仍返回首次结果 None
    assert get_runtime_model_config() is None


def test_create_agent_chat_llm_uses_runtime_config(monkeypatch, fake_redis):
    import app.config as config_mod
    from app.config import AgentChatModelSlot, create_agent_chat_llm

    set_runtime_model_config({"model": "qwen-max", "temperature": 0.9})
    captured = {}

    def fake_create_llm(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(config_mod, "create_llm", fake_create_llm)
    create_agent_chat_llm(AgentChatModelSlot.CLIENT_SEARCH)
    assert captured["model"] == "qwen-max"
    assert captured["temperature"] == 0.9
