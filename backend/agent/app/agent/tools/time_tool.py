import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.tools import tool

from app.core.agent.middleware import tool_call_status

DEFAULT_AGENT_TIME_ZONE = "Asia/Shanghai"
_WEEKDAY_LABELS = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")

try:
    _AGENT_TZ = ZoneInfo(DEFAULT_AGENT_TIME_ZONE)
except ZoneInfoNotFoundError:
    # Windows 无系统时区库且未安装 tzdata;Asia/Shanghai 恒为 UTC+8
    _AGENT_TZ = datetime.timezone(datetime.timedelta(hours=8))


def _build_current_time_info(now: datetime.datetime | None = None) -> dict:
    timezone = _AGENT_TZ
    resolved_now = now.astimezone(timezone) if now is not None else datetime.datetime.now(timezone)
    date_text = resolved_now.strftime("%Y-%m-%d")
    time_text = resolved_now.strftime("%H:%M:%S")
    weekday = _WEEKDAY_LABELS[resolved_now.weekday()]
    return {
        "timezone": DEFAULT_AGENT_TIME_ZONE,
        "date": date_text,
        "time": time_text,
        "weekday": weekday,
        "display_text": f"当前北京时间:{date_text} {time_text}({weekday})",
    }


@tool(
    description=(
        "获取当前北京时间。"
        "当用户询问今天、现在、当前日期、当前时间、星期几,"
        "或回答需要当前日期时间上下文(如'本周''今天有什么更新')时调用。"
        "只读工具,不需要用户确认。"
    ),
)
@tool_call_status(display_name="获取当前时间")
def get_current_time() -> dict:
    """获取当前北京时间。"""
    return _build_current_time_info()
