import pytest

from jobs.importer.main import run_recent


class _CalendarFailureClient:
    def get_calendar(self):
        raise ConnectionError("calendar upstream unavailable")


def test_run_recent_calendar_failure_is_not_an_empty_success():
    with pytest.raises(RuntimeError, match="日历获取失败"):
        run_recent(_CalendarFailureClient(), db=None, resume=False)
