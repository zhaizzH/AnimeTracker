from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.admin.agent_node import admin_agent
from app.agent.client.discover import discover_agent
from app.agent.client.recommend import recommend_agent
from app.agent.client.gateway import gateway_router
from app.agent.client.search import search_agent
from app.agent.state import AgentState

_ALLOWED_TARGETS = ("search_agent", "discover_agent", "recommend_agent")


def _entry_router(_: AgentState) -> dict:
    return {}


def _route_from_entry(state: AgentState) -> str:
    user = state.get("user")
    if user is not None and getattr(user, "role", None) == "ADMIN":
        return "admin_agent"
    return "gateway_router"


def _route_from_gateway(state: AgentState) -> str:
    routing = state.get("routing") or {}
    target = routing.get("route_target")
    if target not in _ALLOWED_TARGETS:
        raise ValueError(f"gateway_router must provide a valid route_target, got {target!r}")
    return target


def build_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("entry_router", _entry_router)
    graph.add_node("gateway_router", gateway_router)
    graph.add_node("search_agent", search_agent)
    graph.add_node("discover_agent", discover_agent)
    graph.add_node("recommend_agent", recommend_agent)
    graph.add_node("admin_agent", admin_agent)

    graph.add_edge(START, "entry_router")
    graph.add_conditional_edges(
        "entry_router",
        _route_from_entry,
        {"gateway_router": "gateway_router", "admin_agent": "admin_agent"},
    )
    graph.add_conditional_edges(
        "gateway_router",
        _route_from_gateway,
        {"search_agent": "search_agent", "discover_agent": "discover_agent", "recommend_agent": "recommend_agent"},
    )
    graph.add_edge("search_agent", END)
    graph.add_edge("discover_agent", END)
    graph.add_edge("recommend_agent", END)
    graph.add_edge("admin_agent", END)
    return graph.compile()
