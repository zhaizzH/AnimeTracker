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
@tool_call_status(display_name="搜索番剧")
def search_subjects(query: str, page: int = 1, size: int = 20) -> list | dict:
    """按关键词搜索番剧。query: 搜索关键词"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/search", params={"q": query, "page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
@tool_call_status(display_name="查看番剧详情")
def get_subject_detail(subject_id: int) -> dict:
    """获取番剧详细信息。subject_id: 番剧 ID"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/{subject_id}", timeout=10
    ).raise_for_status().json()["data"])


@tool
@tool_call_status(display_name="查看剧集列表")
def get_episodes(subject_id: int) -> list:
    """获取番剧的剧集列表。subject_id: 番剧 ID"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/{subject_id}/episodes", timeout=10
    ).raise_for_status().json()["data"])


@tool
@tool_call_status(display_name="查看标签")
def get_tags() -> list:
    """获取所有标签（按使用次数降序）"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/tags", timeout=10
    ).raise_for_status().json()["data"])


@tool
@tool_call_status(display_name="按标签筛选番剧")
def get_subjects_by_tag(tag: str, page: int = 1, size: int = 20) -> list:
    """按标签获取番剧。tag: 标签名称"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/tags/{tag}/subjects", params={"page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


search_tools = [search_subjects, get_subject_detail, get_episodes, get_tags, get_subjects_by_tag]
