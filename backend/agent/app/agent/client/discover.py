from app.agent.dependencies import AgentDependencies
from app.agent.client.collections import build_collection_read_tools
from app.agent.client.navigation import build_request_navigation_tool
from app.agent.client.rag_tools import build_rag_tools
from app.agent.ports import AgentChatModelSlot
from app.agent.run import run_domain_agent
from app.agent.time_tool import get_current_time
from app.agent.tools import build_schedule_tool


def build_discover_agent(dependencies: AgentDependencies):
    _rag_search_subjects, rag_discover_subjects, _rag_recommend_subjects = build_rag_tools(dependencies.retrieval)
    discover_tools = [build_schedule_tool(dependencies.business)]
    collection_read_tools = build_collection_read_tools(dependencies.business)

    # 工具在工厂体构建一次：闭包内每请求重建会重造 BaseTool 与 pydantic schema
    navigation_tool = build_request_navigation_tool()

    def discover_agent(state):
        return run_domain_agent(
            state,
            slot=AgentChatModelSlot.CLIENT_DISCOVER,
            tools=[
                rag_discover_subjects,
                *discover_tools,
                *collection_read_tools,
                get_current_time,
                navigation_tool,
            ],
            prompt_key="client_discover_agent_prompt",
            prompt_path="client/discover_agent_prompt.md",
            llm_factory=dependencies.llm_factory,
            prompt_repository=dependencies.prompt_repository,
        )

    return discover_agent
