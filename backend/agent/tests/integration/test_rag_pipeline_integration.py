"""真实 RAG 链路只允许显式、隔离的测试资源运行。"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from io import BytesIO

import pytest
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.rag.redis_index import RedisSubjectIndex
from importer.db import get_engine
from importer.normalize import NormalizedSubject
from importer.repository import ImportBundle, ImportRepository
from importer.storage import ObjectStorage
from indexer.main import run_batch
from indexer.repository import IndexJobRepository


pytestmark = pytest.mark.skipif(
    os.getenv("RAG_INTEGRATION_TESTS") != "true",
    reason="set RAG_INTEGRATION_TESTS=true to run isolated RAG pipeline tests",
)


def _required_environment() -> tuple[str, str, str, str]:
    """防止集成环境变量误指向生产 MySQL、MinIO 或 Redis 命名空间。"""
    database = os.getenv("DB_NAME", "")
    cover_bucket = os.getenv("MINIO_BUCKET", "")
    raw_bucket = os.getenv("MINIO_RAW_BUCKET", "")
    key_prefix = os.getenv("RAG_TEST_KEY_PREFIX", "")
    assert database.endswith("_test")
    assert cover_bucket.endswith("-test")
    assert raw_bucket.endswith("-test")
    assert key_prefix.startswith("test:rag:")
    return database, cover_bucket, raw_bucket, key_prefix


class _ImageResponse:
    headers = {"Content-Type": "image/jpeg"}
    raw = BytesIO(b"fixture-cover")

    def raise_for_status(self):
        return None


class _Embedding:
    def embed_documents(self, texts):
        return [[0.0] * 1024 for _ in texts]


def _subject(bangumi_id: int) -> NormalizedSubject:
    return NormalizedSubject(
        bangumi_id=bangumi_id,
        name=f"fixture-{bangumi_id}",
        name_cn=f"测试-{bangumi_id}",
        summary="隔离 RAG 集成测试条目",
        aliases=(), meta_tags=("TV",), free_tags=(), credits=(),
        rating_total=1, rating_counts={}, collection_counts={"collect": 1},
        image_source_url=f"https://fixtures.invalid/{bangumi_id}.jpg",
        source_fetched_at=datetime.now(timezone.utc),
    )
def test_rag_pipeline_writes_three_bundles_then_cleans_all_test_resources():
    """真实隔离链路必须覆盖 MySQL、两个 MinIO 桶和 Redis，清理后都归零。"""
    database, cover_bucket, raw_bucket, key_prefix = _required_environment()
    redis_url = os.getenv("RAG_TEST_REDIS_URL", "")
    assert redis_url
    index_prefix = os.getenv("RAG_TEST_INDEX_PREFIX", "idx:test:rag:")
    assert index_prefix.startswith("idx:test:rag:")
    engine = get_engine(
        os.getenv("DB_HOST", "127.0.0.1"), int(os.getenv("DB_PORT", "3306")),
        os.getenv("DB_USER", "root"), os.getenv("DB_PASSWORD", ""), database,
    )
    client = redis.Redis.from_url(redis_url, decode_responses=False)
    index = RedisSubjectIndex(client, key_prefix=key_prefix, index_prefix=index_prefix)
    storage = ObjectStorage(download=lambda *_args, **_kwargs: _ImageResponse())
    version = "pipeline-test-v1"
    ids = (980001, 980002, 980003)
    id_params = {f"id{position}": value for position, value in enumerate(ids)}
    id_clause = ", ".join(f":id{position}" for position in range(len(ids)))
    index_name = index.ensure_version(version)
    try:
        with Session(engine) as session:
            repository = ImportRepository(session, trusted_tag_min_count=1)
            for bangumi_id in ids:
                storage.put_raw_subject(bangumi_id, {"id": bangumi_id, "type": 2, "nsfw": False})
                cover = storage.put_cover(bangumi_id, f"https://fixtures.invalid/{bangumi_id}.jpg")
                repository.write_bundle(ImportBundle(_subject(bangumi_id), cover), version)
            result = run_batch(
                limit=10,
                index_version=version,
                repository=IndexJobRepository(session),
                embedding_client=_Embedding(),
                redis_index=index,
            )
        assert result.indexed == 3
        assert len(list(client.scan_iter(match=f"{key_prefix}subject:{version}:*"))) == 3
    finally:
        with Session(engine) as session:
            session.execute(text(f"DELETE FROM rag_index_job WHERE subject_id IN (SELECT id FROM subject WHERE bangumi_id IN ({id_clause}))"), id_params)
            for table in ("subject_alias", "subject_meta_tag", "subject_credit", "subject_tag", "subject_relation"):
                session.execute(text(f"DELETE FROM {table} WHERE subject_id IN (SELECT id FROM subject WHERE bangumi_id IN ({id_clause}))"), id_params)
            session.execute(text(f"DELETE FROM subject WHERE bangumi_id IN ({id_clause})"), id_params)
            session.commit()
        for bangumi_id in ids:
            for bucket, object_name in (
                (raw_bucket, f"raw/bangumi/subjects/{bangumi_id}.json.gz"),
                (cover_bucket, f"covers/{bangumi_id}.jpg"),
            ):
                try:
                    storage._minio.remove_object(bucket, object_name)
                except Exception:
                    pass
        try:
            client.execute_command("FT.DROPINDEX", index_name, "DD")
        except Exception:
            pass
        keys = list(client.scan_iter(match=f"{key_prefix}subject:{version}:*"))
        if keys:
            client.delete(*keys)
        with Session(engine) as session:
            assert session.execute(text(f"SELECT COUNT(*) FROM subject WHERE bangumi_id IN ({id_clause})"), id_params).scalar() == 0
            assert session.execute(text("SELECT COUNT(*) FROM rag_index_job WHERE index_version=:version"), {"version": version}).scalar() == 0
        assert list(client.scan_iter(match=f"{key_prefix}subject:{version}:*")) == []
        assert index_name.encode() not in client.execute_command("FT._LIST")
        assert list(storage._minio.list_objects(raw_bucket, prefix="raw/bangumi/subjects/", recursive=True)) == []
        assert list(storage._minio.list_objects(cover_bucket, prefix="covers/", recursive=True)) == []
