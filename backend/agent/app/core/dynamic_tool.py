"""动态工具加载共享协议（自 medicine-ai-agent 移植，适配 AnimeTracker 工具装饰器）。

机制：agent 只常驻 base 工具 + list/load 两个协议工具；业务工具按领域分组，
运行时经 load_tools 注入后对模型可见。AnimeTracker 当前业务领域为空，
全部工具常驻 base；等工具增多再按领域搬入 business_tools_by_domain。
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_core.tools import BaseTool
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.middleware import tool_call_status


@dataclass(frozen=True)
class DynamicToolingTextConfig:
    list_description: str
    list_tool_name: str
    list_usage_tip: str
    load_description: str
    load_tool_name: str
    load_success_prefix: str
    load_completion_message: str = (
        "这些工具无需用户确认；你可以继续直接调用已加载的实际工具名完成任务。"
    )


class LoadToolsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_keys: list[str] = Field(
        min_length=1,
        description="需要加载的业务工具 key 数组，只允许 snake_case 工具名",
    )

    @field_validator("tool_keys")
    @classmethod
    def normalize_tool_keys(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for raw in value:
            key = str(raw or "").strip().lower()
            if not key:
                raise ValueError("tool_keys 不能包含空值")
            if key not in normalized:
                normalized.append(key)
        if not normalized:
            raise ValueError("tool_keys 不能为空")
        return normalized


class LoadableToolsCatalog(BaseModel):
    exact_tool_names: list[str]
    tools_by_domain: dict[str, list[str]]
    supports_multi_load: bool
    usage_tip: str


class DynamicToolRegistryProtocol(Protocol):
    def filter_visible_tools(
        self, *, request_tools: list[Any], loaded_tool_keys: list[str] | None
    ) -> list[Any]: ...


def normalize_loaded_tool_keys(state: Any) -> list[str] | None:
    if not isinstance(state, Mapping):
        return None
    raw = state.get("loaded_tool_keys")
    if not isinstance(raw, list):
        return None
    normalized: list[str] = []
    for key in raw:
        k = str(key or "").strip()
        if k and k not in normalized:
            normalized.append(k)
    return normalized


def merge_unique_loaded_tool_keys(existing: list[str], requested: list[str]) -> list[str]:
    merged: list[str] = []
    for key in [*existing, *requested]:
        k = str(key or "").strip()
        if k and k not in merged:
            merged.append(k)
    return merged


def extract_loaded_tool_keys_from_stream_result(stream_result: dict[str, Any]) -> list[str]:
    latest_state = stream_result.get("latest_state")
    normalized = normalize_loaded_tool_keys(latest_state)
    return normalized if normalized is not None else []


class DynamicToolMiddleware(AgentMiddleware):
    """根据状态中的 loaded_tool_keys 动态过滤模型可见工具。"""

    def __init__(self, *, registry: DynamicToolRegistryProtocol) -> None:
        self._registry = registry

    def _filter_request_tools(self, request: ModelRequest) -> ModelRequest:
        request_tools = list(request.tools)
        state_dict = request.state if isinstance(request.state, Mapping) else {}
        visible = self._registry.filter_visible_tools(
            request_tools=request_tools,
            loaded_tool_keys=normalize_loaded_tool_keys(state_dict),
        )
        return request.override(tools=visible)

    def wrap_model_call(self, request, handler):
        return handler(self._filter_request_tools(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._filter_request_tools(request))


class ManagedDynamicToolRegistry:
    """动态工具注册中心共享基类。"""

    def __init__(
        self,
        *,
        business_tools_by_domain: dict[str, tuple[BaseTool, ...]],
        extra_base_tools: tuple[BaseTool, ...] = (),
        text_config: DynamicToolingTextConfig,
    ) -> None:
        self._text_config = text_config
        self._business_tools_by_domain = dict(business_tools_by_domain)
        self._business_tools: tuple[BaseTool, ...] = tuple(
            tool_obj
            for domain_tools in self._business_tools_by_domain.values()
            for tool_obj in domain_tools
        )
        self._list_loadable_tools = create_list_loadable_tools_tool(
            get_tool_catalog=self.get_business_tool_catalog,
            text_config=self._text_config,
        )
        self._load_tools = create_load_tools_tool(
            get_allowed_tool_keys=self.get_business_tool_key_set,
            text_config=self._text_config,
        )
        self._base_tools: tuple[BaseTool, ...] = (
            self._list_loadable_tools,
            self._load_tools,
            *extra_base_tools,
        )
        self._managed_tools: tuple[BaseTool, ...] = (*self._base_tools, *self._business_tools)
        self._tool_by_key = self._build_tool_index(self._managed_tools)

    @staticmethod
    def _build_tool_index(tools: tuple[BaseTool, ...]) -> dict[str, BaseTool]:
        index: dict[str, BaseTool] = {}
        for t in tools:
            key = str(getattr(t, "name", "") or "").strip()
            if not key:
                raise ValueError("工具缺少 name，无法注册")
            if key in index:
                raise ValueError(f"工具 key 重复：{key}")
            index[key] = t
        return index

    @property
    def all_tools(self) -> list[BaseTool]:
        return list(self._managed_tools)

    @property
    def base_tools(self) -> list[BaseTool]:
        return list(self._base_tools)

    def get_business_tool_key_set(self) -> set[str]:
        return {str(t.name).strip() for t in self._business_tools}

    def get_business_tool_catalog(self) -> dict[str, list[str]]:
        return {
            domain: [str(t.name).strip() for t in tools if str(t.name).strip()]
            for domain, tools in self._business_tools_by_domain.items()
        }

    def get_base_tool_key_set(self) -> set[str]:
        return {str(t.name).strip() for t in self._base_tools}

    def get_managed_tool_key_set(self) -> set[str]:
        return set(self._tool_by_key.keys())

    def resolve_visible_tool_key_set(self, loaded_tool_keys: list[str] | None) -> set[str]:
        visible = self.get_base_tool_key_set()
        if not loaded_tool_keys:
            return visible
        for key in loaded_tool_keys:
            k = str(key or "").strip()
            if k in self.get_business_tool_key_set():
                visible.add(k)
        return visible

    def filter_visible_tools(
        self, *, request_tools: list[Any], loaded_tool_keys: list[str] | None
    ) -> list[Any]:
        visible_keys = self.resolve_visible_tool_key_set(loaded_tool_keys)
        managed_keys = self.get_managed_tool_key_set()
        result: list[Any] = []
        for t in request_tools:
            key = str(getattr(t, "name", "") or "").strip()
            if not key or key not in managed_keys or key in visible_keys:
                result.append(t)
        return result


def create_list_loadable_tools_tool(*, get_tool_catalog, text_config) -> Any:
    @tool(description=text_config.list_description)
    @tool_call_status(display_name=text_config.list_tool_name)
    def list_loadable_tools() -> LoadableToolsCatalog:
        tools_by_domain = get_tool_catalog()
        exact: list[str] = []
        for names in tools_by_domain.values():
            for name in names:
                if name and name not in exact:
                    exact.append(name)
        return LoadableToolsCatalog(
            exact_tool_names=exact,
            tools_by_domain=tools_by_domain,
            supports_multi_load=True,
            usage_tip=text_config.list_usage_tip,
        )

    return list_loadable_tools


def create_load_tools_tool(*, get_allowed_tool_keys, text_config) -> Any:
    @tool(description=text_config.load_description)
    @tool_call_status(display_name=text_config.load_tool_name)
    def load_tools(tool_keys: list[str], runtime: ToolRuntime[None, Any]) -> Command:
        validated = LoadToolsRequest.model_validate({"tool_keys": tool_keys})
        normalized = validated.tool_keys
        allowed = get_allowed_tool_keys()
        unresolved = [k for k in normalized if k not in allowed]
        if unresolved:
            raise ValueError("不允许加载以下工具: " + ", ".join(unresolved))

        state = runtime.state if isinstance(runtime.state, Mapping) else {}
        merged = merge_unique_loaded_tool_keys(
            existing=normalize_loaded_tool_keys(state) or [],
            requested=normalized,
        )
        message = ToolMessage(
            content=f"{text_config.load_success_prefix}{', '.join(normalized)}\n{text_config.load_completion_message}",
            tool_call_id=runtime.tool_call_id,
        )
        return Command(update={"messages": [message], "loaded_tool_keys": merged})

    return load_tools


__all__ = [
    "DynamicToolMiddleware",
    "DynamicToolRegistryProtocol",
    "DynamicToolingTextConfig",
    "LoadToolsRequest",
    "LoadableToolsCatalog",
    "ManagedDynamicToolRegistry",
    "create_list_loadable_tools_tool",
    "create_load_tools_tool",
    "extract_loaded_tool_keys_from_stream_result",
    "merge_unique_loaded_tool_keys",
    "normalize_loaded_tool_keys",
]
