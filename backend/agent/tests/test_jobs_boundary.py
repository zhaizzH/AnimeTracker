from pathlib import Path


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
