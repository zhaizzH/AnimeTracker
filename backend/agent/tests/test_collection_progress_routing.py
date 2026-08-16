from datetime import datetime, timedelta

from app.agent.client import gateway
from app.agent import run
from app.schemas.pending_action import CollectionProgressPendingAction


def _pending(preview_id="p1", user_id=7):
    return CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id=preview_id,
        user_id=user_id,
        expires_at=datetime.now() + timedelta(minutes=10),
        items=[{"subjectId": 1, "subjectName": "A", "currentEpStatus": 3, "targetEpStatus": 5}],
    )


def test_pending_confirmation_forces_recommend_agent():
    state = {"pending_action": _pending(), "current_question": "确认"}
    assert gateway._resolve_forced_pending_route(state) == {"routing": {"route_target": "recommend_agent"}}


def test_no_pending_action_does_not_force_route():
    state = {"pending_action": None, "current_question": "确认"}
    assert gateway._resolve_forced_pending_route(state) is None


def test_non_confirmation_does_not_force_route():
    state = {"pending_action": _pending(), "current_question": "帮我搜一下这部番剧"}
    assert gateway._resolve_forced_pending_route(state) is None


def test_is_explicit_confirmation_rejects_negation_and_vague_text():
    assert gateway._is_explicit_confirmation("确认") is True
    assert gateway._is_explicit_confirmation("不确认") is False
    assert gateway._is_explicit_confirmation("再想想") is False


def test_gateway_router_returns_before_llm_when_pending_confirmation():
    state = {"pending_action": _pending(), "current_question": "确认", "history_messages": []}
    assert gateway.gateway_router(state) == {"routing": {"route_target": "recommend_agent"}}


def test_run_domain_agent_appends_pending_context_with_preview_id(monkeypatch):
    captured = {}

    def fake_create_agent(**kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt")
        return object()

    monkeypatch.setattr(run, "create_agent", fake_create_agent)
    monkeypatch.setattr(run, "create_agent_chat_llm", lambda **k: object())
    monkeypatch.setattr(run, "agent_stream", lambda *a, **k: {"streamed_text": "已更新"})

    state = {"pending_action": _pending("p1"), "history_messages": []}
    result = run.run_domain_agent(
        state,
        slot=run.AgentChatModelSlot.CLIENT_RECOMMEND,
        tools=[],
        prompt_key="client_recommend_agent_prompt",
        prompt_path="client/recommend_agent_prompt.md",
        include_pending_action=True,
    )
    prompt = captured["system_prompt"].content
    assert result["result"] == "已更新"
    assert "p1" in prompt
    assert "待确认动作" in prompt
