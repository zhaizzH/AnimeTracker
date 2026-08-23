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
                 "image_storage_status": "MISSING", "eps": 12, "source_fetched_at": None},
                {"id": 2, "bangumi_id": 22, "type": 2, "nsfw": 1, "image": None, "image_source_url": None,
                 "image_storage_status": "MISSING", "eps": 0, "source_fetched_at": "2026-08-23"},
                {"id": 3, "bangumi_id": 33, "type": 2, "nsfw": 0,
                 "image": "http://minio/anime-tracker/covers/33.jpg", "image_source_url": "https://source/33.jpg",
                 "image_storage_status": "STORED", "eps": 2, "source_fetched_at": "2026-08-23"},
            ],
            "episode_count": [{"subject_id": 3, "episode_count": 1}],
            "episode_drift": [{"id": 7, "subject_id": 3, "status": "Air", "airdate": "2999-01-01"}],
            "self_relation": [{"id": 8, "subject_id": 3, "related_subject_id": 3}],
            "tag": [{"id": 9, "subject_id": 3, "name": ""}, {"id": 10, "subject_id": 3, "name": "a" * 65}],
        }

    def execute(self, statement, _params=None):
        sql = str(statement).lower()
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

    def list_objects(self):
        return ["covers/unreferenced.jpg"]

    def fingerprint(self):
        return "minio-fingerprint"


def test_quality_report_contains_every_category_and_fixed_root_fields():
    from importer.quality import build_quality_report

    report = build_quality_report(FakeDatabase(), FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    assert set(report.categories) == EXPECTED
    assert set(report.as_dict()) == {
        "generatedAt", "commit", "dirty", "databaseFingerprint", "minioFingerprint", "counts", "items",
    }
    assert all(item.action for item in report.items)


def test_quality_uses_canonical_object_path_instead_of_image_url():
    from importer.quality import build_quality_report

    report = build_quality_report(FakeDatabase(), FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    missing = [item for item in report.items if item.category == "MISSING_COVER_OBJECT"]
    assert missing[0].target == "covers/33.jpg"
    assert "http://minio" not in missing[0].target


def test_volumes_null_is_not_an_anime_quality_defect():
    from importer.quality import build_quality_report

    report = build_quality_report(FakeDatabase(), FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    assert all("volume" not in item.category.lower() for item in report.items)


def test_quality_report_writer_returns_the_confirmation_digest(tmp_path):
    from importer.quality import build_quality_report, write_quality_report

    report = build_quality_report(FakeDatabase(), FakeMinio(), datetime(2026, 8, 23, tzinfo=timezone.utc))

    digest = write_quality_report(report, tmp_path / "quality.json")

    assert len(digest) == 64
