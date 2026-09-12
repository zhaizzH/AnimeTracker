from types import SimpleNamespace

from app.agent.client.gateway import (
    _is_explicit_confirmation,
    _is_explicit_recommendation_request,
)
from app.agent.graph import _route_from_entry
from app.agent.runtime import agent_stream


def test_admin_entry_routes_to_admin_agent() -> None:
    state = {
        "current_question": "你支持 RAG 吗？",
        "user": SimpleNamespace(role="ADMIN"),
    }

    assert _route_from_entry(state) == "admin_agent"


def test_user_entry_routes_to_gateway_router() -> None:
    state = {
        "current_question": "搜索科幻动画",
        "user": SimpleNamespace(role="USER"),
    }

    assert _route_from_entry(state) == "gateway_router"


def test_explicit_recommendation_request_is_detectable() -> None:
    assert _is_explicit_recommendation_request("搜索评分高的动画，然后加入想看")
    assert not _is_explicit_recommendation_request("搜索评分高的动画")
    assert not _is_explicit_recommendation_request("不要加入想看")


def test_confirmation_phrase_is_checked_before_negation_markers() -> None:
    assert _is_explicit_confirmation("没问题")
    assert _is_explicit_confirmation("确认？")
    assert not _is_explicit_confirmation("不要执行")


def test_reasoning_chunks_keep_word_boundaries() -> None:
    class FakeAgent:
        async def astream(self, _payload, stream_mode):
            assert stream_mode == ["messages", "values"]
            yield (
                "messages",
                (SimpleNamespace(content="", reasoning_content="I "), {"langgraph_node": "model"}),
            )
            yield (
                "messages",
                (SimpleNamespace(content="", reasoning_content="will "), {"langgraph_node": "model"}),
            )
            yield (
                "messages",
                (SimpleNamespace(content="", reasoning_content="search"), {"langgraph_node": "model"}),
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

    assert visible_thinking == ["I ", "will ", "search"]
    assert result["streamed_thinking"] == "I will search"
    assert result["streamed_text"] == "中文答案"
