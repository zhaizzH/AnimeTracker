from __future__ import annotations

from jobs.importer.repository import ImportCheckpoint


class CatalogClient:
    def __init__(self, ids):
        self.ids = ids
        self.calls = []

    def iter_subject_ids(self, subject_type=2, limit=100):
        self.calls.append({"type": subject_type, "limit": limit})
        yield from self.ids


def test_full_scan_uses_catalog_iterator_without_year_and_deduplicates(monkeypatch):
    from jobs.importer import main

    client = CatalogClient([3, 1, 3, 2])
    batches = []
    monkeypatch.setattr(main, "_run_batch", lambda ids, *_args, **kwargs: batches.append((list(ids), kwargs)) or len(ids))
    monkeypatch.setattr(main, "run_recent", lambda *_args, **_kwargs: 0)

    assert main.run_full(client, None, False, limit=3, access_token="", user_agent="", host="", port=0, user="", password="", db_name="") == 3
    assert client.calls == [{"type": 2, "limit": 100}]
    assert batches == [([3, 1, 2], {"base_done": 3, "access_token": "", "user_agent": "", "host": "", "port": 0, "user": "", "password": "", "db_name": ""})]


def test_full_scan_preserves_checkpoint_for_catalog_snapshot(monkeypatch):
    from jobs.importer import main

    client = CatalogClient([10, 20, 30])
    checkpoint = ImportCheckpoint("full", 1, 10, main._ids_sha256([10, 20, 30]))
    captured = {}
    monkeypatch.setattr(main, "_run_batch", lambda ids, *_args, **kwargs: captured.update(ids=list(ids), kwargs=kwargs) or 2)
    monkeypatch.setattr(main, "run_recent", lambda *_args, **_kwargs: 0)

    assert main.run_full(client, None, True, resume_checkpoint=checkpoint, access_token="", user_agent="", host="", port=0, user="", password="", db_name="") == 2
    assert captured["ids"] == [10, 20, 30]
    assert captured["kwargs"]["resume_checkpoint"] == checkpoint


def test_full_scan_runs_recent_catchup_without_reusing_full_checkpoint(monkeypatch):
    from jobs.importer import main

    calls = []
    monkeypatch.setattr(main, "_run_batch", lambda ids, *_args, **_kwargs: len(list(ids)))
    monkeypatch.setattr(main, "run_recent", lambda *_args, **kwargs: calls.append(kwargs) or 4)

    assert main.run_full(CatalogClient([1]), None, False, record_id=7, mode="full", resume_checkpoint=ImportCheckpoint("full", 0, None, main._ids_sha256([1])), access_token="", user_agent="", host="", port=0, user="", password="", db_name="") == 5
    assert "record_id" not in calls[0]
    assert "resume_checkpoint" not in calls[0]
    assert calls[0]["track_progress"] is False


def test_import_single_subject_uses_all_episode_pages_and_safe_relations(monkeypatch):
    from jobs.importer import main

    recorded = {}

    class Client:
        def get_subject(self, subject_id):
            if subject_id == 42:
                return {"id": 42, "type": 2, "nsfw": False, "eps": 201, "images": {}}
            if subject_id == 3:
                return {"id": 3, "type": 2, "nsfw": False}
            if subject_id == 4:
                return {"id": 4, "type": 2, "nsfw": True}
            return {"id": subject_id, "type": 2}  # missing nsfw must fail closed

        def get_subject_persons(self, _):
            return []

        def get_all_episodes(self, _):
            return [{"id": 1}, {"id": 201}]

        def get_relations(self, _):
            return [{"id": 3, "type": 2, "nsfw": False}, {"id": 4, "type": 2, "nsfw": False}, {"id": 5, "type": 2, "nsfw": False}]

    class Storage:
        def put_raw_subject(self, *_):
            return None

        def put_cover(self, *_):
            return object()

    class Repository:
        def __init__(self, _):
            pass

        def write_bundle(self, bundle, _):
            recorded["bundle"] = bundle

    monkeypatch.setattr(main, "_get_object_storage", lambda: Storage())
    monkeypatch.setattr(main, "ImportRepository", Repository)
    monkeypatch.setattr(main, "normalize_subject", lambda data, persons: object())

    class Session:
        def rollback(self):
            pass

    assert main.import_single_subject(Client(), Session(), 42, False) == main.OUTCOME_SUCCESS
    assert recorded["bundle"].episodes == ({"id": 1}, {"id": 201})
    assert recorded["bundle"].relations == ({"id": 3, "type": 2, "nsfw": False},)


def test_dry_run_full_does_not_open_database_or_write_records(monkeypatch, caplog):
    from jobs.importer import main

    monkeypatch.setattr(main, "BangumiClient", lambda **_kwargs: CatalogClient([1, 2, 3]))
    monkeypatch.setattr(main, "get_engine", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("dry-run must not open database")))

    with caplog.at_level("INFO"):
        assert main.main(["--mode", "full", "--limit", "2", "--dry-run"]) == 0
    assert "dry-run" in caplog.text
