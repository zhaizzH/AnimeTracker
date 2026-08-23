from langchain_core.tools import tool

from app.agent.client.collections import collection_read_tools
from app.agent.client.rag_tools import rag_discover_subjects
from app.agent.http import call_api
from app.agent.run import run_domain_agent
from app.agent.time_tool import get_current_time
from app.config import AgentChatModelSlot
from app.core.middleware import tool_call_status


@tool
@tool_call_status(display_name="查询每周追番日程")
def get_schedule(weekday: int = -1, year: int = 0, quarter: str = "") -> dict:
    """按星期获取每周追番列表。weekday: 0=周日 1=周一 ... 6=周六，-1=全部；year: 年份；quarter: spring/summer/autumn/winter"""
    params = {"weekday": weekday, "page": 1, "size": 50}
    if year:
        params["year"] = year
    if quarter:
        params["quarter"] = quarter
    return call_api("GET", "/api/client/subjects/schedule", params=params)


@tool
@tool_call_status(display_name="查看季度新番")
def get_season_subjects(year: int, quarter: str, page: int = 1, size: int = 20) -> list:
    """按季度获取新番。year: 年份；quarter: spring/summer/autumn/winter"""
    data = call_api("GET", "/api/client/subjects/season", params={"year": year, "quarter": quarter, "page": page, "size": size})
    return data.get("content") if isinstance(data, dict) else data


@tool
@tool_call_status(display_name="查看热度榜")
def get_popular_subjects(page: int = 1, size: int = 10) -> list:
    """获取热度榜（按收藏数降序）"""
    data = call_api("GET", "/api/client/subjects", params={"sort": "collectionTotal", "order": "desc", "page": page, "size": size})
    return data.get("content") if isinstance(data, dict) else data


@tool
@tool_call_status(display_name="查看评分榜")
def get_top_rated(page: int = 1, size: int = 10) -> list:
    """获取评分榜（按评分降序）"""
    data = call_api("GET", "/api/client/subjects", params={"sort": "score", "order": "desc", "page": page, "size": size})
    return data.get("content") if isinstance(data, dict) else data


@tool
@tool_call_status(display_name="查看统计数据")
def get_stats() -> dict:
    """获取番剧统计数据（总数等）"""
    data = call_api("GET", "/api/client/subjects", params={"page": 1, "size": 1})
    if isinstance(data, dict):
        data.setdefault("total", 0)
    return data


discover_tools = [rag_discover_subjects, get_schedule]


def discover_agent(state):
    return run_domain_agent(
        state,
        slot=AgentChatModelSlot.CLIENT_DISCOVER,
        tools=[*discover_tools, *collection_read_tools, get_current_time],
        prompt_key="client_discover_agent_prompt",
        prompt_path="client/discover_agent_prompt.md",
    )
