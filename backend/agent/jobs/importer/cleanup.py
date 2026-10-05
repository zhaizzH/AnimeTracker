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
        raise ConfirmationMismatch("质量报告无效") from error
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
        raise ConfirmationMismatch("无法读取质量报告") from error
    digest = hashlib.sha256(content).hexdigest()
    if not confirm_sha256 or confirm_sha256 != digest:
        raise ConfirmationMismatch("清理需要精确的报告 SHA-256")
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConfirmationMismatch("质量报告 JSON 无效") from error
    _validate_report(payload)
    actual_commit, actual_dirty = git_state() if commit is None or dirty is None else (commit, dirty)
    if payload["commit"] != actual_commit or bool(payload["dirty"]) != bool(actual_dirty):
        raise ConfirmationMismatch("报告对应的 git 状态已变化")
    if payload["databaseFingerprint"] != database_fingerprint(db):
        raise ConfirmationMismatch("数据库指纹已变化")
    if payload["minioFingerprint"] != minio_fingerprint(minio):
        raise ConfirmationMismatch("MinIO 指纹已变化")
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
        raise ConfirmationMismatch("报告包含不支持的数据库删除操作")
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
            raise ConfirmationMismatch("报告包含不支持的修复动作")


def _delete_reported_object(minio, target: object) -> None:
    if not isinstance(target, str) or not target.startswith("covers/") or any(char in target for char in "*?\\") or "://" in target:
        raise ConfirmationMismatch("未引用对象目标无效")
    if hasattr(minio, "delete_object"):
        minio.delete_object(target)
        return
    client = getattr(minio, "_minio", minio)
    bucket = getattr(minio, "_bucket", None) or getattr(minio, "bucket_name", None)
    if not bucket:
        raise ConfirmationMismatch("删除操作需要 MinIO bucket 名称")
    client.remove_object(bucket, target)


def _validate_report(payload: object) -> None:
    expected = {"generatedAt", "commit", "dirty", "databaseFingerprint", "minioFingerprint", "counts", "items"}
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise ConfirmationMismatch("质量报告无效")
    if not isinstance(payload["generatedAt"], str) or not isinstance(payload["commit"], str) or not isinstance(payload["dirty"], bool) or not isinstance(payload["databaseFingerprint"], str) or not isinstance(payload["minioFingerprint"], str):
        raise ConfirmationMismatch("质量报告元数据无效")
    if not isinstance(payload["items"], list) or not isinstance(payload["counts"], Mapping) or set(payload["counts"]) != set(CATEGORIES):
        raise ConfirmationMismatch("质量报告无效")
    actual_counts = {category: 0 for category in CATEGORIES}
    for item in payload["items"]:
        if not isinstance(item, Mapping) or set(item) != {"category", "action", "target", "details"} or not isinstance(item["details"], Mapping):
            raise ConfirmationMismatch("质量报告条目无效")
        if item["category"] not in CATEGORIES:
            raise ConfirmationMismatch("质量报告分类无效")
        _validate_item(item)
        actual_counts[item["category"]] += 1
    if any(not isinstance(payload["counts"][category], int) or isinstance(payload["counts"][category], bool) or payload["counts"][category] < 0 or payload["counts"][category] != actual_counts[category] for category in CATEGORIES):
        raise ConfirmationMismatch("质量报告计数与条目不匹配")


def _validate_item(item: Mapping[str, Any]) -> None:
    category, action, target, details = item["category"], item["action"], item["target"], item["details"]
    rules = {
        "NON_ANIME": {"DELETE"}, "NSFW": {"DELETE"}, "SOURCE_MISSING": {"REIMPORT"},
        "SELF_RELATION": {"DELETE"}, "MISSING_COVER_OBJECT": {"KEEP_SOURCE_FALLBACK", "REIMPORT"},
        "UNREFERENCED_OBJECT": {"DELETE"}, "NO_EPISODES": {"REIMPORT"}, "EPISODE_SHORTAGE": {"REIMPORT"},
        "EPISODE_STATUS_DRIFT": {"REPAIR"}, "BLANK_TAG": {"DELETE"}, "NOISY_TAG": {"REVIEW"},
    }
    if action not in rules[category]:
        raise ConfirmationMismatch("质量报告动作无效")
    if category in {"MISSING_COVER_OBJECT", "UNREFERENCED_OBJECT"}:
        if not isinstance(target, str) or not target.startswith("covers/") or any(char in target for char in "*?\\") or "://" in target:
            raise ConfirmationMismatch("质量对象目标无效")
    elif not isinstance(target, int) or isinstance(target, bool) or target < 1:
        raise ConfirmationMismatch("质量数据库目标无效")
    if category == "MISSING_COVER_OBJECT" and (not isinstance(details.get("subjectId"), int) or isinstance(details["subjectId"], bool) or details["subjectId"] < 1):
        raise ConfirmationMismatch("缺少封面的详情无效")
    if category == "EPISODE_STATUS_DRIFT" and details.get("expectedStatus") not in {"Air", "Today", "NA"}:
        raise ConfirmationMismatch("剧集状态详情无效")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="应用已批准的 RAG 数据质量报告")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--confirm-sha256")
    args = parser.parse_args(argv)
    if not args.confirm_sha256:
        return 2
    from dotenv import load_dotenv
    from sqlalchemy.orm import Session
    from app.adapters.mysql.import_records import get_engine
    try:
        from .storage import ObjectStorage
    except ImportError:
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
