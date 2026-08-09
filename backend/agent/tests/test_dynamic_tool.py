from langchain.messages import ToolMessage
from langchain_core.tools import tool

from app.core.dynamic_tool import (
    DynamicToolMiddleware,
    DynamicToolingTextConfig,
    ManagedDynamicToolRegistry,
)


@tool
def order_list() -> str:
    """业务工具样例"""
    return "order_list"


@tool
def base_ping() -> str:
    """基础工具样例"""
    return "base_ping"


def _config() -> DynamicToolingTextConfig:
    return DynamicToolingTextConfig(
        list_description="查看可加载工具目录",
        list_tool_name="查看可加载工具目录",
        list_usage_tip="调用 load_tools 时，tool_keys 必须使用目录中的精确工具名。",
        load_description="加载当前任务所需的业务工具",
        load_tool_name="加载业务工具",
        load_success_prefix="已加载以下业务工具：",
    )


def _registry(business: dict | None = None, extra: tuple = ()) -> ManagedDynamicToolRegistry:
    return ManagedDynamicToolRegistry(
        business_tools_by_domain=business or {},
        extra_base_tools=extra,
        text_config=_config(),
    )


def test_duplicate_tool_key_raises():
    try:
        ManagedDynamicToolRegistry(
            business_tools_by_domain={"a": (order_list,), "b": (order_list,)},
            text_config=_config(),
        )
        assert False, "应抛出重复 key 异常"
    except ValueError as exc:
        assert "重复" in str(exc)


def test_all_tools_includes_list_load_and_base():
    reg = _registry(extra=(base_ping,))
    names = {t.name for t in reg.all_tools}
    assert "list_loadable_tools" in names
    assert "load_tools" in names
    assert "base_ping" in names


def test_empty_business_catalog():
    reg = _registry(extra=(base_ping,))
    assert reg.get_business_tool_catalog() == {}
    assert reg.get_business_tool_key_set() == set()


def test_visible_keys_base_only_by_default():
    reg = _registry(business={"a": (order_list,)}, extra=(base_ping,))
    visible = reg.resolve_visible_tool_key_set(None)
    assert "order_list" not in visible
    assert "base_ping" in visible


def test_load_adds_business_tool():
    reg = _registry(business={"a": (order_list,)}, extra=(base_ping,))
    visible = reg.resolve_visible_tool_key_set(["order_list"])
    assert "order_list" in visible


def test_filter_visible_tools_drops_unloaded_business():
    reg = _registry(business={"a": (order_list,)}, extra=(base_ping,))
    kept = reg.filter_visible_tools(request_tools=reg.all_tools, loaded_tool_keys=None)
    names = {t.name for t in kept}
    assert "order_list" not in names
    assert "base_ping" in names


def test_dynamic_middleware_filters_request_tools():
    reg = _registry(business={"a": (order_list,)}, extra=(base_ping,))
    middleware = DynamicToolMiddleware(registry=reg)
    seen = []

    class FakeRequest:
        def __init__(self, tools, state):
            self.tools = tools
            self.state = state

        def override(self, **kw):
            self.tools = kw["tools"]
            return self

    def handler(req):
        seen.append(req)
        return "ok"

    middleware.wrap_model_call(FakeRequest(reg.all_tools, {}), handler)
    names = {t.name for t in seen[0].tools}
    assert "order_list" not in names
    assert "base_ping" in names


def test_load_tools_path_updates_loaded_tool_keys():
    reg = _registry(business={"a": (order_list,)}, extra=(base_ping,))
    load_tool = next(t for t in reg.all_tools if t.name == "load_tools")

    class StubRuntime:
        state = {}
        tool_call_id = "call_dynamic_1"

    result = load_tool.func(tool_keys=["order_list"], runtime=StubRuntime())
    assert result.update["loaded_tool_keys"] == ["order_list"]
    messages = result.update["messages"]
    assert isinstance(messages[0], ToolMessage)
