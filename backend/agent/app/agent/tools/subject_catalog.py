from langchain_core.tools import tool

from app.agent.middleware import tool_call_status
from app.agent.ports import BusinessGateway


def build_subject_catalog_tools(business: BusinessGateway) -> tuple:
    @tool
    @tool_call_status(display_name="搜索番剧")
    def search_subjects(query: str, page: int = 1, size: int = 20) -> list | dict:
        """按关键词搜索番剧。query: 搜索关键词"""
        data = business.request("GET", "/api/client/subjects/search", params={"q": query, "page": page, "size": size})
        return data.get("content") if isinstance(data, dict) else data

    @tool
    @tool_call_status(display_name="查看番剧详情")
    def get_subject_detail(subject_id: int) -> dict:
        """获取番剧详细信息。subject_id: 番剧 ID"""
        return business.request("GET", f"/api/client/subjects/{subject_id}")

    @tool
    @tool_call_status(display_name="查看剧集列表")
    def get_episodes(subject_id: int) -> list:
        """获取番剧的剧集列表。subject_id: 番剧 ID"""
        return business.request("GET", f"/api/client/subjects/{subject_id}/episodes")

    @tool
    @tool_call_status(display_name="按标签筛选番剧")
    def get_subjects_by_tag(tag: str, page: int = 1, size: int = 20) -> list:
        """按标签获取番剧。tag: 标签名称"""
        data = business.request("GET", f"/api/client/tags/{tag}/subjects", params={"page": page, "size": size})
        return data.get("content") if isinstance(data, dict) else data

    @tool
    @tool_call_status(display_name="查询每周追番日程")
    def get_schedule(weekday: int = -1, year: int = 0, quarter: str = "") -> dict:
        """按星期获取每周追番列表。weekday: 0=周日 1=周一 ... 6=周六，-1=全部；year: 年份；quarter: spring/summer/autumn/winter"""
        params = {"weekday": weekday, "page": 1, "size": 50}
        if year:
            params["year"] = year
        if quarter:
            params["quarter"] = quarter
        return business.request("GET", "/api/client/subjects/schedule", params=params)

    @tool
    @tool_call_status(display_name="查看季度新番")
    def get_season_subjects(year: int, quarter: str, page: int = 1, size: int = 20) -> list:
        """按季度获取新番。year: 年份；quarter: spring/summer/autumn/winter"""
        data = business.request(
            "GET",
            "/api/client/subjects/season",
            params={"year": year, "quarter": quarter, "page": page, "size": size},
        )
        return data.get("content") if isinstance(data, dict) else data

    @tool
    @tool_call_status(display_name="查看热度榜")
    def get_popular_subjects(page: int = 1, size: int = 10) -> list:
        """获取热度榜（按收藏数降序）"""
        data = business.request(
            "GET",
            "/api/client/subjects",
            params={"sort": "collectionTotal", "order": "desc", "page": page, "size": size},
        )
        return data.get("content") if isinstance(data, dict) else data

    @tool
    @tool_call_status(display_name="查看评分榜")
    def get_top_rated(page: int = 1, size: int = 10) -> list:
        """获取评分榜（按评分降序）"""
        data = business.request(
            "GET",
            "/api/client/subjects",
            params={"sort": "score", "order": "desc", "page": page, "size": size},
        )
        return data.get("content") if isinstance(data, dict) else data

    @tool
    @tool_call_status(display_name="查看统计数据")
    def get_stats() -> dict:
        """获取番剧统计数据（总数等）"""
        data = business.request("GET", "/api/client/subjects", params={"page": 1, "size": 1})
        if isinstance(data, dict):
            data.setdefault("total", 0)
        return data

    return (
        search_subjects,
        get_subject_detail,
        get_episodes,
        get_subjects_by_tag,
        get_schedule,
        get_season_subjects,
        get_popular_subjects,
        get_top_rated,
        get_stats,
    )
