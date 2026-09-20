from app.agent.dependencies import AgentDependencies
from app.agent.client.actions import build_action_tools
from app.agent.client.actions.subject_resolution import build_subject_resolution_tools
from app.agent.client.collections import build_collection_read_tools
from app.agent.client.rag_tools import build_rag_tools
from app.agent.ports import AgentChatModelSlot
from app.agent.run import run_domain_agent
from app.agent.time_tool import get_current_time

def build_recommend_agent(dependencies: AgentDependencies):
    _rag_search_subjects, _rag_discover_subjects, rag_recommend_subjects = build_rag_tools(dependencies.retrieval)
    collection_read_tools = build_collection_read_tools(dependencies.business)
    recommend_action_tools = build_action_tools(dependencies.business)
    # 单标题解析复用同一 RAG 用例做模糊回退，不复制检索/证据逻辑
    subject_resolution_tools = build_subject_resolution_tools(dependencies.business, dependencies.retrieval)

    def recommend_agent(state):
        return run_domain_agent(
            state,
            slot=AgentChatModelSlot.CLIENT_RECOMMEND,
            tools=[
                rag_recommend_subjects,
                *subject_resolution_tools,
                *collection_read_tools,
                *recommend_action_tools,
                get_current_time,
            ],
            prompt_key="client_recommend_agent_prompt",
            prompt_path="client/recommend_agent_prompt.md",
            llm_factory=dependencies.llm_factory,
            prompt_repository=dependencies.prompt_repository,
            include_pending_action=True,
        )

    return recommend_agent
