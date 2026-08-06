from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.agent.http import call_api
from app.core.middleware import tool_call_status
from app.schemas.auth import UserInfo


def _require_user(user: UserInfo | None) -> dict | None:
    if user is None:
        return {"error": True, "message": "用户上下文不可用"}
    return None


@tool
@tool_call_status(display_name="查看我的追番列表")
def get_my_collections(type: int = 0, page: int = 1, size: int = 20,
                       user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """查看当前用户的追番收藏列表。type: 0=全部 1=想看 2=在看 3=看过 4=搁置 5=抛弃；page: 页码；size: 每页数量"""
    err = _require_user(user)
    if err:
        return err
    params = {"page": page, "size": size}
    if type:
        params["type"] = type
    return call_api("GET", "/api/user/collections", params=params, token=user.token)


@tool
@tool_call_status(display_name="查看我的单部追番")
def get_my_collection(subject_id: int,
                      user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """查看当前用户对某部番的收藏状态与进度。subject_id: 番剧 ID"""
    err = _require_user(user)
    if err:
        return err
    return call_api("GET", f"/api/user/collections/{subject_id}", token=user.token)


@tool
@tool_call_status(display_name="查看我的收藏统计")
def get_my_stats(user: Annotated[UserInfo | None, InjectedState("user")] = None) -> dict:
    """查看当前用户各类收藏数量统计（1=想看 2=在看 3=看过 4=搁置 5=抛弃）"""
    err = _require_user(user)
    if err:
        return err
    return call_api("GET", "/api/user/collections/counts", token=user.token)


@tool
@tool_call_status(display_name="获取我的观看画像")
def get_my_watch_profile(cap: int = 50,
                         user: Annotated[UserInfo | None, InjectedState("user")] = None) -> list:
    """获取当前用户观看历史压缩画像，供个性化推荐。cap: 最多取前 N 部"""
    err = _require_user(user)
    if err:
        return err
    data = call_api("GET", "/api/user/collections", params={"page": 1, "size": cap}, token=user.token)
    if isinstance(data, dict) and data.get("error"):
        return data
    items = data.get("content") if isinstance(data, dict) else []
    return [_compact(item) for item in items][:cap]


def _compact(item: dict) -> dict:
    sub = item.get("subject") or {}
    return {
        "name": sub.get("name") or sub.get("nameCn") or "",
        "subject_type": sub.get("type"),
        "score": sub.get("score"),
        "eps": sub.get("eps"),
        "my_progress": item.get("epStatus"),
        "collection_type": item.get("type"),
    }


user_collections_tools = [get_my_collections, get_my_collection, get_my_stats, get_my_watch_profile]
