import pytest

from app.agent.graph import build_graph
from app.config import settings
from app.schemas.auth import UserInfo


def test_graph_builds():
    graph = build_graph()
    assert graph is not None


def test_entry_router_routes_admin_to_denied():
    from app.agent.graph import _route_from_entry
    state = {"user": UserInfo(user_id=1, username="a", role="ADMIN"), "history_messages": [], "routing": None, "result": ""}
    assert _route_from_entry(state) == "admin_denied"


def test_entry_router_routes_user_to_gateway():
    from app.agent.graph import _route_from_entry
    state = {"user": UserInfo(user_id=1, username="a", role="USER"), "history_messages": [], "routing": None, "result": ""}
    assert _route_from_entry(state) == "gateway_router"


def test_route_from_gateway_invalid_raises():
    from app.agent.graph import _route_from_gateway
    with pytest.raises(ValueError):
        _route_from_gateway({"routing": {"route_target": "hack"}})
