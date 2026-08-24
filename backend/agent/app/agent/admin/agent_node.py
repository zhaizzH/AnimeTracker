from app.agent.admin.tools import ADMIN_TOOL_REGISTRY
from app.agent.dependencies import AgentDependencies
from app.agent.ports import AgentChatModelSlot
from app.agent.run import run_domain_agent


def build_admin_agent(dependencies: AgentDependencies):
    def admin_agent(state):
        return run_domain_agent(
            state,
            slot=AgentChatModelSlot.ADMIN_NODE,
            tools=ADMIN_TOOL_REGISTRY.all_tools,
            prompt_key="admin_agent_prompt",
            prompt_path="admin/admin_agent_prompt.md",
            llm_factory=dependencies.llm_factory,
            prompt_repository=dependencies.prompt_repository,
        )

    return admin_agent
