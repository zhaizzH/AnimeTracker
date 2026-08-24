"""只读的数据质量预览；不会修改数据库或对象存储。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Literal, Mapping, Sequence
from urllib.parse import urlparse

from sqlalchemy import text

from app.shared.observability import log_event


Category = Literal[
    "NON_ANIME", "NSFW", "SOURCE_MISSING", "SELF_RELATION", "MISSING_COVER_OBJECT",
    "UNREFERENCED_OBJECT", "NO_EPISODES", "EPISODE_SHORTAGE", "EPISODE_STATUS_DRIFT",
    "BLANK_TAG", "NOISY_TAG",
]
Action = Literal["DELETE", "REPAIR", "REIMPORT", "KEEP_SOURCE_FALLBACK", "REVIEW"]

CATEGORIES: tuple[Category, ...] = (
    "NON_ANIME", "NSFW", "SOURCE_MISSING", "SELF_RELATION", "MISSING_COVER_OBJECT",
    "UNREFERENCED_OBJECT", "NO_EPISODES", "EPISODE_SHORTAGE", "EPISODE_STATUS_DRIFT",
    "BLANK_TAG", "NOISY_TAG",
)


@dataclass(frozen=True)
class QualityItem:
    category: Category
    action: Action
    target: int | str
    details: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"category": self.category, "action": self.action, "target": self.target, "details": dict(self.details)}


@dataclass(frozen=True)
class QualityReport:
    generated_at: datetime
    commit: str
    dirty: bool
    database_fingerprint: str
    minio_fingerprint: str
    categories: Mapping[Category, tuple[QualityItem, ...]]
    index_version: str | None = None
    embedding_contract: Mapping[str, Any] | None = None
    coverage: float | None = None
    content_hash_samples: tuple[Mapping[str, Any], ...] | None = None

    @property
    def items(self) -> tuple[QualityItem, ...]:
        return tuple(item for category in CATEGORIES for item in self.categories[category])

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "generatedAt": self.generated_at.isoformat(),
            "commit": self.commit,
            "dirty": self.dirty,
            "databaseFingerprint": self.database_fingerprint,
            "minioFingerprint": self.minio_fingerprint,
            "counts": {category: len(self.categories[category]) for category in CATEGORIES},
            "items": [item.as_dict() for item in self.items],
        }
        if self.index_version:
            payload["indexVersion"] = self.index_version
        if self.embedding_contract:
            payload["embeddingContract"] = dict(self.embedding_contract)
        if self.coverage is not None:
            payload["coverage"] = self.coverage
        if self.content_hash_samples is not None:
            payload["contentHashSamples"] = [dict(item) for item in self.content_hash_samples]
        return payload


def database_fingerprint(db) -> str:
    """覆盖所有清理目标表的稳定摘要，供 apply 前失效检测使用。"""
    result = db.execute(text(
        "SELECT SHA2(CONCAT_WS('|', "
        "(SELECT CONCAT(COUNT(*), ':', COALESCE(MAX(updated_at), ''), ':', COALESCE(SUM(id), 0), ':', "
        "COALESCE(SUM(CRC32(CONCAT_WS(':', id, bangumi_id, type, nsfw, import_status, eps, image, image_source_url, image_storage_status, source_fetched_at))), 0)) FROM subject), "
        "(SELECT CONCAT(COUNT(*), ':', COALESCE(SUM(id), 0), ':', COALESCE(SUM(CRC32(CONCAT_WS(':', id, subject_id, related_subject_id, relation))), 0)) FROM subject_relation), "
        "(SELECT CONCAT(COUNT(*), ':', COALESCE(SUM(id), 0), ':', COALESCE(SUM(CRC32(CONCAT_WS(':', id, subject_id, name))), 0)) FROM subject_tag), "
        "(SELECT CONCAT(COUNT(*), ':', COALESCE(SUM(id), 0), ':', COALESCE(SUM(CRC32(CONCAT_WS(':', id, subject_id, status, airdate))), 0)) FROM episode)"
        "), 256) AS database_fingerprint"
    ))
    value = result.scalar()
    return str(value or "empty")


def minio_fingerprint(minio) -> str:
    if hasattr(minio, "fingerprint"):
        return str(minio.fingerprint())
    import hashlib

    names = sorted(_list_object_names(minio))
    return hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()


def build_quality_report(
    db,
    minio,
    as_of: datetime,
    *,
    index_version: str | None = None,
    embedding_contract: Mapping[str, Any] | None = None,
    redis_index: Any | None = None,
) -> QualityReport:
    """检查约定的 11 类问题，所有查询均为只读。"""
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    grouped: dict[Category, list[QualityItem]] = {category: [] for category in CATEGORIES}
    subjects = _rows(db, "SELECT id, bangumi_id, type, nsfw, image, image_source_url, image_storage_status, eps, source_fetched_at, import_status FROM subject")
    episode_counts = {int(row["subject_id"]): int(row["episode_count"] or 0) for row in _rows(
        db, "SELECT subject_id, COUNT(*) AS episode_count FROM episode GROUP BY subject_id"
    )}
    object_names = set(_list_object_names(minio))
    referenced_objects: set[str] = set()

    for subject in subjects:
        subject_id = int(subject["id"])
        if int(subject.get("type") or 0) != 2:
            grouped["NON_ANIME"].append(_item("NON_ANIME", "DELETE", subject_id, {"bangumiId": subject.get("bangumi_id")}))
        if bool(subject.get("nsfw")):
            grouped["NSFW"].append(_item("NSFW", "DELETE", subject_id, {"bangumiId": subject.get("bangumi_id")}))
        active_import = int(subject.get("import_status") or 0) == 1
        if active_import and not subject.get("source_fetched_at"):
            grouped["SOURCE_MISSING"].append(_item("SOURCE_MISSING", "REIMPORT", subject_id, {}))

        object_name = canonical_cover_object_path(subject.get("image"), minio)
        if object_name:
            referenced_objects.add(object_name)
            if subject.get("image_storage_status") == "STORED" and object_name not in object_names:
                action: Action = "KEEP_SOURCE_FALLBACK" if subject.get("image_source_url") else "REIMPORT"
                grouped["MISSING_COVER_OBJECT"].append(_item("MISSING_COVER_OBJECT", action, object_name, {"subjectId": subject_id}))

        expected_eps = subject.get("eps")
        actual_eps = episode_counts.get(subject_id, 0)
        if active_import and isinstance(expected_eps, int) and expected_eps > 0:
            if actual_eps == 0:
                grouped["NO_EPISODES"].append(_item("NO_EPISODES", "REIMPORT", subject_id, {"expected": expected_eps}))
            elif actual_eps < expected_eps:
                grouped["EPISODE_SHORTAGE"].append(_item("EPISODE_SHORTAGE", "REIMPORT", subject_id, {"expected": expected_eps, "actual": actual_eps}))

    for row in _rows(db, "SELECT id, subject_id, related_subject_id FROM subject_relation WHERE subject_id = related_subject_id"):
        grouped["SELF_RELATION"].append(_item("SELF_RELATION", "DELETE", int(row["id"]), {"subjectId": int(row["subject_id"])}))
    for row in _rows(db, "SELECT id, subject_id, status, airdate FROM episode WHERE airdate IS NOT NULL"):
        expected_status = _expected_episode_status(row.get("airdate"), as_of)
        if expected_status is not None and row.get("status") != expected_status:
            grouped["EPISODE_STATUS_DRIFT"].append(_item("EPISODE_STATUS_DRIFT", "REPAIR", int(row["id"]), {"subjectId": int(row["subject_id"]), "expectedStatus": expected_status}))
    for row in _rows(db, "SELECT id, subject_id, name FROM subject_tag"):
        name = str(row.get("name") or "")
        if not name.strip():
            grouped["BLANK_TAG"].append(_item("BLANK_TAG", "DELETE", int(row["id"]), {"subjectId": int(row["subject_id"])}))
        elif len(name) > 64 or "\n" in name:
            grouped["NOISY_TAG"].append(_item("NOISY_TAG", "REVIEW", int(row["id"]), {"subjectId": int(row["subject_id"])}))
    for name in sorted(object_names - referenced_objects):
        grouped["UNREFERENCED_OBJECT"].append(_item("UNREFERENCED_OBJECT", "DELETE", name, {}))

    commit, dirty = git_state()
    database_digest = database_fingerprint(db)
    coverage = None
    samples = None
    if index_version:
        if redis_index is None:
            raise RuntimeError("带 index_version 的质量报告必须读取目标 Redis 索引")
        expected_hashes = _expected_content_hashes(db, index_version)
        reader = getattr(redis_index, "content_hashes", None)
        if not callable(reader):
            raise RuntimeError("目标 Redis 索引不支持 content_hash 抽样读取")
        observed_hashes = reader(index_version)
        if not isinstance(observed_hashes, Mapping):
            raise RuntimeError("目标 Redis content_hash 读取结果无效")
        qualified_ids = {int(subject["id"]) for subject in subjects if int(subject.get("type") or 0) == 2 and not bool(subject.get("nsfw"))}
        indexed_ids = {subject_id for subject_id in qualified_ids if expected_hashes.get(subject_id) and observed_hashes.get(subject_id)}
        coverage = len(indexed_ids) / len(qualified_ids) if qualified_ids else 0.0
        samples = tuple({"subjectId": subject_id, "expected": expected_hashes.get(subject_id, ""), "observed": str(observed_hashes.get(subject_id) or "")} for subject_id in sorted(qualified_ids)[:20])
    return QualityReport(as_of, commit, dirty, database_digest, minio_fingerprint(minio), {key: tuple(value) for key, value in grouped.items()}, index_version, embedding_contract, coverage, samples)


def write_quality_report(report: QualityReport, path: str | Path) -> str:
    """写出确定性 JSON 并返回 cleanup 必须回显的完整摘要。"""
    content = json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    Path(path).write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def canonical_cover_object_path(image: object, minio) -> str | None:
    """从公开 URL 提取桶内路径；绝不把 URL 作为 MinIO object name。"""
    if not isinstance(image, str) or not image:
        return None
    parsed = urlparse(image)
    if not parsed.scheme or not parsed.netloc:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    bucket = getattr(minio, "bucket_name", None) or getattr(minio, "_bucket", None)
    endpoint = getattr(minio, "endpoint", None) or getattr(minio, "_endpoint", None)
    if not bucket or not endpoint or parsed.netloc.lower() != _endpoint_netloc(str(endpoint)):
        return None
    if parts[:1] != [bucket]:
        return None
    parts = parts[1:]
    object_name = "/".join(parts)
    return object_name if object_name.startswith("covers/") else None


def git_state() -> tuple[str, bool]:
    root = Path(__file__).resolve().parents[3]
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(root), "status", "--porcelain"], check=True, capture_output=True, text=True).stdout.strip())
        return commit, dirty
    except (OSError, subprocess.CalledProcessError):
        return "unknown", True


def _rows(db, query: str) -> Sequence[Mapping[str, Any]]:
    return db.execute(text(query)).mappings().all()


def _list_object_names(minio) -> list[str]:
    if hasattr(minio, "list_objects"):
        objects = minio.list_objects()
    else:
        client = getattr(minio, "_minio", minio)
        bucket = getattr(minio, "_bucket", None) or getattr(minio, "bucket_name", None)
        if not bucket:
            raise ValueError("MinIO bucket name is required for quality report")
        objects = client.list_objects(bucket, recursive=True)
    return [item if isinstance(item, str) else item.object_name for item in objects]


def _expected_episode_status(airdate: object, as_of: datetime) -> str | None:
    if isinstance(airdate, str):
        try:
            airdate = datetime.fromisoformat(airdate).date()
        except ValueError:
            return None
    if not hasattr(airdate, "isoformat"):
        return None
    return "Air" if airdate < as_of.date() else "Today" if airdate == as_of.date() else "NA"


def _endpoint_netloc(endpoint: str) -> str:
    parsed = urlparse(endpoint if "://" in endpoint else f"//{endpoint}")
    return parsed.netloc.lower()


def _item(category: Category, action: Action, target: int | str, details: Mapping[str, Any]) -> QualityItem:
    return QualityItem(category, action, target, details)


def _expected_content_hashes(db, index_version: str) -> dict[int, str]:
    try:
        rows = db.execute(text("SELECT subject_id, content_hash FROM rag_index_job WHERE index_version=:index_version"), {"index_version": index_version}).mappings().all()
    except Exception as error:
        raise RuntimeError("无法读取 MySQL 权威 content_hash") from error
    result: dict[int, str] = {}
    for row in rows:
        subject_id = int(row["subject_id"])
        content_hash = str(row.get("content_hash") or "").strip()
        if not content_hash:
            raise RuntimeError("MySQL content_hash 为空")
        result[subject_id] = content_hash
    return result


def _subject_digest(subject: Mapping[str, Any]) -> str:
    content = json.dumps(dict(subject), ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only RAG data quality report")
    parser.add_argument("--output", required=True)
    parser.add_argument("--index-version")
    args = parser.parse_args(argv)
    from dotenv import load_dotenv
    from sqlalchemy.orm import Session
    try:
        from .db import get_engine
        from .storage import ObjectStorage
    except ImportError:
        from db import get_engine
        from storage import ObjectStorage
    import os

    load_dotenv()
    engine = get_engine(os.getenv("DB_HOST", "127.0.0.1"), int(os.getenv("DB_PORT", "3306")), os.getenv("DB_USER", "root"), os.getenv("DB_PASSWORD", ""), os.getenv("DB_NAME", "anime_tracker"))
    redis_index = None
    if args.index_version:
        import redis
        from app.rag.redis_index import RedisSubjectIndex
        redis_url = os.getenv("RAG_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_index = RedisSubjectIndex(redis.Redis.from_url(redis_url))
    with Session(engine) as db:
        contract = {"provider": "dashscope", "model": os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-v4"), "dimensions": int(os.getenv("RAG_EMBEDDING_DIM", "1024")), "profileVersion": os.getenv("RAG_PROFILE_VERSION", "subject-profile-v1")}
        report = build_quality_report(db, ObjectStorage(), datetime.now(timezone.utc), index_version=args.index_version, embedding_contract=contract, redis_index=redis_index)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    digest = write_quality_report(report, output)
    log_event("rag.data_quality.completed", candidateCount=len(report.items), success=True)
    print(f"report={output}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
