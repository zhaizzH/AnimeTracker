"""显式摘要确认后的最小数据修复执行器。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from sqlalchemy import text

from .quality import CATEGORIES, database_fingerprint, git_state, minio_fingerprint


class ConfirmationMismatch(RuntimeError):
    """执行前状态与已审批报告不一致。"""


@dataclass(frozen=True)
class CleanupResult:
    applied: int
    manual_review: int


def write_cleanup_plan(report, path: str | Path) -> str:
    try:
        payload = report.as_dict() if hasattr(report, "as_dict") else dict(report)
    except (TypeError, ValueError) as error:
        raise ConfirmationMismatch("invalid quality report") from error
    _validate_report(payload)
    target = Path(path)
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    target.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def apply_cleanup_plan(path: str | Path, confirm_sha256: str | None, db, minio, *, commit: str | None = None, dirty: bool | None = None) -> CleanupResult:
    target = Path(path)
    try:
        content = target.read_bytes()
    except OSError as error:
        raise ConfirmationMismatch("unable to read quality report") from error
    digest = hashlib.sha256(content).hexdigest()
    if not confirm_sha256 or confirm_sha256 != digest:
        raise ConfirmationMismatch("cleanup requires the exact report SHA-256")
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConfirmationMismatch("invalid quality report JSON") from error
    _validate_report(payload)
    actual_commit, actual_dirty = git_state() if commit is None or dirty is None else (commit, dirty)
    if payload["commit"] != actual_commit or bool(payload["dirty"]) != bool(actual_dirty):
        raise ConfirmationMismatch("report git state has changed")
    if payload["databaseFingerprint"] != database_fingerprint(db):
        raise ConfirmationMismatch("database fingerprint has changed")
    if payload["minioFingerprint"] != minio_fingerprint(minio):
        raise ConfirmationMismatch("MinIO fingerprint has changed")
    # SQLAlchemy 的只读 fingerprint 查询会开启事务；结束它后每个目标才能各自提交。
    if hasattr(db, "commit"):
        db.commit()

    applied = manual_review = 0
    for item in payload["items"]:
        if item["action"] == "REVIEW":
            manual_review += 1
        elif item["action"] == "DELETE" and item["category"] == "UNREFERENCED_OBJECT":
            _delete_reported_object(minio, item["target"])
            applied += 1
        elif item["action"] == "DELETE":
            _delete_database_target(db, item)
            applied += 1
        else:
            _apply_database_action(db, item)
            applied += 1
    return CleanupResult(applied, manual_review)


def _delete_database_target(db, item: Mapping[str, Any]) -> None:
    statements = {
        "NON_ANIME": "DELETE FROM subject WHERE id=:id",
        "NSFW": "DELETE FROM subject WHERE id=:id",
        "SELF_RELATION": "DELETE FROM subject_relation WHERE id=:id",
        "BLANK_TAG": "DELETE FROM subject_tag WHERE id=:id",
    }
    statement = statements.get(item["category"])
    if statement is None:
        raise ConfirmationMismatch("report includes an unsupported database deletion")
    with db.begin():
        db.execute(text(statement), {"id": int(item["target"])})


def _apply_database_action(db, item: Mapping[str, Any]) -> None:
    category, action = item["category"], item["action"]
    with db.begin():
        if action == "REIMPORT":
            subject_id = item["target"] if isinstance(item["target"], int) else item["details"]["subjectId"]
            db.execute(text("UPDATE subject SET import_status=0 WHERE id=:id"), {"id": int(subject_id)})
        elif category == "MISSING_COVER_OBJECT" and action == "KEEP_SOURCE_FALLBACK":
            db.execute(text("UPDATE subject SET image=image_source_url, image_storage_status='SOURCE_FALLBACK' WHERE id=:id"), {"id": int(item["details"]["subjectId"])})
        elif category == "EPISODE_STATUS_DRIFT" and action == "REPAIR":
            db.execute(text("UPDATE episode SET status=:status WHERE id=:id"), {"id": int(item["target"]), "status": item["details"]["expectedStatus"]})
        else:
            raise ConfirmationMismatch("report includes an unsupported repair action")


def _delete_reported_object(minio, target: object) -> None:
    if not isinstance(target, str) or not target.startswith("covers/") or any(char in target for char in "*?\\") or "://" in target:
        raise ConfirmationMismatch("unreferenced object target is invalid")
    if hasattr(minio, "delete_object"):
        minio.delete_object(target)
        return
    client = getattr(minio, "_minio", minio)
    bucket = getattr(minio, "_bucket", None) or getattr(minio, "bucket_name", None)
    if not bucket:
        raise ConfirmationMismatch("MinIO bucket name is required for deletion")
    client.remove_object(bucket, target)


def _validate_report(payload: object) -> None:
    expected = {"generatedAt", "commit", "dirty", "databaseFingerprint", "minioFingerprint", "counts", "items"}
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise ConfirmationMismatch("invalid quality report")
    if not isinstance(payload["generatedAt"], str) or not isinstance(payload["commit"], str) or not isinstance(payload["dirty"], bool) or not isinstance(payload["databaseFingerprint"], str) or not isinstance(payload["minioFingerprint"], str):
        raise ConfirmationMismatch("invalid quality report metadata")
    if not isinstance(payload["items"], list) or not isinstance(payload["counts"], Mapping) or set(payload["counts"]) != set(CATEGORIES):
        raise ConfirmationMismatch("invalid quality report")
    actual_counts = {category: 0 for category in CATEGORIES}
    for item in payload["items"]:
        if not isinstance(item, Mapping) or set(item) != {"category", "action", "target", "details"} or not isinstance(item["details"], Mapping):
            raise ConfirmationMismatch("invalid quality report item")
        if item["category"] not in CATEGORIES:
            raise ConfirmationMismatch("invalid quality report category")
        _validate_item(item)
        actual_counts[item["category"]] += 1
    if any(not isinstance(payload["counts"][category], int) or isinstance(payload["counts"][category], bool) or payload["counts"][category] < 0 or payload["counts"][category] != actual_counts[category] for category in CATEGORIES):
        raise ConfirmationMismatch("quality report counts do not match items")


def _validate_item(item: Mapping[str, Any]) -> None:
    category, action, target, details = item["category"], item["action"], item["target"], item["details"]
    rules = {
        "NON_ANIME": {"DELETE"}, "NSFW": {"DELETE"}, "SOURCE_MISSING": {"REIMPORT"},
        "SELF_RELATION": {"DELETE"}, "MISSING_COVER_OBJECT": {"KEEP_SOURCE_FALLBACK", "REIMPORT"},
        "UNREFERENCED_OBJECT": {"DELETE"}, "NO_EPISODES": {"REIMPORT"}, "EPISODE_SHORTAGE": {"REIMPORT"},
        "EPISODE_STATUS_DRIFT": {"REPAIR"}, "BLANK_TAG": {"DELETE"}, "NOISY_TAG": {"REVIEW"},
    }
    if action not in rules[category]:
        raise ConfirmationMismatch("invalid quality report action")
    if category in {"MISSING_COVER_OBJECT", "UNREFERENCED_OBJECT"}:
        if not isinstance(target, str) or not target.startswith("covers/") or any(char in target for char in "*?\\") or "://" in target:
            raise ConfirmationMismatch("invalid quality object target")
    elif not isinstance(target, int) or isinstance(target, bool) or target < 1:
        raise ConfirmationMismatch("invalid quality database target")
    if category == "MISSING_COVER_OBJECT" and (not isinstance(details.get("subjectId"), int) or details["subjectId"] < 1):
        raise ConfirmationMismatch("invalid missing-cover details")
    if category == "EPISODE_STATUS_DRIFT" and details.get("expectedStatus") not in {"Air", "Today", "NA"}:
        raise ConfirmationMismatch("invalid episode-status details")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply an approved RAG data quality report")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--confirm-sha256")
    args = parser.parse_args(argv)
    if not args.confirm_sha256:
        return 2
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
    try:
        with Session(engine) as db:
            result = apply_cleanup_plan(args.plan, args.confirm_sha256, db, ObjectStorage())
    except ConfirmationMismatch as error:
        print(str(error))
        return 2
    print(json.dumps({"applied": result.applied, "manualReview": result.manual_review}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
