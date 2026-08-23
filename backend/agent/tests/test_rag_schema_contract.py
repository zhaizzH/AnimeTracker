from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
MIGRATION = REPOSITORY / "docs" / "database" / "migrations" / "2026-08-23-agent-rag.sql"
SCHEMA = REPOSITORY / "docs" / "database" / "db-schema.sql"

SUBJECT_COLUMNS = (
    "rating_total",
    "rating_count_json",
    "collection_wish",
    "collection_collect",
    "collection_doing",
    "collection_on_hold",
    "collection_dropped",
    "image_source_url",
    "image_storage_status",
    "image_checked_at",
    "source_fetched_at",
)
IMPORT_RECORD_COLUMNS = (
    "checkpoint_json",
    "scanned_count",
    "success_count",
    "failure_count",
    "skipped_count",
    "source_snapshot_at",
    "heartbeat_at",
)


def test_migration_is_forward_only_and_complete():
    """发布迁移只能新增 RAG 所需结构，且四张表必须可安全重复创建。"""
    sql = MIGRATION.read_text(encoding="utf-8").upper()

    assert "DROP TABLE" not in sql
    assert "DROP COLUMN" not in sql
    for name in ("SUBJECT_ALIAS", "SUBJECT_META_TAG", "SUBJECT_CREDIT", "RAG_INDEX_JOB"):
        assert f"CREATE TABLE IF NOT EXISTS `{name}`" in sql
    for column in (*SUBJECT_COLUMNS, *IMPORT_RECORD_COLUMNS):
        assert f"`{column.upper()}`" in sql
    assert "UNIQUE KEY `UK_RAG_JOB_SUBJECT_VERSION` (`SUBJECT_ID`, `INDEX_VERSION`)" in sql
    assert "UNIQUE KEY `UK_SUBJECT_META_TAG` (`SUBJECT_ID`, `NAME`)" in sql
    assert "UNIQUE KEY `UK_SUBJECT_CREDIT` (`SUBJECT_ID`, `NAME`, `ROLE`)" in sql


def test_complete_schema_includes_rag_tables_and_columns():
    """新环境初始化的完整 schema 必须包含同一套 RAG 数据模型。"""
    sql = SCHEMA.read_text(encoding="utf-8").upper()

    for name in ("SUBJECT_ALIAS", "SUBJECT_META_TAG", "SUBJECT_CREDIT", "RAG_INDEX_JOB"):
        assert f"CREATE TABLE `{name}`" in sql
    for column in (*SUBJECT_COLUMNS, *IMPORT_RECORD_COLUMNS):
        assert f"`{column.upper()}`" in sql
