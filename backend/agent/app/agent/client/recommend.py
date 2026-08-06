from app.agent.client.collections import user_collections_tools
from app.agent.run import run_domain_agent
from app.agent.time_tool import get_current_time
from app.config import AgentChatModelSlot


def recommend_agent(state):
    return run_domain_agent(
        state,
        slot=AgentChatModelSlot.CLIENT_RECOMMEND,
        tools=[*user_collections_tools, get_current_time],
        prompt_key="client_recommend_agent_prompt",
        prompt_path="client/recommend_agent_prompt.md",
    )
