from __future__ import annotations

from array import array
from dataclasses import dataclass
import json
import math
from typing import Any, Mapping, Sequence

from app.entities.enums import EntityKind
from app.rag.schemas import RetrievalQuery, SubjectProfile


VECTOR_DIMENSIONS = 1024


def vector_bytes(values: Sequence[float]) -> bytes:
    """Encode and validate a fixed-dimension little-endian Float32 vector."""
    if len(values) != VECTOR_DIMENSIONS:
        raise ValueError("embedding 必须是 1024 个有限浮点数")
    try:
        normalized = [float(value) for value in values]
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError("embedding 必须是 1024 个有限浮点数") from exc
    if not all(math.isfinite(value) for value in normalized):
        raise ValueError("embedding 必须是 1024 个有限浮点数")
    encoded = array("f", normalized)
    if not all(math.isfinite(value) for value in encoded):
        raise ValueError("embedding 必须是 1024 个有限浮点数")
    return encoded.tobytes()


@dataclass(frozen=True)
class SubjectIndexDocument:
    """A versioned public Subject document written to a Redis Vector Set."""

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
    type: int = 2
    nsfw: bool = False
    source_active: bool = True


class LexicalSearchUnavailable(RuntimeError):
    """The lexical half is owned by Business/MySQL, not Redis."""


class RedisSubjectIndex:
    """Redis 8 Vector Set adapter for versioned Subject embeddings.

    Lexical retrieval is deliberately not implemented here. Callers must
    inject a Business lexical adapter so MySQL release and Vector Set version
    can be checked together.
    """

    def __init__(self, redis: Any, key_prefix: str = "rag:vectors:", index_prefix: str = "idx:rag:", active_alias: str | None = None):
        self._redis = redis
        self._key_prefix = key_prefix
        self._index_prefix = index_prefix
        # Compatibility property only. Publication is controlled by MySQL.
        self._active_alias = active_alias or "search_index_release"

    @property
    def active_alias(self) -> str:
        return self._active_alias

    def index_name(self, index_version: str) -> str:
        return self.vector_key(index_version)

    def vector_key(self, index_version: str) -> str:
        return f"{self._key_prefix}SUBJECT:{self._validate_version(index_version)}"

    def document_key(self, index_version: str, subject_id: int) -> str:
        self._validate_subject_id(subject_id)
        return f"{self.vector_key(index_version)}:{subject_id}"

    def ensure_version(self, index_version: str) -> str:
        self._validate_version(index_version)
        for command in ("VADD", "VSIM", "VREM"):
            try:
                info = self._redis.execute_command("COMMAND", "INFO", command)
            except Exception as exc:
                raise RuntimeError(f"无法探测 Redis Vector Set {command}") from exc
            if not _command_info_present(info):
                raise RuntimeError(f"Redis 未启用 Vector Set {command}；RAG 索引保持关闭")
        return self.vector_key(index_version)

    def write(self, document: SubjectIndexDocument) -> None:
        if document.type != 2 or document.nsfw:
            raise ValueError("RAG 索引仅接收 type=2 且非 NSFW 的动画条目")
        self._redis.execute_command(
            "VADD", self.vector_key(document.index_version), "FP32", vector_bytes(document.vector),
            f"SUBJECT:{self._validate_subject_id(document.subject_id)}", "Q8", "SETATTR", self._attributes(document),
        )

    def content_hashes(self, index_version: str) -> dict[int, str]:
        """Read a bounded sample via Vector Set attributes for quality gates."""
        try:
            members = self._redis.execute_command("VRANGE", self.vector_key(index_version), "-", "+", 100)
        except Exception as exc:
            raise RuntimeError("Redis 不支持 Vector Set 抽样读取") from exc
        result: dict[int, str] = {}
        if not isinstance(members, (list, tuple)):
            return result
        for member in members:
            try:
                member = member.decode() if isinstance(member, bytes) else str(member)
                subject_id = int(member.rsplit(":", 1)[1])
                raw_attrs = self._redis.execute_command("VGETATTR", self.vector_key(index_version), member)
                attrs_text = raw_attrs.decode() if isinstance(raw_attrs, bytes) else str(raw_attrs)
                content_hash = json.loads(attrs_text).get("content_hash")
            except (AttributeError, IndexError, TypeError, ValueError, KeyError, json.JSONDecodeError):
                continue
            if isinstance(content_hash, str):
                result[subject_id] = content_hash
        return result

    def activate(self, index_version: str) -> None:
        raise RuntimeError("发布指针由 MySQL search_index_release 管理；不允许更新 Redis alias")

    def lexical_search(self, _query: str, limit: int = 50) -> Any:
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        raise LexicalSearchUnavailable("MySQL FULLTEXT lexical API 尚未注入")

    def semantic_search(self, _query: str, _vector: Sequence[float], limit: int = 50) -> Any:
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        raise RuntimeError("Vector Set 查询需要 RetrievalQuery；请调用 semantic_search_query")

    def semantic_search_query(self, query: RetrievalQuery, vector: Sequence[float], limit: int = 50) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        index_version = getattr(query, "index_version", None)
        if not index_version:
            raise RuntimeError("查询缺少 indexVersion；拒绝跨版本 Vector Set 查询")
        args: list[Any] = [
            "VSIM", self.vector_key(index_version), "FP32", vector_bytes(vector),
            "WITHSCORES", "WITHATTRIBS", "COUNT", limit,
        ]
        filter_expression = _vector_filter(query)
        if filter_expression:
            args.extend(("FILTER", filter_expression))
        raw = self._redis.execute_command(*args)
        return _parse_vsim_rows(raw)

    def semantic_search_for_version(
        self, index_version: str, query: RetrievalQuery, vector: Sequence[float], *, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Run VSIM only against the release returned by Business lexical search."""
        version = self._validate_version(index_version)
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        args: list[Any] = [
            "VSIM", self.vector_key(version), "FP32", vector_bytes(vector),
            "WITHSCORES", "WITHATTRIBS", "COUNT", limit,
        ]
        filter_expression = _vector_filter(query)
        if filter_expression:
            args.extend(("FILTER", filter_expression))
        raw = self._redis.execute_command(*args)
        return _parse_vsim_rows(raw)

    def search(self, query: str, vector: Sequence[float], *, limit: int = 10) -> Any:
        return self.semantic_search(query, vector, limit=limit)

    @staticmethod
    def _validate_version(index_version: str) -> str:
        if not isinstance(index_version, str) or not index_version or ":" in index_version or any(char.isspace() for char in index_version):
            raise ValueError("index_version 不能为空、不能包含冒号或空白")
        return index_version

    @staticmethod
    def _validate_subject_id(subject_id: int) -> int:
        if isinstance(subject_id, bool) or int(subject_id) < 1:
            raise ValueError("subject_id 必须是正整数")
        return int(subject_id)

    @staticmethod
    def _attributes(document: SubjectIndexDocument) -> str:
        payload: dict[str, Any] = {
            "entity_kind": EntityKind.SUBJECT.value,
            "entity_id": document.subject_id,
            "subject_id": document.subject_id,
            "name": document.title[:128],
            "aliases": [str(value)[:128] for value in document.aliases if str(value)],
            "content_hash": document.profile.content_hash,
            "schema_version": document.profile.schema_version,
            "source_active": bool(document.source_active),
            "type": document.type,
            "nsfw": document.nsfw,
        }
        for field in ("year", "quarter", "score", "rating_total", "collection_total", "air_status"):
            value = getattr(document, field)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _vector_filter(query: RetrievalQuery) -> str:
    """Build only literals from typed query; never accept user expressions."""
    parts = ['.entity_kind == "SUBJECT"', ".source_active == true", ".type == 2", ".nsfw == false"]
    if query.year_from is not None:
        parts.append(f".year >= {int(query.year_from)}")
    if query.year_to is not None:
        parts.append(f".year <= {int(query.year_to)}")
    if query.quarter:
        parts.append(f".quarter == {int({'spring': 1, 'summer': 2, 'autumn': 3, 'winter': 4}[query.quarter])}")
    if query.score_min is not None:
        parts.append(f".score >= {float(query.score_min):.8g}")
    if query.rating_total_min is not None:
        parts.append(f".rating_total >= {int(query.rating_total_min)}")
    if query.air_status:
        parts.append(f'.air_status == "{query.air_status}"')
    for subject_id in query.exclude_subject_ids:
        parts.append(f".subject_id != {int(subject_id)}")
    return " && ".join(parts)


def _parse_vsim_rows(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, Mapping):
        rows: list[dict[str, Any]] = []
        for member, value in raw.items():
            try:
                member_text = member.decode() if isinstance(member, bytes) else str(member)
                score, attrs_value = (value[0], value[1]) if isinstance(value, (list, tuple)) else (value, None)
                score_value = float(score.decode() if isinstance(score, bytes) else score)
                attrs_text = attrs_value.decode() if isinstance(attrs_value, bytes) else attrs_value
                attrs = json.loads(attrs_text) if attrs_text else {}
                kind, raw_id = member_text.rsplit(":", 1)
                subject_id = int(raw_id)
            except (AttributeError, IndexError, TypeError, ValueError, KeyError, json.JSONDecodeError):
                continue
            if kind != EntityKind.SUBJECT.value or not isinstance(attrs, Mapping):
                continue
            row = dict(attrs)
            row.update({"subject_id": subject_id, "id": subject_id, "score": score_value})
            rows.append(row)
        return rows
    if not isinstance(raw, (list, tuple)):
        return []
    rows: list[dict[str, Any]] = []
    for offset in range(0, len(raw) - 2, 3):
        try:
            member = raw[offset].decode() if isinstance(raw[offset], bytes) else str(raw[offset])
            score = float(raw[offset + 1].decode() if isinstance(raw[offset + 1], bytes) else raw[offset + 1])
            attrs_text = raw[offset + 2].decode() if isinstance(raw[offset + 2], bytes) else raw[offset + 2]
            attrs = json.loads(attrs_text) if attrs_text else {}
            kind, raw_id = member.rsplit(":", 1)
            subject_id = int(raw_id)
        except (AttributeError, IndexError, TypeError, ValueError, KeyError, json.JSONDecodeError):
            continue
        if kind != EntityKind.SUBJECT.value or not isinstance(attrs, Mapping):
            continue
        row = dict(attrs)
        row.update({"subject_id": subject_id, "id": subject_id, "score": score})
        rows.append(row)
    return rows


def _command_info_present(info: Any) -> bool:
    """Redis returns ``[None]`` for an unknown COMMAND INFO entry."""
    if not info:
        return False
    return not isinstance(info, (list, tuple)) or any(item is not None for item in info)
