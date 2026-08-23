from __future__ import annotations

import gzip
from io import BytesIO
import logging
from datetime import datetime, timezone
from unittest.mock import ANY, Mock

from importer import main
from importer.storage import CoverResult, ObjectStorage, ObjectStorageError


class FakeMinio:
    def __init__(self):
        self.calls: list[str] = []
        self.last_bucket: str | None = None
        self.object_name: str | None = None
        self.bytes = b""
        self.stat_error: Exception | None = None

    def bucket_exists(self, bucket: str) -> bool:
        self.calls.append("bucket_exists")
        return True

    def put_object(self, bucket: str, object_name: str, data, length: int, **kwargs) -> None:
        self.calls.append("put_object")
        self.last_bucket = bucket
        self.object_name = object_name
        self.bytes = data.read()

    def stat_object(self, bucket: str, object_name: str) -> None:
        self.calls.append("stat_object")
        if self.stat_error:
            raise self.stat_error


def fake_download(url: str, **kwargs):
    response = type("Response", (), {})()
    response.headers = {"Content-Type": "image/jpeg"}
    response.raw = BytesIO(b"cover")
    response.raise_for_status = lambda: None
    return response


def storage(fake_minio: FakeMinio) -> ObjectStorage:
    return ObjectStorage(
        minio_client=fake_minio,
        download=fake_download,
        environment={
            "MINIO_ENDPOINT": "minio.example.test",
            "MINIO_BUCKET": "anime-tracker",
            "MINIO_RAW_BUCKET": "anime-tracker-private",
        },
        sleep=lambda _: None,
    )


def test_cover_falls_back_when_stat_fails():
    fake_minio = FakeMinio()
    fake_minio.stat_error = RuntimeError("missing")

    result = storage(fake_minio).put_cover(42, "https://img/42.jpg")

    assert result.display_url == "https://img/42.jpg"
    assert result.source_url == "https://img/42.jpg"
    assert result.object_name is None
    assert result.status == "SOURCE_FALLBACK"
    assert fake_minio.calls == ["bucket_exists", "put_object", "stat_object"] * 3


def test_raw_snapshot_is_private_gzip_json():
    fake_minio = FakeMinio()

    name = storage(fake_minio).put_raw_subject(42, {"name": "A", "id": 42})

    assert name == "raw/bangumi/subjects/42.json.gz"
    assert fake_minio.last_bucket == "anime-tracker-private"
    assert fake_minio.object_name == name
    assert gzip.decompress(fake_minio.bytes).decode("utf-8") == '{"id":42,"name":"A"}'


def test_cover_returns_public_url_only_after_put_then_stat():
    fake_minio = FakeMinio()

    result = storage(fake_minio).put_cover(42, "https://img/42.jpg")

    assert result.display_url == "http://minio.example.test/anime-tracker/covers/42.jpg"
    assert result.source_url == "https://img/42.jpg"
    assert result.object_name == "covers/42.jpg"
    assert result.status == "STORED"
    assert fake_minio.calls == ["bucket_exists", "put_object", "stat_object"]


def test_empty_cover_is_marked_missing_without_storage_call():
    fake_minio = FakeMinio()

    result = storage(fake_minio).put_cover(42, "")

    assert result.display_url == ""
    assert result.object_name is None
    assert result.status == "MISSING"
    assert fake_minio.calls == []


def test_storage_error_log_does_not_include_exception_body(caplog):
    fake_minio = FakeMinio()
    fake_minio.stat_error = RuntimeError("secret-key=response-body")

    with caplog.at_level(logging.WARNING):
        storage(fake_minio).put_cover(42, "https://img/42.jpg")

    assert "subject_id=42" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert "secret-key" not in caplog.text
    assert "response-body" not in caplog.text


def test_raw_storage_error_log_does_not_include_exception_body(caplog):
    fake_minio = FakeMinio()
    fake_minio.put_object = Mock(side_effect=RuntimeError("secret-key=response-body"))

    with caplog.at_level(logging.WARNING):
        try:
            storage(fake_minio).put_raw_subject(42, {"id": 42})
        except ObjectStorageError:
            pass
        else:
            raise AssertionError("raw storage failure must be raised")

    assert "subject_id=42" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert "secret-key" not in caplog.text
    assert "response-body" not in caplog.text


def test_repository_receives_cover_result_without_mutating_raw_bangumi_image(monkeypatch):
    raw = {"id": 42, "images": {"large": "https://img/42.jpg"}}
    cover = CoverResult(
        display_url="http://minio/anime-tracker/covers/42.jpg",
        source_url="https://img/42.jpg",
        object_name="covers/42.jpg",
        status="STORED",
        checked_at=datetime.now(timezone.utc),
    )
    repository = Mock(return_value=7)
    monkeypatch.setattr(main, "upsert_subject", repository)

    main._write_related(Mock(), {"data": raw, "cover": cover, "episodes": []})

    repository.assert_called_once_with(ANY, raw, cover)
    assert raw["images"]["large"] == "https://img/42.jpg"
