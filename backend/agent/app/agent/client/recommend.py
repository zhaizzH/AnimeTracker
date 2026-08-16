from app.agent.client.actions import action_tools
from app.agent.client.collections import collection_read_tools
from app.agent.run import run_domain_agent
from app.agent.time_tool import get_current_time
from app.config import AgentChatModelSlot

recommend_action_tools = [*action_tools]


def recommend_agent(state):
    return run_domain_agent(
        state,
        slot=AgentChatModelSlot.CLIENT_RECOMMEND,
        tools=[*collection_read_tools, *recommend_action_tools, get_current_time],
        prompt_key="client_recommend_agent_prompt",
        prompt_path="client/recommend_agent_prompt.md",
        include_pending_action=True,
    )
