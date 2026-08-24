from __future__ import annotations

from datetime import datetime, timezone


EXPECTED = {
    "NON_ANIME",
    "NSFW",
    "SOURCE_MISSING",
    "SELF_RELATION",
    "MISSING_COVER_OBJECT",
    "UNREFERENCED_OBJECT",
    "NO_EPISODES",
    "EPISODE_SHORTAGE",
    "EPISODE_STATUS_DRIFT",
    "BLANK_TAG",
    "NOISY_TAG",
}


class Result:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def scalar(self):
        return self._rows[0][0] if self._rows else 0


class FakeDatabase:
    def __init__(self):
        self.rows = {
            "subject": [
                {"id": 1, "bangumi_id": 11, "type": 1, "nsfw": 0, "image": None, "image_source_url": None,
                 "image_storage_status": "MISSING", "eps": 12, "source_fetched_at": None, "import_status": 1},
                {"id": 2, "bangumi_id": 22, "type": 2, "nsfw": 1, "image": None, "image_source_url": None,
                 "image_storage_status": "MISSING", "eps": 0, "source_fetched_at": "2026-08-23", "import_status": 1},
                {"id": 3, "bangumi_id": 33, "type": 2, "nsfw": 0,
                 "image": "http://minio/anime-tracker/covers/33.jpg", "image_source_url": "https://source/33.jpg",
                 "image_storage_status": "STORED", "eps": 2, "source_fetched_at": "2026-08-23", "import_status": 1},
            ],
            "episode_count": [{"subject_id": 3, "episode_count": 1}],
            "episode_drift": [{"id": 7, "subject_id": 3, "status": "Air", "airdate": "2999-01-01"}],
            "self_relation": [{"id": 8, "subject_id": 3, "related_subject_id": 3}],
            "tag": [{"id": 9, "subject_id": 3, "name": ""}, {"id": 10, "subject_id": 3, "name": "a" * 65}],
        }
        self.index_jobs = [{"subject_id": 3, "content_hash": "expected-hash"}]

    def execute(self, statement, _params=None):
        sql = str(statement).lower()
        if "from rag_index_job" in sql:
            return Result(self.index_jobs)
        if "database_fingerprint" in sql:
            return Result([("db-fingerprint",)])
        if "from subject_relation" in sql:
            return Result(self.rows["self_relation"])
        if "from episode" in sql and "status" in sql:
            return Result(self.rows["episode_drift"])
        if "from episode" in sql:
            return Result(self.rows["episode_count"])
        if "from subject_tag" in sql:
            return Result(self.rows["tag"])
        if "from subject" in sql:
            return Result(self.rows["subject"])
        raise AssertionError(sql)


class FakeMinio:
    bucket_name = "anime-tracker"
    endpoint = "minio"

    def list_objects(self):
        return ["covers/unreferenced.jpg"]

    def fingerprint(self):
        return "minio-fingerprint"


class FakeIndex:
    def __init__(self, hashes):
        self.hashes = hashes

    def content_hashes(self, _version):
        return dict(self.hashes)


def test_quality_report_contains_every_category_and_fixed_root_fields():
    from jobs.importer.quality import build_quality_report

    report = build_quality_report(FakeDatabase(), FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    assert set(report.categories) == EXPECTED
    assert set(report.as_dict()) == {
        "generatedAt", "commit", "dirty", "databaseFingerprint", "minioFingerprint", "counts", "items",
    }
    assert all(item.action for item in report.items)


def test_quality_uses_canonical_object_path_instead_of_image_url():
    from jobs.importer.quality import build_quality_report

    report = build_quality_report(FakeDatabase(), FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    missing = [item for item in report.items if item.category == "MISSING_COVER_OBJECT"]
    assert missing[0].target == "covers/33.jpg"
    assert "http://minio" not in missing[0].target


def test_quality_report_with_index_version_emits_gate_coverage_and_hash_samples():
    from jobs.importer.quality import build_quality_report

    report = build_quality_report(
        FakeDatabase(),
        FakeMinio(),
        datetime(2026, 8, 23, tzinfo=timezone.utc),
        index_version="v1",
        embedding_contract={"provider": "dashscope", "model": "text-embedding-v4", "dimensions": 1024, "profileVersion": "subject-profile-v1"},
        redis_index=FakeIndex({3: "expected-hash"}),
    )
    payload = report.as_dict()
    assert 0 <= payload["coverage"] <= 1
    assert payload["contentHashSamples"]
    assert all(sample["expected"] and sample["observed"] for sample in payload["contentHashSamples"])


def test_quality_coverage_uses_all_qualified_subjects_and_compares_independent_redis_hashes():
    from jobs.importer.quality import build_quality_report

    db = FakeDatabase()
    db.index_jobs = []
    missing = build_quality_report(
        db, FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc),
        index_version="v1", redis_index=FakeIndex({3: "observed-hash"}),
    ).as_dict()
    assert missing["coverage"] == 0
    assert missing["contentHashSamples"][0]["expected"] == ""
    assert missing["contentHashSamples"][0]["observed"] == "observed-hash"

    db.index_jobs = [{"subject_id": 3, "content_hash": "expected-hash"}]
    changed = build_quality_report(
        db, FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc),
        index_version="v1", redis_index=FakeIndex({3: "changed-hash"}),
    ).as_dict()
    assert changed["coverage"] == 1
    assert changed["contentHashSamples"][0]["expected"] != changed["contentHashSamples"][0]["observed"]

    absent = build_quality_report(
        db, FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc),
        index_version="v1", redis_index=FakeIndex({}),
    ).as_dict()
    assert absent["coverage"] == 0
    assert absent["contentHashSamples"][0]["observed"] == ""


def test_volumes_null_is_not_an_anime_quality_defect():
    from jobs.importer.quality import build_quality_report

    report = build_quality_report(FakeDatabase(), FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    assert all("volume" not in item.category.lower() for item in report.items)


def test_past_na_episode_is_reported_as_status_drift():
    from jobs.importer.quality import build_quality_report

    db = FakeDatabase()
    db.rows["episode_drift"] = [{"id": 7, "subject_id": 3, "status": "NA", "airdate": "2026-08-22"}]

    report = build_quality_report(db, FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    drift = [item for item in report.items if item.category == "EPISODE_STATUS_DRIFT"]
    assert drift[0].details["expectedStatus"] == "Air"


def test_external_cover_url_is_not_treated_as_a_minio_object_reference():
    from jobs.importer.quality import canonical_cover_object_path

    assert canonical_cover_object_path("https://source.example/covers/33.jpg", FakeMinio()) is None


def test_database_fingerprint_covers_every_cleanup_target_table():
    from jobs.importer.quality import database_fingerprint

    class Database:
        def __init__(self):
            self.query = ""

        def execute(self, statement):
            self.query = str(statement).lower()
            return type("Result", (), {"scalar": lambda _: "fingerprint"})()

    db = Database()

    assert database_fingerprint(db) == "fingerprint"
    assert all(table in db.query for table in ("subject", "subject_relation", "subject_tag", "episode"))
    assert "sum(id)" in db.query
    assert "image_source_url" in db.query
    assert "eps" in db.query


def test_quality_report_writer_returns_the_confirmation_digest(tmp_path):
    from jobs.importer.quality import build_quality_report, write_quality_report

    report = build_quality_report(FakeDatabase(), FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    digest = write_quality_report(report, tmp_path / "quality.json")

    assert len(digest) == 64
