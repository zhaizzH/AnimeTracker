import pytest

from app.agent.graph import _route_from_entry, _route_from_gateway
from app.chat.user import UserInfo


def test_entry_routes_admin_and_user_without_model_call():
    admin = UserInfo(user_id=1, username="admin", role="ADMIN", token="a")
    user = UserInfo(user_id=2, username="user", role="USER", token="u")

    assert _route_from_entry({"user": admin}) == "admin_agent"
    assert _route_from_entry({"user": user}) == "gateway_router"


def test_gateway_rejects_unknown_target():
    with pytest.raises(ValueError, match="valid route_target"):
        _route_from_gateway({"routing": {"route_target": "unknown"}})
