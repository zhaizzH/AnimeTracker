"""`navigation_emitter`：图后路由的纯函数节点。

读 state 的 NavigationIntent → 白名单映射成 path + label → 发 ui_action → 清空 intent。
不挂 LLM、不产 answer 文本；`open_subject` 在这里做权威回查（design D4）。
"""
from collections.abc import Callable
from urllib.parse import urlencode

from app.agent.dependencies import AgentDependencies
from app.agent.state import AgentState
from app.chat.event_sink import emit_ui_action

_QUARTER_LABELS = {"spring": "春", "summer": "夏", "autumn": "秋", "winter": "冬"}
# tab 键 → 中文，与 MyCollections 的 TABS 一致（0/全部 不追加）
_COLLECTION_TAB_LABELS = {"1": "想看", "2": "看过", "3": "在看", "4": "搁置", "5": "抛弃"}

def _with_query(path: str, query: list[tuple[str, str]]) -> str:
    return f"{path}?{urlencode(query)}" if query else path

def _anime_index(params: dict) -> tuple[str, str]:
    query: list[tuple[str, str]] = []
    keyword = (params.get("q") or "").strip()
    if keyword:
        query.append(("q", keyword))
    # tags 是列表 → 重复 tag 键（前端 useSearchParams().getAll('tag')）
    query.extend(("tag", tag) for tag in params.get("tags") or [])
    # 默认值不写入地址栏（与前端 FILTER_DEFAULTS 一致）
    if params.get("page") not in (None, 1):
        query.append(("page", str(params["page"])))
    if params.get("sort") not in (None, "score"):
        query.append(("sort", str(params["sort"])))
    if params.get("order") not in (None, "desc"):
        query.append(("order", str(params["order"])))
    if params.get("year") is not None:
        query.append(("year", str(params["year"])))
    if params.get("weekday") is not None:
        query.append(("weekday", str(params["weekday"])))
    label = "「番剧索引」"
    if params.get("year") is not None:
        label += f" · {params['year']} 年"
    if keyword:
        label += f" · 「{keyword}」"
    return _with_query("/anime", query), label

def _schedule(params: dict) -> tuple[str, str]:
    query: list[tuple[str, str]] = []
    if params.get("year") is not None:
        query.append(("year", str(params["year"])))
    quarter = params.get("quarter")
    if quarter:
        query.append(("quarter", str(quarter)))
    if params.get("tab"):
        query.append(("tab", str(params["tab"])))
    label = "「追番日程」"
    if params.get("year") is not None:
        label += f" · {params['year']} 年"
    if quarter:
        label += f" · {_QUARTER_LABELS.get(str(quarter), '')}季"
    return _with_query("/schedule", query), label

def _collections(params: dict) -> tuple[str, str]:
    query: list[tuple[str, str]] = []
    tab = params.get("tab")
    if tab not in (None, "all"):
        query.append(("tab", str(tab)))
    if params.get("page") not in (None, 1):
        query.append(("page", str(params["page"])))
    label = "「我的收藏」"
    if tab not in (None, "all"):
        label += f" · {_COLLECTION_TAB_LABELS.get(str(tab), '')}"
    return _with_query("/my-collections", query), label

def _profile(_params: dict) -> tuple[str, str]:
    return "/profile", "「个人中心」"

_MAPPING: dict[str, Callable[[dict], tuple[str, str]]] = {
    "open_anime_index": _anime_index,
    "open_schedule": _schedule,
    "open_collections": _collections,
    "open_profile": _profile,
}

def build_navigation_emitter(dependencies: AgentDependencies):
    def navigation_emitter(state: AgentState) -> dict:
        intent = state.get("navigation_intent")
        if not intent:
            return {}
        action = intent.get("action")
        params = intent.get("params") or {}
        if action == "open_subject":
            subject_id = params.get("subject_id")
            # 权威回查：只校验 int > 0 挡不住模型编造的 ID；失败则静默跳过，不白屏跳 404
            detail = dependencies.business.request("GET", f"/api/client/subjects/{subject_id}")
            if not isinstance(detail, dict) or detail.get("error"):
                return {"navigation_intent": None}
            # 优先中文名：浮层提示是中文界面文案，openapi 里 name 是日文/英文名
            # （真机实测：优先 name 会让提示出现「メイドインアビス 目覚める神秘」）
            name = detail.get("nameCn") or detail.get("name") or "条目"
            path, label = f"/subject/{subject_id}", f"「{name}」"
        elif action in _MAPPING:
            path, label = _MAPPING[action](params)
        else:  # 工具已白名单校验，这里只防手写 state
            return {"navigation_intent": None}
        emit_ui_action(action=str(action), params=params, path=path, label=label)
        return {"navigation_intent": None}

    return navigation_emitter
