from app.agent.ports import BusinessGateway
from app.chat.events import AgentEvent, AgentEventType
from app.chat.ports import ChatStore
from app.rag.ports import EmbeddingPort, SubjectIndex, UserPreferenceProvider


def test_agent_event_is_transport_independent():
    event = AgentEvent(type=AgentEventType.ANSWER, text="ok")

    assert event.type == AgentEventType.ANSWER
    assert event.text == "ok"


def test_external_boundaries_are_runtime_checkable_protocols():
    for contract in (BusinessGateway, ChatStore, EmbeddingPort, SubjectIndex, UserPreferenceProvider):
        assert getattr(contract, "_is_runtime_protocol", False) is True
