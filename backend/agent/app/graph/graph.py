import logging
from langgraph.graph import StateGraph, END

from app.graph.state import AgentState
from app.graph.nodes import (
    create_entry_node, create_user_router, create_admin_router,
    create_denied_node, create_sub_agent_node, create_role_router,
)
from app.graph.prompts import SEARCH_PROMPT, DISCOVER_PROMPT, RECOMMEND_PROMPT
from app.tools.user_tools import tools as user_tools

logger = logging.getLogger(__name__)


def create_router_graph(llm, settings, store):
    """构建并返回完整的 Router Graph"""

    # 创建节点
    builder = StateGraph(AgentState)

    builder.add_node("entry", create_entry_node(store))
    builder.add_node("user_router", create_user_router(llm))
    builder.add_node("admin_router", create_admin_router(llm))
    builder.add_node("denied", create_denied_node(llm))
    builder.add_node("search", create_sub_agent_node(
        "search", user_tools, SEARCH_PROMPT, llm, settings.agent_max_iterations))
    builder.add_node("discover", create_sub_agent_node(
        "discover", user_tools, DISCOVER_PROMPT, llm, settings.agent_max_iterations))
    builder.add_node("recommend", create_sub_agent_node(
        "recommend", user_tools, RECOMMEND_PROMPT, llm, settings.agent_max_iterations))

    builder.set_entry_point("entry")

    # 第一层路由：角色分发（entry → role_router 条件边，但不注册为独立节点）
    builder.add_conditional_edges("entry", create_role_router(), {
        "user_router": "user_router",
        "admin_router": "admin_router",
    })

    # 第二层路由：意图分发
    builder.add_conditional_edges("user_router", lambda s: s.next_agent or "search", {
        "search": "search",
        "discover": "discover",
        "recommend": "recommend",
    })

    # ADMIN 路径（当前拒绝）
    builder.add_edge("admin_router", "denied")

    # 所有终点汇聚到 END
    for agent in ("search", "discover", "recommend", "denied"):
        builder.add_edge(agent, END)

    return builder.compile()
