from app.config import AgentChatModelSlot, create_agent_chat_llm
from langchain_community.chat_models.tongyi import ChatTongyi


def test_route_slot_uses_zero_temperature():
    llm = create_agent_chat_llm(AgentChatModelSlot.CLIENT_ROUTE)
    assert isinstance(llm, ChatTongyi)
    assert llm.model_kwargs["temperature"] == 0.0


def test_search_slot_inherits_settings_temperature():
    llm = create_agent_chat_llm(AgentChatModelSlot.CLIENT_SEARCH)
    assert llm.model_kwargs["temperature"] == 0.3  # settings.llm_temperature 默认值
