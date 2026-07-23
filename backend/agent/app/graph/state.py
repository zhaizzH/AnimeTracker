from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from typing import Sequence

from app.schemas.auth import UserInfo


class AgentState(BaseModel):
    """Router Graph 运行时状态"""
    messages: Sequence[BaseMessage]
    user: UserInfo
    next_agent: str | None = None
    final_output: str = ""
    used_tools: list[str] = []


class SubAgentState(BaseModel):
    """Sub-agent 内部 ReAct 循环状态"""
    messages: Sequence[BaseMessage]
    is_done: bool = False
    output: str = ""
    used_tools: list[str] = []
