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
@tool_call_status(display_name="查询每周追番日程")
def get_schedule(weekday: int = -1, year: int = 0, quarter: str = "") -> dict:
    """按星期获取每周追番列表。weekday: 0=周日 1=周一 ... 6=周六，-1=全部；year: 年份；quarter: spring/summer/autumn/winter"""
    params = {"weekday": weekday, "page": 1, "size": 50}
    if year:
        params["year"] = year
    if quarter:
        params["quarter"] = quarter
    return call_api("GET", "/api/user/subjects/schedule", params=params)


@tool
@tool_call_status(display_name="查看季度新番")
def get_season_subjects(year: int, quarter: str, page: int = 1, size: int = 20) -> list:
    """按季度获取新番。year: 年份；quarter: spring/summer/autumn/winter"""
    data = call_api("GET", "/api/user/subjects/season",
                    params={"year": year, "quarter": quarter, "page": page, "size": size})
    return data.get("content") if isinstance(data, dict) else data


@tool
@tool_call_status(display_name="查看热度榜")
def get_popular_subjects(page: int = 1, size: int = 10) -> list:
    """获取热度榜（按收藏数降序）"""
    data = call_api("GET", "/api/user/subjects",
                    params={"sort": "collectionTotal", "order": "desc", "page": page, "size": size})
    return data.get("content") if isinstance(data, dict) else data


@tool
@tool_call_status(display_name="查看评分榜")
def get_top_rated(page: int = 1, size: int = 10) -> list:
    """获取评分榜（按评分降序）"""
    data = call_api("GET", "/api/user/subjects",
                    params={"sort": "score", "order": "desc", "page": page, "size": size})
    return data.get("content") if isinstance(data, dict) else data


@tool
@tool_call_status(display_name="查看统计数据")
def get_stats() -> dict:
    """获取番剧统计数据（总数等）"""
    data = call_api("GET", "/api/user/subjects", params={"page": 1, "size": 1})
    if isinstance(data, dict):
        data.setdefault("total", 0)
    return data


discover_tools = [get_schedule, get_season_subjects, get_popular_subjects, get_top_rated, get_stats]


def discover_agent(state: AgentState) -> dict[str, Any]:
    llm = create_agent_chat_llm(slot=AgentChatModelSlot.CLIENT_DISCOVER)
    agent = create_agent(
        model=llm,
        tools=[*discover_tools, *user_collections_tools, get_current_time],
        system_prompt=SystemMessage(
            content=load_managed_prompt("client_discover_agent_prompt", "client/discover_agent_prompt.md")
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
