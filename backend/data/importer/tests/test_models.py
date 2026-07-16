"""验证 SQLAlchemy 模型字段与 init.sql 中定义的 schema 一致"""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from models import Subject, Episode, SubjectTag, ImportRecord, Base


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_subject_table_columns(engine):
    """验证 Subject 模型包含 init.sql 中 subject 表的所有字段"""
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("subject")}
    expected = {
        "id", "bangumi_id", "name", "name_cn", "summary",
        "type", "eps", "volumes", "air_date", "air_weekday",
        "image", "score", "rank", "collection_total", "nsfw",
        "import_status", "last_imported_at", "created_at", "updated_at",
    }
    assert expected.issubset(columns), f"Missing fields: {expected - columns}"
    # 验证唯一约束
    unique_constraints = inspector.get_unique_constraints("subject")
    assert any("bangumi_id" in c["column_names"] for c in unique_constraints)


def test_episode_table_columns(engine):
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("episode")}
    expected = {
        "id", "subject_id", "bangumi_ep_id", "type", "sort",
        "name", "name_cn", "duration", "airdate", "description",
        "status", "created_at",
    }
    assert expected.issubset(columns)


def test_subject_tag_table(engine):
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("subject_tag")}
    assert {"id", "subject_id", "name", "count"}.issubset(columns)
    unique_constraints = inspector.get_unique_constraints("subject_tag")
    assert any(set(c["column_names"]) == {"subject_id", "name"} for c in unique_constraints)


def test_import_record_table(engine):
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("import_record")}
    expected = {
        "id", "mode", "season_key", "started_at",
        "completed_at", "status", "subject_count", "error_message", "created_at",
    }
    assert expected.issubset(columns)


def test_subject_crud(engine):
    """CURD 基本操作 — SQLite 测试需显式设置 BigInteger PK"""
    from datetime import date
    with Session(engine) as session:
        s = Subject(
            id=1,  # SQLite: BigInteger PK needs explicit id
            bangumi_id=1,
            name="Test Anime",
            name_cn="测试动画",
            type=2,
            eps=12,
            air_date=date(2024, 1, 1),
            air_weekday=1,
            score=7.5,
            rank=100,
        )
        session.add(s)
        session.commit()
        fetched = session.query(Subject).filter_by(bangumi_id=1).first()
        assert fetched is not None
        assert fetched.name == "Test Anime"
        assert fetched.name_cn == "测试动画"
