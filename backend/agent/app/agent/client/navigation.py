"""`request_navigation`：纯 state 写入的导航意图，零 IO、不发事件、不调 LLM。

参数经 Pydantic 卡边界（design D3），非法值返回错误 dict 且**不写 state**。
返回值必须是带 ``ToolMessage`` 的 ``Command``（design D2）：普通返回值只会变成
ToolMessage 内容、不进 state，图的条件边读不到；只写 intent 则会抛 ``ValueError``。
"""
import json
from typing import Annotated, Any, Literal

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict, Field, ValidationError

_YEAR_MIN = 1900
_YEAR_MAX = 2100

class _AnimeIndexParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str | None = None
    tags: list[str] | None = None
    year: int | None = Field(default=None, ge=_YEAR_MIN, le=_YEAR_MAX)
    weekday: int | None = Field(default=None, ge=0, le=6)
    sort: Literal["score", "air_date", "rank", "collection_total"] | None = None
    order: Literal["asc", "desc"] | None = None
    page: int | None = Field(default=None, ge=1)

class _ScheduleParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int | None = Field(default=None, ge=_YEAR_MIN, le=_YEAR_MAX)
    quarter: Literal["spring", "summer", "autumn", "winter"] | None = None
    tab: Literal["0", "1", "2", "3", "4", "5", "6"] | None = None

class _SubjectParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: int = Field(alias="subjectId", gt=0)

class _CollectionsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tab: Literal["all", "1", "2", "3", "4", "5"] | None = None
    page: int | None = Field(default=None, ge=1)

# action 白名单 → 参数模型；None 表示无参数
_PARAM_MODELS: dict[str, type[BaseModel] | None] = {
    "open_anime_index": _AnimeIndexParams,
    "open_schedule": _ScheduleParams,
    "open_subject": _SubjectParams,
    "open_collections": _CollectionsParams,
    "open_profile": None,
}

def build_request_navigation_tool():
    """构建导航工具。

    ponytail: 写入门控属 child 4（composite-write-navigate），本工厂**没有**门控参数。
    删掉占位 `gated` 参数是刻意的：留一个调用期不读的开关，会让 child 4 传 `gated=True`
    却静默不生效。child 4 落地时加回参数与门控 body（三行）。
    """

    @tool
    def request_navigation(
        action: str,
        params: dict[str, Any] | None = None,
        tool_call_id: Annotated[str, InjectedToolCallId] = "",
    ) -> Command:
        """请求前端跳转到只读页面（不执行任何写入）。

        action 取值与参数：
        - open_anime_index: q?, tags?(string[]), year?, weekday?(**0=周日…6=周六**),
          sort?(score/air_date/rank/collection_total), order?(asc/desc), page?
        - open_schedule: year?, quarter?(spring/summer/autumn/winter),
          tab?("0"-"6"，**0=周一…6=周日**；与下面 open_anime_index 的 weekday 相反)
        - open_subject: subjectId（必填，必须是前序工具已解析出的真实 ID，不接受标题）
        - open_collections: tab?(all/1/2/3/4/5), page?
        - open_profile: 无参数
        """
        def _error(message: str) -> Command:
            return Command(update={"messages": [ToolMessage(
                content=json.dumps({"error": True, "message": message}, ensure_ascii=False),
                tool_call_id=tool_call_id,
            )]})

        if action not in _PARAM_MODELS:
            return _error(f"不支持的导航 action：{action}")
        raw = params or {}
        model_cls = _PARAM_MODELS[action]
        if model_cls is None:
            if raw:
                return _error(f"{action} 不接受参数")
            normalized: dict[str, Any] = {}
        else:
            try:
                normalized = model_cls.model_validate(raw).model_dump(exclude_none=True)
            except ValidationError as exc:
                return _error(f"{action} 参数非法：{exc.errors()[0].get('msg', '')}")
        return Command(update={
            "navigation_intent": {"action": action, "params": normalized},
            "messages": [ToolMessage(
                content=json.dumps({"ok": True, "action": action}, ensure_ascii=False),
                tool_call_id=tool_call_id,
            )],
        })

    return request_navigation
