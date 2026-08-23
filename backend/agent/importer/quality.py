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

    @property
    def items(self) -> tuple[QualityItem, ...]:
        return tuple(item for category in CATEGORIES for item in self.categories[category])

    def as_dict(self) -> dict[str, Any]:
        return {
            "generatedAt": self.generated_at.isoformat(),
            "commit": self.commit,
            "dirty": self.dirty,
            "databaseFingerprint": self.database_fingerprint,
            "minioFingerprint": self.minio_fingerprint,
            "counts": {category: len(self.categories[category]) for category in CATEGORIES},
            "items": [item.as_dict() for item in self.items],
        }


def database_fingerprint(db) -> str:
    """用目录行数和最后更新时间生成轻量的执行前指纹。"""
    result = db.execute(text(
        "SELECT SHA2(CONCAT(COUNT(*), ':', COALESCE(MAX(updated_at), '')), 256) AS database_fingerprint FROM subject"
    ))
    value = result.scalar()
    return str(value or "empty")


def minio_fingerprint(minio) -> str:
    if hasattr(minio, "fingerprint"):
        return str(minio.fingerprint())
    import hashlib

    names = sorted(_list_object_names(minio))
    return hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()


def build_quality_report(db, minio, as_of: datetime) -> QualityReport:
    """检查约定的 11 类问题，所有查询均为只读。"""
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    grouped: dict[Category, list[QualityItem]] = {category: [] for category in CATEGORIES}
    subjects = _rows(db, "SELECT id, bangumi_id, type, nsfw, image, image_source_url, image_storage_status, eps, source_fetched_at FROM subject")
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
        if not subject.get("source_fetched_at"):
            grouped["SOURCE_MISSING"].append(_item("SOURCE_MISSING", "REIMPORT", subject_id, {}))

        object_name = canonical_cover_object_path(subject.get("image"), minio)
        if object_name:
            referenced_objects.add(object_name)
            if subject.get("image_storage_status") == "STORED" and object_name not in object_names:
                action: Action = "KEEP_SOURCE_FALLBACK" if subject.get("image_source_url") else "REIMPORT"
                grouped["MISSING_COVER_OBJECT"].append(_item("MISSING_COVER_OBJECT", action, object_name, {"subjectId": subject_id}))

        expected_eps = subject.get("eps")
        actual_eps = episode_counts.get(subject_id, 0)
        if isinstance(expected_eps, int) and expected_eps > 0:
            if actual_eps == 0:
                grouped["NO_EPISODES"].append(_item("NO_EPISODES", "REIMPORT", subject_id, {"expected": expected_eps}))
            elif actual_eps < expected_eps:
                grouped["EPISODE_SHORTAGE"].append(_item("EPISODE_SHORTAGE", "REIMPORT", subject_id, {"expected": expected_eps, "actual": actual_eps}))

    for row in _rows(db, "SELECT id, subject_id, related_subject_id FROM subject_relation WHERE subject_id = related_subject_id"):
        grouped["SELF_RELATION"].append(_item("SELF_RELATION", "DELETE", int(row["id"]), {"subjectId": int(row["subject_id"])}))
    for row in _rows(db, "SELECT id, subject_id, status, airdate FROM episode WHERE status <> 'NA' AND airdate IS NOT NULL"):
        if _episode_status_drift(row, as_of):
            grouped["EPISODE_STATUS_DRIFT"].append(_item("EPISODE_STATUS_DRIFT", "REPAIR", int(row["id"]), {"subjectId": int(row["subject_id"])}))
    for row in _rows(db, "SELECT id, subject_id, name FROM subject_tag"):
        name = str(row.get("name") or "")
        if not name.strip():
            grouped["BLANK_TAG"].append(_item("BLANK_TAG", "DELETE", int(row["id"]), {"subjectId": int(row["subject_id"])}))
        elif len(name) > 64 or "\n" in name:
            grouped["NOISY_TAG"].append(_item("NOISY_TAG", "REVIEW", int(row["id"]), {"subjectId": int(row["subject_id"])}))
    for name in sorted(object_names - referenced_objects):
        grouped["UNREFERENCED_OBJECT"].append(_item("UNREFERENCED_OBJECT", "DELETE", name, {}))

    commit, dirty = git_state()
    return QualityReport(as_of, commit, dirty, database_fingerprint(db), minio_fingerprint(minio), {key: tuple(value) for key, value in grouped.items()})


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
        return image.lstrip("/") if image.startswith("covers/") else None
    parts = [part for part in parsed.path.split("/") if part]
    bucket = getattr(minio, "bucket_name", None) or getattr(minio, "_bucket", None)
    if bucket and parts[:1] == [bucket]:
        parts = parts[1:]
    elif parts and parts[0] == "anime-tracker":
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


def _episode_status_drift(row: Mapping[str, Any], as_of: datetime) -> bool:
    airdate = row.get("airdate")
    if isinstance(airdate, str):
        try:
            airdate = datetime.fromisoformat(airdate).date()
        except ValueError:
            return False
    if not hasattr(airdate, "isoformat"):
        return False
    expected = "Air" if airdate < as_of.date() else "Today" if airdate == as_of.date() else "NA"
    return row.get("status") != expected


def _item(category: Category, action: Action, target: int | str, details: Mapping[str, Any]) -> QualityItem:
    return QualityItem(category, action, target, details)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only RAG data quality report")
    parser.add_argument("--output", required=True)
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
    with Session(engine) as db:
        report = build_quality_report(db, ObjectStorage(), datetime.now(timezone.utc))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    digest = write_quality_report(report, output)
    print(f"report={output}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
