from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool

from app.agent.client.collections import user_collections_tools
from app.agent.http import call_api
from app.agent.state import AgentState
from app.agent.time_tool import get_current_time
from app.config import AgentChatModelSlot, create_agent_chat_llm
from app.core.agent_runtime import agent_stream
from app.core.event_bus import emit_answer_delta, emit_thinking_delta
from app.core.middleware import build_tool_status_middleware, tool_call_status
from app.core.prompt_sync import load_managed_prompt


@tool
@tool_call_status(display_name="搜索番剧")
def search_subjects(query: str, page: int = 1, size: int = 20) -> list | dict:
    """按关键词搜索番剧。query: 搜索关键词"""
    data = call_api("GET", "/api/user/subjects/search", params={"q": query, "page": page, "size": size})
    return data.get("content") if isinstance(data, dict) else data


@tool
@tool_call_status(display_name="查看番剧详情")
def get_subject_detail(subject_id: int) -> dict:
    """获取番剧详细信息。subject_id: 番剧 ID"""
    return call_api("GET", f"/api/user/subjects/{subject_id}")


@tool
@tool_call_status(display_name="查看剧集列表")
def get_episodes(subject_id: int) -> list:
    """获取番剧的剧集列表。subject_id: 番剧 ID"""
    return call_api("GET", f"/api/user/subjects/{subject_id}/episodes")


@tool
@tool_call_status(display_name="查看标签")
def get_tags() -> list:
    """获取所有标签（按使用次数降序）"""
    return call_api("GET", "/api/user/tags")


@tool
@tool_call_status(display_name="按标签筛选番剧")
def get_subjects_by_tag(tag: str, page: int = 1, size: int = 20) -> list:
    """按标签获取番剧。tag: 标签名称"""
    data = call_api("GET", f"/api/user/tags/{tag}/subjects", params={"page": page, "size": size})
    return data.get("content") if isinstance(data, dict) else data


search_tools = [search_subjects, get_subject_detail, get_episodes, get_tags, get_subjects_by_tag]


def search_agent(state: AgentState) -> dict[str, Any]:
    llm = create_agent_chat_llm(slot=AgentChatModelSlot.CLIENT_SEARCH)
    agent = create_agent(
        model=llm,
        tools=[*search_tools, *user_collections_tools, get_current_time],
        system_prompt=SystemMessage(
            content=load_managed_prompt("client_search_agent_prompt", "client/search_agent_prompt.md")
        ),
        state_schema=AgentState,
        middleware=[build_tool_status_middleware()],
    )
    stream = agent_stream(
        agent,
        list(state.get("history_messages") or []),
        initial_state=state,
        on_model_delta=emit_answer_delta,
        on_thinking_delta=emit_thinking_delta,
    )
    text = stream["streamed_text"]
    return {"result": text, "messages": [AIMessage(content=text)]}
