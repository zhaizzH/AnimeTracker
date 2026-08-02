import httpx
from langchain_core.tools import tool

from app.config import settings
from app.core.agent.middleware import tool_call_status

BASE = settings.backend_base_url


def _safe_call(func):
    try:
        return func()
    except httpx.TimeoutException:
        return {"error": True, "message": "后端服务超时"}
    except httpx.HTTPStatusError as e:
        return {"error": True, "message": f"后端返回错误: {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"error": True, "message": f"后端服务不可用: {str(e)}"}


@tool
@tool_call_status(display_name="查询每周追番日程")
def get_schedule(weekday: int = -1, year: int = 0, quarter: str = "") -> dict:
    """按星期获取每周追番列表。weekday: 0=周日 1=周一 ... 6=周六，-1=全部；year: 年份；quarter: spring/summer/autumn/winter"""
    params = {"weekday": weekday, "page": 1, "size": 50}
    if year:
        params["year"] = year
    if quarter:
        params["quarter"] = quarter
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/schedule", params=params, timeout=10
    ).raise_for_status().json()["data"])


@tool
@tool_call_status(display_name="查看季度新番")
def get_season_subjects(year: int, quarter: str, page: int = 1, size: int = 20) -> list:
    """按季度获取新番。year: 年份；quarter: spring/summer/autumn/winter"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/season",
        params={"year": year, "quarter": quarter, "page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
@tool_call_status(display_name="查看热度榜")
def get_popular_subjects(page: int = 1, size: int = 10) -> list:
    """获取热度榜（按收藏数降序）"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects", params={"sort": "collectionTotal", "order": "desc", "page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
@tool_call_status(display_name="查看评分榜")
def get_top_rated(page: int = 1, size: int = 10) -> list:
    """获取评分榜（按评分降序）"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects", params={"sort": "score", "order": "desc", "page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
@tool_call_status(display_name="查看统计数据")
def get_stats() -> dict:
    """获取番剧统计数据（总数等）"""
    def _call():
        data = httpx.get(
            f"{BASE}/api/user/subjects", params={"page": 1, "size": 1}, timeout=10
        ).raise_for_status().json()["data"]
        data.setdefault("total", 0)
        return data
    return _safe_call(_call)


discover_tools = [get_schedule, get_season_subjects, get_popular_subjects, get_top_rated, get_stats]
