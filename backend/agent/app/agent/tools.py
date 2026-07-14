import httpx
from langchain_core.tools import tool
from app.config import settings

BASE = settings.backend_base_url


@tool
def search_subjects(query: str, page: int = 1, size: int = 20) -> list:
    """按关键词搜索番剧。query: 搜索关键词"""
    resp = httpx.get(f"{BASE}/subjects/search", params={"q": query, "page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_subject_detail(subject_id: int) -> dict:
    """获取番剧详细信息。subject_id: 番剧 ID"""
    resp = httpx.get(f"{BASE}/subjects/{subject_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


@tool
def get_episodes(subject_id: int) -> list:
    """获取番剧的剧集列表。subject_id: 番剧 ID"""
    resp = httpx.get(f"{BASE}/subjects/{subject_id}/episodes", timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


@tool
def get_schedule(weekday: int = -1, year: int = 0, quarter: str = "") -> dict:
    """按星期获取每周追番列表。weekday: 0=周日 1=周一 ... 6=周六，-1=全部；year: 年份，默认当前年；quarter: spring/summer/autumn/winter"""
    params = {"weekday": weekday, "page": 1, "size": 50}
    if year:
        params["year"] = year
    if quarter:
        params["quarter"] = quarter
    resp = httpx.get(f"{BASE}/subjects/schedule", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


@tool
def get_season_subjects(year: int, quarter: str, page: int = 1, size: int = 20) -> list:
    """按季度获取新番。year: 年份；quarter: spring/summer/autumn/winter"""
    resp = httpx.get(f"{BASE}/subjects/season", params={"year": year, "quarter": quarter, "page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_popular_subjects(page: int = 1, size: int = 10) -> list:
    """获取热度榜（按收藏数降序）"""
    resp = httpx.get(f"{BASE}/subjects", params={"sort": "collectionTotal", "order": "desc", "page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_top_rated(page: int = 1, size: int = 10) -> list:
    """获取评分榜（按评分降序）"""
    resp = httpx.get(f"{BASE}/subjects", params={"sort": "score", "order": "desc", "page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_tags() -> list:
    """获取所有标签（按使用次数降序）"""
    resp = httpx.get(f"{BASE}/tags", timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


@tool
def get_subjects_by_tag(tag: str, page: int = 1, size: int = 20) -> list:
    """按标签获取番剧。tag: 标签名称"""
    resp = httpx.get(f"{BASE}/tags/{tag}/subjects", params={"page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_stats() -> dict:
    """获取番剧统计数据（总数等）"""
    resp = httpx.get(f"{BASE}/subjects", params={"page": 1, "size": 1}, timeout=10)
    resp.raise_for_status()
    data = resp.json()["data"]
    return {"total": data["total"], "page": data["page"], "size": data["size"]}


tools = [
    search_subjects,
    get_subject_detail,
    get_episodes,
    get_schedule,
    get_season_subjects,
    get_popular_subjects,
    get_top_rated,
    get_tags,
    get_subjects_by_tag,
    get_stats,
]
