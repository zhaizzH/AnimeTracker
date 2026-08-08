import pytest
from langchain_core.messages import AIMessage

from app.agent.client.gateway import _resolve_routing_result


def test_resolve_valid_target():
    payload = {"messages": [AIMessage(content='{"route_target": "search_agent"}')]}
    assert _resolve_routing_result(payload) == {"route_target": "search_agent"}


@pytest.mark.parametrize("bad", [
    '{"route_target": "hack"}',
    'not json',
    '{"other": 1}',
])
def test_resolve_invalid_raises(bad):
    payload = {"messages": [AIMessage(content=bad)]}
    with pytest.raises(ValueError):
        _resolve_routing_result(payload)


def test_resolve_empty_messages_raises():
    with pytest.raises(ValueError):
        _resolve_routing_result({"messages": []})


def test_resolve_anthropic_content_block_list():
    # Anthropic 端点模型返回 content 块列表(thinking+text),必须能从中抽取 JSON
    payload = {"messages": [AIMessage(content=[
        {"type": "thinking", "thinking": "用户意图是搜索", "signature": ""},
        {"type": "text", "text": '{"route_target": "discover_agent"}'},
    ])]}
    assert _resolve_routing_result(payload) == {"route_target": "discover_agent"}
