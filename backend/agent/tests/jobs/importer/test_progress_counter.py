"""R5 导入进度计数（Redis）的键语义与残留防护。

计数键 `animetracker:import:{record_id}:done` 没有 TTL，只在 `main()` 的
`finally` 里删除。importer 被 SIGKILL 时 `finally` 不执行，键会残留；而
`--resume` 会复用同一个 `record_id`（`load_resume_record` + `resume_import_record`），
残留值会被叠加进终态 `subject_count`，使「导入记录」页显示虚高。

`main()` 在拿到导入锁之后、任何 INCR 之前调用 `_clear_done(record_id)` 清零。
本文件锁定该不变式；`main()` 的具体接线由集成/手测覆盖。
"""

from __future__ import annotations

import fakeredis
import pytest

from jobs.importer import main as importer_main

_RECORD_ID = 7
_KEY = f"animetracker:import:{_RECORD_ID}:done"


@pytest.fixture
def redis_client(monkeypatch):
    client = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(importer_main, "_redis_client", client)
    return client


def test_incr_done_accumulates_per_record(redis_client):
    importer_main._incr_done(_RECORD_ID)
    importer_main._incr_done(_RECORD_ID)

    assert redis_client.get(_KEY) == "2"


def test_counters_are_isolated_by_record_id(redis_client):
    importer_main._incr_done(_RECORD_ID)
    importer_main._incr_done(99)

    assert redis_client.get(_KEY) == "1"
    assert redis_client.get("animetracker:import:99:done") == "1"


def test_read_and_clear_returns_total_then_deletes_key(redis_client):
    importer_main._incr_done(_RECORD_ID)
    importer_main._incr_done(_RECORD_ID)

    assert importer_main._read_and_clear_done(_RECORD_ID) == 2
    assert redis_client.get(_KEY) is None


def test_read_and_clear_without_key_returns_zero(redis_client):
    assert importer_main._read_and_clear_done(_RECORD_ID) == 0


def test_read_and_clear_returns_none_on_redis_failure(monkeypatch):
    """Redis 故障时返回 None 而非 0。

    返回 0 会让调用方把一次成功的导入写成 `subject_count=0` 的 COMPLETED；
    返回 None 强制调用方回退到本次运行的内存计数。
    """

    class _Broken:
        def get(self, _key):
            raise RuntimeError("redis down")

        def delete(self, _key):
            raise RuntimeError("redis down")

    monkeypatch.setattr(importer_main, "_redis_client", _Broken())

    assert importer_main._read_and_clear_done(_RECORD_ID) is None


def test_incr_failure_does_not_break_import(monkeypatch):
    """INCR 失败只告警，不影响导入主流程。"""

    class _Broken:
        def incr(self, _key):
            raise RuntimeError("redis down")

    monkeypatch.setattr(importer_main, "_redis_client", _Broken())

    importer_main._incr_done(_RECORD_ID)  # 不应抛出


def test_stale_counter_from_killed_run_is_cleared_before_resume(redis_client):
    """回归：run 1 被硬杀留下计数键，run 2 --resume 复用 record_id。

    清零必须发生在本次 INCR 之前，否则终态 subject_count = 残留 + 本次成功数。
    """
    # run 1：成功 500 条后被 SIGKILL，finally 未执行 → 键残留
    redis_client.set(_KEY, 500)

    # run 2：拿到导入锁 → 清零残留（main() 的 resume 路径）
    importer_main._clear_done(_RECORD_ID)
    assert redis_client.get(_KEY) is None

    # 本次只成功 3 条
    for _ in range(3):
        importer_main._incr_done(_RECORD_ID)

    assert importer_main._read_and_clear_done(_RECORD_ID) == 3
