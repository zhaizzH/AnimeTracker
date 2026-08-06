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
