from app.agent.admin.tools import ADMIN_TOOL_REGISTRY
from app.agent.run import run_domain_agent
from app.config import AgentChatModelSlot


def admin_agent(state):
    return run_domain_agent(
        state,
        slot=AgentChatModelSlot.ADMIN_NODE,
        tools=ADMIN_TOOL_REGISTRY.all_tools,
        prompt_key="admin_agent_prompt",
        prompt_path="admin/admin_agent_prompt.md",
    )
