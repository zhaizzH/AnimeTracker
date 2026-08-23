import pytest
from pydantic import ValidationError

from app.config import Settings


def test_rag_defaults_and_redis_fallback():
    """配置缺失时，RAG 必须安全停用并复用会话 Redis。"""
    s = Settings(_env_file=None, redis_url="redis://session/0")

    assert s.rag_enabled is False
    assert s.rag_embedding_model == "text-embedding-v4"
    assert s.rag_embedding_dim == 1024
    assert s.effective_rag_redis_url == "redis://session/0"
    assert s.minio_raw_bucket == "anime-tracker-private"
    assert s.minio_raw_bucket != s.minio_bucket


def test_rag_redis_url_overrides_session_redis():
    """独立 RAG 索引 Redis 配置必须优先于会话 Redis。"""
    s = Settings(
        _env_file=None,
        redis_url="redis://session/0",
        rag_redis_url="redis://rag/1",
    )

    assert s.effective_rag_redis_url == "redis://rag/1"


def test_rag_embedding_model_rejects_model_switch():
    """RAG 向量维度契约仅允许指定的 Embedding 模型。"""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, rag_embedding_model="text-embedding-v3")


def test_raw_bucket_must_not_match_public_cover_bucket():
    """原始快照不得落入公开封面桶。"""
    with pytest.raises(ValidationError, match="MINIO_RAW_BUCKET"):
        Settings(
            _env_file=None,
            minio_bucket="shared-public-bucket",
            minio_raw_bucket="shared-public-bucket",
        )
