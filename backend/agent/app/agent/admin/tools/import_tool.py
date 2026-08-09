from langchain_core.tools import tool

from app.core import import_runner
from app.core.middleware import tool_call_status


@tool
@tool_call_status(display_name="导入最近新番")
def trigger_recent_import() -> str:
    """触发一次 recent 模式的番剧数据导入：从 Bangumi 放送日历拉取本周更新条目写入库。
    仅支持 recent 档位；season/full/since 模式的导入不要调用本工具，
    请直接提示管理员前往管理后台的「数据导入」页面手动操作。"""
    try:
        import_runner.run_import(mode="recent")
    except import_runner.ImportAlreadyRunning:
        return "已有导入任务在运行中，请到数据导入界面查看进度。"
    except ValueError:
        return "导入触发失败，请到数据导入界面手动操作。"
    return "已触发 recent 模式导入，进度请到数据导入界面查看。"
