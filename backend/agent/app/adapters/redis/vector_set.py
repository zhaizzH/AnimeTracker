"""Redis 8 Vector Set primitives used by the RAG index.

The adapter intentionally contains no RediSearch commands.  A vector set is
versioned by key and its members carry only public, non-private metadata.  The
MySQL ``search_index_release`` remains the publication pointer; this module
never creates an alias or decides which version is active.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Sequence

from redis.exceptions import ResponseError

from app.adapters.redis.subject_index import VECTOR_DIMENSIONS, vector_bytes
from app.entities.enums import EntityKind


VECTOR_SET_PREFIX = "rag:vectors:"
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_MAX_MEMBER_LENGTH = 128


class VectorSetUnavailable(RuntimeError):
    """Raised when the connected Redis does not expose Vector Set commands."""


def validate_version(index_version: str) -> str:
    if not isinstance(index_version, str) or not _VERSION_PATTERN.fullmatch(index_version):
        raise ValueError("index_version 不能为空，且只能包含字母、数字、点、下划线或短横线")
    return index_version


def vector_set_key(entity_kind: EntityKind | str, index_version: str, *, prefix: str = VECTOR_SET_PREFIX) -> str:
    version = validate_version(index_version)
    kind = entity_kind.value if isinstance(entity_kind, EntityKind) else str(entity_kind).upper()
    if kind not in {item.value for item in EntityKind}:
        raise ValueError("entity_kind 不受支持")
    if not prefix or any(char.isspace() for char in prefix):
        raise ValueError("vector set prefix 不能为空且不能包含空白")
    return f"{prefix}{kind}:{version}"


def vector_member(entity_kind: EntityKind | str, entity_id: int) -> str:
    kind = entity_kind.value if isinstance(entity_kind, EntityKind) else str(entity_kind).upper()
    if kind not in {item.value for item in EntityKind} or isinstance(entity_id, bool) or int(entity_id) < 1:
        raise ValueError("entity member 无效")
    return f"{kind}:{int(entity_id)}"


def _decode(value: Any) -> Any:
    return value.decode("utf-8") if isinstance(value, bytes) else value


def parse_vsim_response(raw: Any) -> list[dict[str, Any]]:
    """Normalize RESP2 ``VSIM ... WITHSCORES WITHATTRIBS`` rows.

    Each result consists of ``member, score, json_attributes``.  Malformed
    rows are ignored; an invalid Redis response never becomes a candidate.
    """

    if isinstance(raw, Mapping):
        # redis-py RESP3 can return {member: (score, attrs)}.
        rows: list[dict[str, Any]] = []
        for member, value in raw.items():
            if isinstance(value, (list, tuple)) and value:
                score, attrs = value[0], value[1] if len(value) > 1 else None
            else:
                score, attrs = value, None
            rows.append(_result_row(member, score, attrs))
        return [row for row in rows if row]
    if not isinstance(raw, (list, tuple)):
        return []
    rows = []
    for offset in range(0, len(raw) - 2, 3):
        row = _result_row(raw[offset], raw[offset + 1], raw[offset + 2])
        if row:
            rows.append(row)
    return rows


def _result_row(member: Any, score: Any, attrs: Any) -> dict[str, Any]:
    member_text = str(_decode(member) or "")
    if not member_text or not isinstance(score, (int, float, str, bytes)):
        return {}
    try:
        similarity = float(_decode(score))
    except (TypeError, ValueError):
        return {}
    if not 0.0 <= similarity <= 1.0:
        return {}
    payload: dict[str, Any] = {"member": member_text, "score": similarity}
    decoded_attrs = _decode(attrs)
    if decoded_attrs:
        try:
            parsed = json.loads(decoded_attrs) if isinstance(decoded_attrs, str) else decoded_attrs
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        if not isinstance(parsed, Mapping):
            return {}
        payload.update(parsed)
    try:
        kind, raw_id = member_text.rsplit(":", 1)
        payload.setdefault("entity_kind", kind)
        payload.setdefault("entity_id", int(raw_id))
    except (ValueError, TypeError):
        return {}
    return payload


class RedisVectorSet:
    """Low-level versioned Vector Set writer/query adapter."""

    def __init__(self, redis_client: Any, *, prefix: str = VECTOR_SET_PREFIX, quantization: str = "Q8") -> None:
        self._redis = redis_client
        self._prefix = prefix
        self._quantization = quantization.upper()
        if self._quantization not in {"Q8", "NOQUANT", "BIN"}:
            raise ValueError("quantization 必须是 Q8、NOQUANT 或 BIN")

    def key(self, entity_kind: EntityKind | str, index_version: str) -> str:
        return vector_set_key(entity_kind, index_version, prefix=self._prefix)

    def ensure_version(self, index_version: str) -> None:
        """Validate the server capability without creating a fake empty index."""
        validate_version(index_version)
        for command in ("VADD", "VSIM", "VREM"):
            try:
                info = self._redis.execute_command("COMMAND", "INFO", command)
            except Exception as exc:
                raise VectorSetUnavailable(f"无法探测 Redis Vector Set {command}") from exc
            if not _command_info_present(info):
                raise VectorSetUnavailable(f"Redis 未启用 Vector Set {command}；需要 Redis 8+")

    def add(
        self,
        entity_kind: EntityKind | str,
        entity_id: int,
        index_version: str,
        vector: Sequence[float],
        *,
        attributes: Mapping[str, Any] | None = None,
    ) -> bool:
        key = self.key(entity_kind, index_version)
        member = vector_member(entity_kind, entity_id)
        encoded = vector_bytes(vector)
        args: list[Any] = ["VADD", key, "FP32", encoded, member]
        args.append(self._quantization)
        if attributes:
            args.extend(("SETATTR", json.dumps(dict(attributes), ensure_ascii=False, separators=(",", ":"))))
        try:
            result = self._redis.execute_command(*args)
        except ResponseError as exc:
            if "unknown command" in str(exc).lower() or "wrong number" in str(exc).lower():
                raise VectorSetUnavailable("Redis Vector Set VADD 不可用") from exc
            raise
        return bool(result)

    def remove(self, entity_kind: EntityKind | str, entity_id: int, index_version: str) -> bool:
        try:
            return bool(self._redis.execute_command("VREM", self.key(entity_kind, index_version), vector_member(entity_kind, entity_id)))
        except ResponseError as exc:
            if "unknown command" in str(exc).lower():
                raise VectorSetUnavailable("Redis Vector Set VREM 不可用") from exc
            raise

    def search(
        self,
        entity_kind: EntityKind | str,
        index_version: str,
        vector: Sequence[float],
        *,
        count: int = 50,
        filter_expression: str | None = None,
        ef: int | None = None,
    ) -> list[dict[str, Any]]:
        if count < 1:
            raise ValueError("count 必须大于 0")
        args: list[Any] = ["VSIM", self.key(entity_kind, index_version), "FP32", vector_bytes(vector), "WITHSCORES", "WITHATTRIBS", "COUNT", count]
        if ef is not None:
            if ef < 1:
                raise ValueError("ef 必须大于 0")
            args.extend(("EF", ef))
        if filter_expression:
            args.extend(("FILTER", filter_expression))
        try:
            raw = self._redis.execute_command(*args)
        except ResponseError as exc:
            if "unknown command" in str(exc).lower() or "vectorset" in str(exc).lower():
                raise VectorSetUnavailable("Redis Vector Set VSIM 不可用") from exc
            raise
        return parse_vsim_response(raw)

    def card(self, entity_kind: EntityKind | str, index_version: str) -> int:
        raw = self._redis.execute_command("VCARD", self.key(entity_kind, index_version))
        return int(raw or 0)

    def embedding(self, entity_kind: EntityKind | str, index_version: str, entity_id: int) -> bytes | None:
        raw = self._redis.execute_command("VEMB", self.key(entity_kind, index_version), vector_member(entity_kind, entity_id), "RAW")
        return raw if isinstance(raw, bytes) else None


def safe_attributes(
    *,
    entity_kind: EntityKind,
    entity_id: int,
    subject_id: int | None = None,
    name: str = "",
    aliases: Sequence[str] = (),
    content_hash: str = "",
    schema_version: str = "",
    source_active: bool = True,
    **metadata: Any,
) -> dict[str, Any]:
    """Build the allowlisted public attributes stored beside a vector."""

    attributes: dict[str, Any] = {
        "entity_kind": entity_kind.value,
        "entity_id": int(entity_id),
        "source_active": bool(source_active),
        "name": str(name)[:_MAX_MEMBER_LENGTH],
        "aliases": [str(item)[:_MAX_MEMBER_LENGTH] for item in aliases if str(item)],
        "content_hash": str(content_hash),
        "schema_version": str(schema_version),
    }
    if subject_id is not None:
        attributes["subject_id"] = int(subject_id)
    for key in ("type", "nsfw", "year", "quarter", "score", "rating_total", "collection_total", "air_status"):
        if key in metadata and metadata[key] is not None:
            attributes[key] = metadata[key]
    return attributes


def _command_info_present(info: Any) -> bool:
    """Redis returns ``[None]`` for an unknown COMMAND INFO entry."""
    if not info:
        return False
    if isinstance(info, Mapping):
        return any(item is not None for item in info.values())
    if isinstance(info, (list, tuple)):
        return any(item is not None for item in info)
    return True
