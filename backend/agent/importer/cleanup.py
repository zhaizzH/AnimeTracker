"""显式摘要确认后的最小数据修复执行器。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from sqlalchemy import text

from .quality import database_fingerprint, git_state, minio_fingerprint


class ConfirmationMismatch(RuntimeError):
    """执行前状态与已审批报告不一致。"""


@dataclass(frozen=True)
class CleanupResult:
    applied: int
    skipped: int


def write_cleanup_plan(report, path: str | Path) -> str:
    payload = report.as_dict() if hasattr(report, "as_dict") else dict(report)
    _validate_report(payload)
    target = Path(path)
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    target.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def apply_cleanup_plan(path: str | Path, confirm_sha256: str | None, db, minio, *, commit: str | None = None, dirty: bool | None = None) -> CleanupResult:
    target = Path(path)
    content = target.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if not confirm_sha256 or confirm_sha256 != digest:
        raise ConfirmationMismatch("cleanup requires the exact report SHA-256")
    payload = json.loads(content)
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

    applied = skipped = 0
    for item in payload["items"]:
        if item["action"] == "DELETE" and item["category"] == "UNREFERENCED_OBJECT":
            _delete_reported_object(minio, item["target"])
            applied += 1
        elif item["action"] == "DELETE":
            _delete_database_target(db, item)
            applied += 1
        else:
            skipped += 1
    return CleanupResult(applied, skipped)


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


def _validate_report(payload: Mapping[str, Any]) -> None:
    expected = {"generatedAt", "commit", "dirty", "databaseFingerprint", "minioFingerprint", "counts", "items"}
    if set(payload) != expected or not isinstance(payload["items"], list):
        raise ConfirmationMismatch("invalid quality report")
    for item in payload["items"]:
        if set(item) != {"category", "action", "target", "details"}:
            raise ConfirmationMismatch("invalid quality report item")
        if item["category"] not in {"NON_ANIME", "NSFW", "SOURCE_MISSING", "SELF_RELATION", "MISSING_COVER_OBJECT", "UNREFERENCED_OBJECT", "NO_EPISODES", "EPISODE_SHORTAGE", "EPISODE_STATUS_DRIFT", "BLANK_TAG", "NOISY_TAG"}:
            raise ConfirmationMismatch("invalid quality report category")
        if item["action"] not in {"DELETE", "REPAIR", "REIMPORT", "KEEP_SOURCE_FALLBACK", "REVIEW"}:
            raise ConfirmationMismatch("invalid quality report action")


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
    print(json.dumps({"applied": result.applied, "skipped": result.skipped}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
