from datetime import datetime, timedelta

from app.agent import run
from app.agent.client import gateway
from app.config import ResolvedLlmProviderConfig
from app.schemas.pending_action import WishlistPendingAction, WishlistPendingItem
from pydantic import SecretStr


def _wishlist_pending():
    return WishlistPendingAction(
        type="ADD_TO_WISHLIST",
        user_id=7,
        expires_at=datetime.now() + timedelta(minutes=10),
        items=[WishlistPendingItem(subject_id=1, subject_name="A")],
    )


def test_wishlist_confirmation_forces_recommend_agent():
    state = {"pending_action": _wishlist_pending(), "current_question": "确认"}
    assert gateway._resolve_forced_pending_route(state) == {"routing": {"route_target": "recommend_agent"}}


def test_wishlist_pending_negation_does_not_force_route():
    state = {"pending_action": _wishlist_pending(), "current_question": "不确认"}
    assert gateway._resolve_forced_pending_route(state) is None


def test_run_domain_agent_injects_pending_only_when_enabled(monkeypatch):
    captured = {}

    def fake_create_agent(**kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt")
        return object()

    monkeypatch.setattr(run, "create_agent", fake_create_agent)
    monkeypatch.setattr(run, "create_agent_chat_llm", lambda **k: object())
    monkeypatch.setattr(
        run,
        "resolve_llm_provider",
        lambda _settings: ResolvedLlmProviderConfig(
            provider="deepseek",
            api_key=SecretStr("test-key"),
            model="test-model",
            route_model="test-route-model",
        ),
    )
    monkeypatch.setattr(run, "agent_stream", lambda *a, **k: {"streamed_text": "ok"})

    state = {"pending_action": _wishlist_pending(), "history_messages": []}

    # 未启用 include_pending_action（search/discover）时不注入待确认上下文
    run.run_domain_agent(state, slot=run.AgentChatModelSlot.CLIENT_SEARCH, tools=[],
                         prompt_key="client_search_agent_prompt", prompt_path="client/search_agent_prompt.md")
    assert "待确认动作" not in captured["system_prompt"].content

    # 启用后（recommend）注入待确认上下文
    run.run_domain_agent(state, slot=run.AgentChatModelSlot.CLIENT_RECOMMEND, tools=[],
                         prompt_key="client_recommend_agent_prompt", prompt_path="client/recommend_agent_prompt.md",
                         include_pending_action=True)
    assert "待确认动作" in captured["system_prompt"].content
