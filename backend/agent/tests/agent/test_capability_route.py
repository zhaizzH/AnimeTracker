from types import SimpleNamespace

from app.agent.graph import _capability_agent, _is_rag_capability_question, _route_from_entry
from app.agent.runtime import _NON_CHINESE_THINKING_FALLBACK, agent_stream


def test_rag_capability_question_uses_deterministic_route() -> None:
    state = {"current_question": "你有 RAG 功能吗？"}

    assert _is_rag_capability_question(state["current_question"])
    assert _route_from_entry(state) == "capability_agent"
    assert "具备 RAG 工具能力" in _capability_agent(state)["result"]


def test_rag_implementation_question_still_uses_normal_router() -> None:
    assert not _is_rag_capability_question("RAG 功能是怎么实现的？")
    assert _route_from_entry({"current_question": "RAG 功能是怎么实现的？"}) == "gateway_router"


def test_admin_capability_question_stays_in_admin_agent() -> None:
    state = {
        "current_question": "你支持 RAG 吗？",
        "user": SimpleNamespace(role="ADMIN"),
    }

    assert _route_from_entry(state) == "admin_agent"


def test_english_reasoning_is_not_exposed_to_sse() -> None:
    class FakeAgent:
        async def astream(self, _payload, stream_mode):
            assert stream_mode == ["messages", "values"]
            yield (
                "messages",
                (SimpleNamespace(content="", reasoning_content="I should inspect the tools."), {"langgraph_node": "model"}),
            )
            yield (
                "messages",
                (SimpleNamespace(content="中文答案", reasoning_content=None), {"langgraph_node": "model"}),
            )
            yield ("values", {"messages": []})

    visible_thinking: list[str] = []
    result = agent_stream(
        FakeAgent(),
        [],
        on_thinking_delta=visible_thinking.append,
    )

    assert visible_thinking == [_NON_CHINESE_THINKING_FALLBACK]
    assert result["streamed_thinking"] == _NON_CHINESE_THINKING_FALLBACK
    assert result["streamed_text"] == "中文答案"
