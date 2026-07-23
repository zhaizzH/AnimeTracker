import logging
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.graph.prompts import ROUTER_PROMPT, ADMIN_DENIED_PROMPT
from app.graph.state import AgentState
from app.graph.sub_agent import create_sub_agent

logger = logging.getLogger(__name__)


def create_entry_node(store):
    """创建入口节点：解析用户信息、加载历史"""
    async def entry(state: AgentState) -> dict:
        user = state.user
        session_id = state.messages[-1].additional_kwargs.get("session_id", "")
        if session_id:
            history = store.get_messages(session_id)
            if history:
                base_msgs = []
                for m in history:
                    if m.role == "user":
                        base_msgs.append(HumanMessage(content=m.content))
                    else:
                        base_msgs.append(AIMessage(content=m.content))
                return {"messages": base_msgs}
        return {}
    return entry


def create_user_router(llm):
    """创建用户路由节点：LLM 判断意图"""
    async def user_router(state: AgentState) -> dict:
        query = ""
        for m in reversed(state.messages):
            if isinstance(m, HumanMessage):
                query = m.content
                break
        history_summary = ""
        if len(state.messages) > 1:
            history_summary = f"共 {len(state.messages)} 条消息，最近提问: {query[:50]}"
        prompt = ROUTER_PROMPT.format(
            role=state.user.role,
            date=datetime.now().strftime("%Y-%m-%d %A"),
            history_summary=history_summary,
            query=query,
        )
        resp = await llm.ainvoke([SystemMessage(content=prompt)])
        agent = resp.content.strip().lower()
        if agent not in ("search", "discover", "recommend"):
            agent = "search"
        logger.info("Router: user=%s query=%s -> %s", state.user.user_id, query[:30], agent)
        return {"next_agent": agent}
    return user_router


def create_admin_router(llm):
    """创建管理员路由节点（Phase 2 实现）"""
    async def admin_router(state: AgentState) -> dict:
        return {"next_agent": "denied"}
    return admin_router


def create_denied_node(llm):
    """创建无权限节点"""
    async def denied(state: AgentState) -> dict:
        resp = await llm.ainvoke([SystemMessage(
            ADMIN_DENIED_PROMPT.format(username=state.user.username)
        )])
        return {"final_output": resp.content}
    return denied


def create_sub_agent_node(name, tools, prompt, llm, max_iterations=5):
    """创建 Sub-agent 节点工厂"""
    sub_graph = create_sub_agent(name, tools, prompt, llm, max_iterations)

    async def node_func(state: AgentState) -> dict:
        sub_state = {
            "messages": list(state.messages[-10:]),
            "is_done": False,
            "output": "",
            "used_tools": [],
        }
        result = await sub_graph.ainvoke(sub_state)
        return {
            "final_output": result.get("output", ""),
            "used_tools": result.get("used_tools", []),
        }
    return node_func


def create_role_router():
    """创建角色路由节点：根据用户角色分发"""
    def role_router(state: AgentState) -> str:
        if state.user.role == "ADMIN":
            return "admin_router"
        return "user_router"
    return role_router
