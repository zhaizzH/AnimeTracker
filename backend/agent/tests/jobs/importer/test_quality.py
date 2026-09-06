from datetime import datetime, timezone

import pytest

from jobs.importer.quality import build_quality_report


class _Result:
    def __init__(self, rows=None, scalar_value=None):
        self._rows = rows or []
        self._scalar_value = scalar_value

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def scalar(self):
        return self._scalar_value


class _Db:
    def execute(self, statement, _params=None):
        sql = str(statement)
        if sql.startswith("SELECT SHA2"):
            return _Result(scalar_value="database-fingerprint")
        if sql.startswith("SELECT id, bangumi_id"):
            return _Result([
                {"id": 1, "type": 2, "nsfw": 0, "image": None, "image_source_url": None,
                 "image_storage_status": None, "eps": None, "source_fetched_at": None, "import_status": 1},
                {"id": 2, "type": 2, "nsfw": 0, "image": None, "image_source_url": None,
                 "image_storage_status": None, "eps": None, "source_fetched_at": None, "import_status": 1},
            ])
        if "SELECT subject_id, COUNT(*) AS episode_count" in sql:
            return _Result([])
        if "FROM subject_relation WHERE" in sql or "FROM episode WHERE airdate" in sql or "FROM subject_tag" in sql:
            return _Result([])
        if "FROM rag_index_job" in sql:
            return _Result([
                {"subject_id": 1, "content_hash": "hash-1"},
                {"subject_id": 2, "content_hash": "hash-2"},
            ])
        raise AssertionError(f"unexpected SQL: {sql}")


class _Minio:
    def list_objects(self):
        return []


class _SampleOnlyIndex:
    def content_hashes(self, _index_version):
        # Simulate Redis VRANGE's bounded sample: one of two vectors is enough
        # for hash evidence, but must not define catalog coverage.
        return {1: "hash-1"}

    def cardinality(self, _index_version):
        return 2


class _NoCardinalityIndex:
    def content_hashes(self, _index_version):
        return {1: "hash-1"}


def _build(redis_index):
    return build_quality_report(
        _Db(),
        _Minio(),
        datetime(2026, 9, 6, tzinfo=timezone.utc),
        index_version="v1",
        redis_index=redis_index,
    )


def test_quality_coverage_uses_vector_cardinality_not_bounded_hash_sample():
    report = _build(_SampleOnlyIndex())

    assert report.coverage == pytest.approx(1.0)
    assert report.catalog_count == 2
    assert report.vector_cardinality == 2
    assert report.content_hash_samples == (
        {"subjectId": 1, "expected": "hash-1", "observed": "hash-1"},
    )
    assert report.as_dict()["coverageCatalogCount"] == 2
    assert report.as_dict()["vectorCardinality"] == 2


def test_quality_fails_closed_when_vector_cardinality_is_unavailable():
    with pytest.raises(RuntimeError, match="cardinality"):
        _build(_NoCardinalityIndex())
