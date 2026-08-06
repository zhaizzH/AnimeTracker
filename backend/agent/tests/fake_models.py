from typing import Any, List

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field


class ToolCallingFakeModel(BaseChatModel):
    """两轮假模型：turn=0 发 tool_name 的工具调用，次轮输出 final_text。"""

    turn: int = Field(default=0)
    tool_name: str = "get_me"
    final_text: str = "done"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(
        self,
        messages: List[BaseMessage],
        stop=None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> ChatResult:
        if self.turn == 0:
            self.turn += 1
            message = AIMessage(content="", tool_calls=[{
                "name": self.tool_name, "args": {}, "id": "call_1", "type": "tool_call",
            }])
        else:
            message = AIMessage(content=self.final_text)
        return ChatResult(generations=[ChatGeneration(message=message)])

    @property
    def _llm_type(self) -> str:
        return "tool_calling_fake"
