from app.config import AgentChatModelSlot, create_agent_chat_llm, settings


def _effective_temperature(llm) -> float:
    # ChatTongyi 将温度放入 model_kwargs；opencode 路径（ChatOpenAI/ChatAnthropic）暴露 .temperature
    return (getattr(llm, "model_kwargs", None) or {}).get("temperature", getattr(llm, "temperature"))


def _no_runtime_config(monkeypatch):
    # 隔离 Redis 运行时配置，避免残留配置污染断言（断言应针对 .env/默认值）
    monkeypatch.setattr("app.config.get_runtime_model_config", lambda: None)


def test_route_slot_uses_zero_temperature(monkeypatch):
    _no_runtime_config(monkeypatch)
    llm = create_agent_chat_llm(AgentChatModelSlot.CLIENT_ROUTE)
    assert _effective_temperature(llm) == 0.0  # 路由槽固定低温，与 settings.llm_temperature 无关


def test_search_slot_inherits_settings_temperature(monkeypatch):
    _no_runtime_config(monkeypatch)
    llm = create_agent_chat_llm(AgentChatModelSlot.CLIENT_SEARCH)
    assert _effective_temperature(llm) == settings.llm_temperature  # 无槽覆盖时继承 settings
