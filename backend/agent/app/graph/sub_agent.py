import asyncio
import logging
from typing import Literal

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import SubAgentState

logger = logging.getLogger(__name__)


def create_sub_agent(
    name: str,
    tools: list[BaseTool],
    system_prompt: str,
    llm: BaseChatModel,
    max_iterations: int = 5,
):
    """创建一个标准的 ReAct Sub-agent Graph

    内部结构: agent_node → (有条件) → tools_node → agent_node → ...
                                    → (无工具调用) → END
    """
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    async def call_agent(state: SubAgentState) -> dict:
        response = await llm_with_tools.ainvoke([
            SystemMessage(content=system_prompt),
            *state.messages[-10:],
        ])
        if not response.tool_calls:
            return {"output": response.content, "is_done": True, "messages": [response]}
        return {"messages": [response], "is_done": False}

    async def call_tools(state: SubAgentState) -> dict:
        last_msg = state.messages[-1]
        tasks = []
        for tc in last_msg.tool_calls:
            tool = tool_map.get(tc["name"])
            if tool:
                tasks.append(tool.ainvoke(tc["args"]))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        tool_msgs = []
        used = []
        for tc, result in zip(last_msg.tool_calls, results):
            used.append(tc["name"])
            if isinstance(result, Exception):
                content = f"工具 {tc['name']} 调用失败: {str(result)}"
            else:
                content = str(result)
            tool_msgs.append(ToolMessage(content=content, tool_call_id=tc["id"]))
        return {"messages": tool_msgs, "used_tools": used}

    def should_continue(state: SubAgentState) -> Literal["continue", "finish"]:
        if state.is_done:
            return "finish"
        steps = len([m for m in state.messages if isinstance(m, ToolMessage)])
        if steps >= max_iterations:
            logger.warning("子代理 %s 已达到最大迭代次数", name)
            return "finish"
        return "continue"

    builder = StateGraph(SubAgentState)
    builder.add_node("agent", call_agent)
    builder.add_node("tools", call_tools)
    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", should_continue, {
        "continue": "tools", "finish": END,
    })
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=MemorySaver())
