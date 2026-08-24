from pathlib import Path
import io
import sys


def test_job_entrypoints_live_outside_fastapi_app():
    from jobs.importer.main import parse_args
    from jobs.indexer.main import run_batch
    from jobs.scheduler.main import ImportScheduler

    assert callable(parse_args)
    assert callable(run_batch)
    assert ImportScheduler is not None


def test_import_api_does_not_import_subprocess_adapter():
    source = Path("app/api/import_api.py").read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "import_runner" not in source


def test_subprocess_launcher_runs_importer_as_package_from_agent_root(monkeypatch):
    from app.adapters.subprocess import import_job

    captured = {}
    launcher = import_job.SubprocessImportJobLauncher()
    monkeypatch.setattr(launcher, "sweep_dead_processes", lambda: None)
    monkeypatch.setattr(import_job, "open", lambda *_args, **_kwargs: io.BytesIO(), raising=False)

    def popen(command, **kwargs):
        captured.update(command=command, kwargs=kwargs)
        return object()

    monkeypatch.setattr(import_job.subprocess, "Popen", popen)

    launcher.start_import("full")

    assert captured["command"] == [
        sys.executable,
        "-m",
        "jobs.importer.main",
        "--mode",
        "full",
    ]
    assert captured["kwargs"]["cwd"] == import_job.AGENT_ROOT
