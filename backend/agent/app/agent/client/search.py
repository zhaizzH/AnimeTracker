from app.agent.dependencies import AgentDependencies
from app.agent.client.collections import build_collection_read_tools
from app.agent.client.navigation import build_request_navigation_tool
from app.agent.client.rag_tools import build_rag_tools
from app.agent.ports import AgentChatModelSlot
from app.agent.run import run_domain_agent
from app.agent.time_tool import get_current_time
from app.agent.tools import build_subject_detail_tool, build_episodes_tool


def build_search_agent(dependencies: AgentDependencies):
    rag_search_subjects, _rag_discover_subjects, _rag_recommend_subjects = build_rag_tools(dependencies.retrieval)
    search_tools = [build_subject_detail_tool(dependencies.business), build_episodes_tool(dependencies.business)]
    collection_read_tools = build_collection_read_tools(dependencies.business)

    # 工具在工厂体构建一次：闭包内每请求重建会重造 BaseTool 与 pydantic schema
    navigation_tool = build_request_navigation_tool()

    def search_agent(state):
        return run_domain_agent(
            state,
            slot=AgentChatModelSlot.CLIENT_SEARCH,
            tools=[
                rag_search_subjects,
                *search_tools,
                *collection_read_tools,
                get_current_time,
                # 纯导航请求也可能被路由到这里：导航工具三节点都注册（写工具仍只在 recommend）
                navigation_tool,
            ],
            prompt_key="client_search_agent_prompt",
            prompt_path="client/search_agent_prompt.md",
            llm_factory=dependencies.llm_factory,
            prompt_repository=dependencies.prompt_repository,
        )

    return search_agent
