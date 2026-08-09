from app.agent.admin.tools.import_tool import trigger_recent_import
from app.agent.client.discover import discover_tools
from app.agent.client.search import search_tools
from app.agent.time_tool import get_current_time
from app.core.dynamic_tool import DynamicToolingTextConfig, ManagedDynamicToolRegistry

_ADMIN_TEXT_CONFIG = DynamicToolingTextConfig(
    list_description="查看当前可加载的管理工具精确名称目录。当你不确定工具名时先调用本工具。",
    list_tool_name="查看可加载工具目录",
    list_usage_tip="调用 load_tools 时，tool_keys 必须使用目录中的精确工具名。",
    load_description="加载当前任务所需的管理工具。当需要调用当前不可见的管理工具时必须先调用本工具。",
    load_tool_name="加载管理工具",
    load_success_prefix="已加载以下管理工具：",
)


class AdminToolRegistry(ManagedDynamicToolRegistry):
    def __init__(self) -> None:
        # 工具量少，全部常驻 base；等工具多了再按领域搬入 business_tools_by_domain。
        super().__init__(
            business_tools_by_domain={},
            extra_base_tools=(
                get_current_time,
                trigger_recent_import,
                *discover_tools,
                *search_tools,
            ),
            text_config=_ADMIN_TEXT_CONFIG,
        )


ADMIN_TOOL_REGISTRY = AdminToolRegistry()
