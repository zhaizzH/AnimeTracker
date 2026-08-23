from __future__ import annotations

from array import array
from dataclasses import dataclass
import math
from typing import Any, Sequence

from redis.exceptions import ResponseError

from app.rag.schemas import SubjectProfile


VECTOR_DIMENSIONS = 1024


@dataclass(frozen=True)
class SubjectIndexDocument:
    """写入版本化 RediSearch HASH 的条目资料。"""

    subject_id: int
    index_version: str
    profile: SubjectProfile
    vector: Sequence[float]
    title: str
    aliases: Sequence[str] = ()
    summary: str = ""
    meta_tags: Sequence[str] = ()
    trusted_tags: Sequence[str] = ()
    credits: Sequence[str] = ()
    year: int | None = None
    quarter: int | None = None
    score: float | None = None
    rating_total: int | None = None
    collection_total: int | None = None
    air_status: str = ""
    type: str = ""
    nsfw: bool = False


def vector_bytes(values: Sequence[float]) -> bytes:
    """编码并验证固定维度的 Float32 向量。"""
    if len(values) != VECTOR_DIMENSIONS:
        raise ValueError("embedding 必须是 1024 个有限浮点数")
    try:
        normalized = [float(value) for value in values]
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError("embedding 必须是 1024 个有限浮点数") from exc
    if not all(math.isfinite(value) for value in normalized):
        raise ValueError("embedding 必须是 1024 个有限浮点数")
    try:
        return array("f", normalized).tobytes()
    except OverflowError as exc:
        raise ValueError("embedding 必须是 1024 个有限浮点数") from exc


class RedisSubjectIndex:
    """RediSearch 的版本化条目索引；调用方负责索引重建门禁。"""

    def __init__(self, redis: Any, key_prefix: str = "rag:", index_prefix: str = "idx:rag:"):
        self._redis = redis
        self._key_prefix = key_prefix
        self._index_prefix = index_prefix

    @property
    def active_alias(self) -> str:
        return f"{self._index_prefix}subject:active"

    def index_name(self, index_version: str) -> str:
        return f"{self._index_prefix}subject:{self._validate_version(index_version)}"

    def document_key(self, index_version: str, subject_id: int) -> str:
        return f"{self._key_prefix}subject:{self._validate_version(index_version)}:{subject_id}"

    def ensure_version(self, index_version: str) -> str:
        """创建索引版本；已存在的索引可安全复用。"""
        version = self._validate_version(index_version)
        name = self.index_name(version)
        prefix = f"{self._key_prefix}subject:{version}:"
        try:
            self._redis.execute_command(
                "FT.CREATE",
                name,
                "ON",
                "HASH",
                "PREFIX",
                "1",
                prefix,
                "SCHEMA",
                "title",
                "TEXT",
                "aliases",
                "TEXT",
                "summary",
                "TEXT",
                "meta_tags",
                "TEXT",
                "trusted_tags",
                "TEXT",
                "credits",
                "TEXT",
                "profile",
                "TEXT",
                "year",
                "NUMERIC",
                "quarter",
                "NUMERIC",
                "score",
                "NUMERIC",
                "rating_total",
                "NUMERIC",
                "collection_total",
                "NUMERIC",
                "air_status",
                "TAG",
                "type",
                "TAG",
                "nsfw",
                "TAG",
                "vector",
                "VECTOR",
                "FLAT",
                "6",
                "TYPE",
                "FLOAT32",
                "DIM",
                str(VECTOR_DIMENSIONS),
                "DISTANCE_METRIC",
                "COSINE",
            )
        except ResponseError as exc:
            if "exists" not in str(exc).lower():
                raise
        return name

    def write(self, document: SubjectIndexDocument) -> None:
        """写入指定版本的 HASH 文档，向量必须先通过 Float32 验证。"""
        mapping: dict[str, Any] = {
            "title": document.title,
            "aliases": self._join(document.aliases),
            "summary": document.summary,
            "meta_tags": self._join(document.meta_tags),
            "trusted_tags": self._join(document.trusted_tags),
            "credits": self._join(document.credits),
            "profile": document.profile.text,
            "content_hash": document.profile.content_hash,
            "schema_version": document.profile.schema_version,
            "air_status": document.air_status,
            "type": document.type,
            "nsfw": "1" if document.nsfw else "0",
            "vector": vector_bytes(document.vector),
        }
        for field in ("year", "quarter", "score", "rating_total", "collection_total"):
            value = getattr(document, field)
            if value is not None:
                mapping[field] = value
        self._redis.hset(self.document_key(document.index_version, document.subject_id), mapping=mapping)

    def activate(self, index_version: str) -> None:
        """原子切换检索别名；绝不删除旧索引、文档或会话键。"""
        self._redis.execute_command("FT.ALIASUPDATE", self.active_alias, self.index_name(index_version))

    def search(self, query: str, vector: Sequence[float], *, limit: int = 10) -> Any:
        """在当前别名上运行全文/过滤条件与 KNN 联合查询。"""
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        expression = query.strip() or "*"
        knn_query = f"{expression}=>[KNN {limit} @vector $vector AS vector_score]"
        return self._redis.execute_command(
            "FT.SEARCH",
            self.active_alias,
            knn_query,
            "PARAMS",
            "2",
            "vector",
            vector_bytes(vector),
            "SORTBY",
            "vector_score",
            "ASC",
            "LIMIT",
            "0",
            str(limit),
            "DIALECT",
            "2",
        )

    @staticmethod
    def _join(values: Sequence[str]) -> str:
        return " ".join(str(value) for value in values)

    @staticmethod
    def _validate_version(index_version: str) -> str:
        if not index_version or ":" in index_version:
            raise ValueError("index_version 不能为空且不能包含冒号")
        return index_version
