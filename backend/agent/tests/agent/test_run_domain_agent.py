"""design D1：嵌套图（create_agent）里工具写的 ``navigation_intent`` 必须由 run_domain_agent 回传。

不回传时外层图的条件边永远读不到 intent，emitter 永不执行且**没有任何报错**。
"""
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.agent.client.navigation import build_request_navigation_tool
from app.agent.ports import AgentChatModelSlot
from app.agent.run import run_domain_agent

class _ToolCallingModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "fake-tool-calling"

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001, ANN201 - 测试替身
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        if any(isinstance(m, ToolMessage) for m in messages):
            reply = AIMessage(content="好的")
        else:
            reply = AIMessage(
                content="",
                tool_calls=[{"name": "request_navigation", "args": {"action": "open_profile"}, "id": "call_1"}],
            )
        return ChatResult(generations=[ChatGeneration(message=reply)])

class _LlmFactory:
    provider = "fake"

    def create(self, slot, *, temperature=None):  # noqa: ANN001, ANN201 - 测试替身
        return _ToolCallingModel()

class _PromptRepository:
    def get(self, key, path):  # noqa: ANN001, ANN201 - 测试替身
        return "你是测试助手"

def test_navigation_intent_written_by_nested_tool_is_relayed() -> None:
    result = run_domain_agent(
        {"history_messages": [HumanMessage(content="打开个人中心")], "navigation_intent": None},
        slot=AgentChatModelSlot.CLIENT_SEARCH,
        tools=[build_request_navigation_tool()],
        prompt_key="client_search_agent_prompt",
        prompt_path="client/search_agent_prompt.md",
        llm_factory=_LlmFactory(),
        prompt_repository=_PromptRepository(),
    )

    assert result["navigation_intent"] == {"action": "open_profile", "params": {}}
    assert result["result"] == "好的"
