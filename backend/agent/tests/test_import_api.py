import sys
from datetime import datetime

import pytest
from fastapi import HTTPException

import app.api.import_api as import_api
import app.core.import_runner as runner


class FakeProc:
    """模拟 subprocess.Popen：poll() 返回进程退出码（None=存活）。

    作为 Popen 使用时首参是 cmd 列表（视为刚启动的存活进程）；直接构造时
    首参为退出码。忽略其余 Popen 启动 kwargs。
    """
    def __init__(self, exit_code=None, **kw):
        self._code = None if isinstance(exit_code, list) else exit_code

    def poll(self):
        return self._code


class FakeSubprocess:
    STDOUT = -2
    Popen = FakeProc


def _reset_gate(monkeypatch):
    runner._proc = None
    monkeypatch.setattr(runner, "_sweep_stale_records", lambda: None)


def test_invalid_mode_rejected(monkeypatch):
    _reset_gate(monkeypatch)
    with pytest.raises(HTTPException) as exc:
        import_api.run_import(mode="bogus")
    assert exc.value.status_code == 400


def test_season_requires_key(monkeypatch):
    _reset_gate(monkeypatch)
    with pytest.raises(HTTPException) as exc:
        import_api.run_import(mode="season")
    assert exc.value.status_code == 400


def test_since_requires_since(monkeypatch):
    _reset_gate(monkeypatch)
    with pytest.raises(HTTPException) as exc:
        import_api.run_import(mode="since")
    assert exc.value.status_code == 400


def test_spawns_importer_with_args(monkeypatch):
    runner._proc = None
    monkeypatch.setattr(runner, "_sweep_stale_records", lambda: None)
    spawned = []

    class FakePopen(FakeProc):
        def __init__(self, cmd, **kw):
            super().__init__(None)
            spawned.append((cmd, kw))

    class FakeSub(FakeSubprocess):
        Popen = FakePopen

    monkeypatch.setattr(runner, "subprocess", FakeSub())

    import_api.run_import(mode="season", key="2026-summer", workers=5)

    cmd, kw = spawned[0]
    assert cmd[0] == sys.executable
    assert cmd[1] == str(runner.IMPORTER_SCRIPT)
    assert "--mode" in cmd and cmd[cmd.index("--mode") + 1] == "season"
    assert cmd[cmd.index("--key") + 1] == "2026-summer"
    assert cmd[cmd.index("--workers") + 1] == "5"
    assert kw["cwd"] == runner.AGENT_ROOT


def test_second_run_conflicts_while_alive(monkeypatch):
    runner._proc = None
    monkeypatch.setattr(runner, "_sweep_stale_records", lambda: None)
    monkeypatch.setattr(runner, "subprocess", FakeSubprocess())

    import_api.run_import(mode="recent")
    with pytest.raises(HTTPException) as exc:
        import_api.run_import(mode="recent")
    assert exc.value.status_code == 409


def test_sweep_clears_dead_process_and_flips_records(monkeypatch):
    runner._proc = FakeProc(exit_code=0)  # 上一进程已退出
    flipped = []
    monkeypatch.setattr(runner, "_sweep_stale_records", lambda: flipped.append(1))
    monkeypatch.setattr(runner, "subprocess", FakeSubprocess())

    import_api.run_import(mode="recent")

    assert flipped  # 进程死亡后触发了兜底翻 FAILED
    assert runner._proc is not None  # 门禁已释放并启动了新进程


class FakeResult:
    def __init__(self, rows=None, scalar_value=None):
        self._rows = rows or []
        self._scalar_value = scalar_value

    def scalar(self):
        return self._scalar_value

    def mappings(self):
        return self

    def all(self):
        return self._rows


def test_status_sweeps_then_returns_aggregate(monkeypatch):
    swept = []
    monkeypatch.setattr(import_api, "sweep_dead_processes", lambda: swept.append(1))

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, stmt):
            if "COUNT" in str(stmt):
                return FakeResult(scalar_value=42)
            return FakeResult([{
                "id": 3,
                "season_key": "2026-summer",
                "status": "COMPLETED",
                "subject_count": 7,
                "started_at": datetime(2026, 8, 1, 10, 0, 0),
                "completed_at": datetime(2026, 8, 1, 10, 5, 0),
                "error_message": None,
            }])

    monkeypatch.setattr(import_api, "db_session", lambda: FakeSession())

    payload = import_api.import_status()

    assert swept  # 状态轮询也触发孤儿清扫
    assert payload["totalSubjects"] == 42  # 真实条目总数，而非记录条数
    records = payload["recentRecords"]
    assert records[0]["season"] == "2026-summer"
    assert records[0]["completedAt"] == "2026-08-01T10:05:00"  # ISO-T，Java LocalDateTime 可解析
    assert payload["lastImportedAt"] == "2026-08-01T10:05:00"
