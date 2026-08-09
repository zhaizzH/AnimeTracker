from app.agent.admin.tools import ADMIN_TOOL_REGISTRY
from app.agent.admin.tools.import_tool import trigger_recent_import
from app.api import import_api


def test_trigger_recent_calls_run_import_recent(monkeypatch):
    calls = []
    monkeypatch.setattr(import_api, "run_import", lambda **kw: calls.append(kw) or {"ok": True})
    out = trigger_recent_import.invoke({})
    assert calls == [{"mode": "recent"}]
    assert "已触发" in out


def test_trigger_recent_conflict_returns_friendly(monkeypatch):
    from fastapi import HTTPException

    def boom(**kw):
        raise HTTPException(status_code=409, detail="已有导入任务运行中")

    monkeypatch.setattr(import_api, "run_import", boom)
    out = trigger_recent_import.invoke({})
    assert "已有导入任务" in out
    assert "409" not in out


def test_admin_registry_keeps_import_resident():
    assert "trigger_recent_import" in {t.name for t in ADMIN_TOOL_REGISTRY.base_tools}
    names = {t.name for t in ADMIN_TOOL_REGISTRY.all_tools}
    assert "trigger_recent_import" in names
    assert "search_subjects" in names
    assert "get_schedule" in names
    assert "get_current_time" in names


def test_admin_registry_business_domains_dormant():
    assert ADMIN_TOOL_REGISTRY.get_business_tool_catalog() == {}
