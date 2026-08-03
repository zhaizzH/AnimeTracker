import datetime

from app.agent.tools.time_tool import _build_current_time_info, get_current_time


def test_get_current_time_returns_expected_keys():
    result = get_current_time.func()
    assert set(result) == {"timezone", "date", "time", "weekday", "display_text"}
    assert result["timezone"] == "Asia/Shanghai"


def test_build_current_time_info_with_fixed_now():
    now = datetime.datetime(2026, 8, 3, 14, 30, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    result = _build_current_time_info(now)
    assert result["date"] == "2026-08-03"
    assert result["time"] == "14:30:00"
    assert result["weekday"] == "星期一"
    assert result["display_text"] == "当前北京时间:2026-08-03 14:30:00(星期一)"
