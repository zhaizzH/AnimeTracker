"""数据库写入器测试"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Subject, Episode, SubjectTag, ImportRecord
from db_writer import DatabaseManager


@pytest.fixture
def db_manager():
    """使用内存 SQLite 的 DatabaseManager"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    mgr = DatabaseManager(session=session)
    yield mgr
    session.close()


class TestUpsertSubject:
    def test_insert_new(self, db_manager):
        """插入新条目"""
        subject = db_manager.upsert_subject(
            bangumi_id=12,
            name="ちょびっツ",
            name_cn="人形电脑天使心",
            type=2,
            eps=27,
            air_date=date(2002, 4, 2),
            score=Decimal("7.6"),
            rank=573,
            collection_total=3817,
            image="https://lain.bgm.tv/pic/cover/l/c2/0a/12_24O6L.jpg",
            summary="在不久的将来...",
            nsfw=False,
        )
        assert subject.id is not None
        assert subject.bangumi_id == 12
        assert subject.name_cn == "人形电脑天使心"
        # import_status 应为 1（已导入）
        assert subject.import_status == 1
        assert subject.last_imported_at is not None

    def test_upsert_update_existing(self, db_manager):
        """更新已存在的条目"""
        db_manager.upsert_subject(bangumi_id=12, name="Chobits", name_cn="人形电脑天使心", type=2)
        updated = db_manager.upsert_subject(
            bangumi_id=12, name="Chobits (Updated)", name_cn="人形电脑天使心", type=2,
        )
        assert updated.name == "Chobits (Updated)"
        # 只应该有一条记录
        count = db_manager.session.query(Subject).filter_by(bangumi_id=12).count()
        assert count == 1

    def test_nullable_fields(self, db_manager):
        """可选字段可以为 None"""
        subject = db_manager.upsert_subject(bangumi_id=99, name="Minimal", type=2)
        assert subject.summary is None
        assert subject.score is None
        assert subject.air_date is None


class TestUpsertEpisodes:
    def test_batch_upsert(self, db_manager):
        """批量写入剧集"""
        subject = db_manager.upsert_subject(bangumi_id=1, name="Test", type=2)
        episodes = [
            {"bangumi_ep_id": 101, "type": 0, "sort": Decimal("1"), "name": "EP1", "airdate": date(2024, 1, 1), "status": "Air"},
            {"bangumi_ep_id": 102, "type": 0, "sort": Decimal("2"), "name": "EP2", "airdate": date(2024, 1, 8), "status": "Air"},
        ]
        db_manager.upsert_episodes(subject.id, episodes)
        count = db_manager.session.query(Episode).filter_by(subject_id=subject.id).count()
        assert count == 2

    def test_upsert_existing(self, db_manager):
        """剧集 UPSERT 不产生重复"""
        subject = db_manager.upsert_subject(bangumi_id=1, name="Test", type=2)
        ep_data = {"bangumi_ep_id": 101, "type": 0, "sort": Decimal("1"), "name": "EP1 Original"}
        db_manager.upsert_episodes(subject.id, [ep_data])

        ep_data["name"] = "EP1 Updated"
        db_manager.upsert_episodes(subject.id, [ep_data])

        count = db_manager.session.query(Episode).filter_by(subject_id=subject.id, bangumi_ep_id=101).count()
        assert count == 1
        name = db_manager.session.query(Episode.name).filter_by(subject_id=subject.id, bangumi_ep_id=101).scalar()
        assert name == "EP1 Updated"


class TestUpsertTags:
    def test_insert_tags(self, db_manager):
        """插入标签"""
        subject = db_manager.upsert_subject(bangumi_id=1, name="Test", type=2)
        tags = [
            {"name": "科幻", "count": 100},
            {"name": "原创", "count": 50},
        ]
        db_manager.upsert_tags(subject.id, tags)
        count = db_manager.session.query(SubjectTag).filter_by(subject_id=subject.id).count()
        assert count == 2

    def test_unique_constraint(self, db_manager):
        """同一标签不重复"""
        subject = db_manager.upsert_subject(bangumi_id=1, name="Test", type=2)
        tags = [{"name": "科幻", "count": 100}]
        db_manager.upsert_tags(subject.id, tags)
        db_manager.upsert_tags(subject.id, [{"name": "科幻", "count": 200}])
        count = db_manager.session.query(SubjectTag).filter_by(subject_id=subject.id, name="科幻").count()
        assert count == 1


class TestImportRecord:
    def test_create_and_complete(self, db_manager):
        """创建导入记录并标记完成"""
        record = db_manager.create_import_record(mode="full")
        assert record.status == "RUNNING"

        db_manager.complete_import_record(record.id, subject_count=100)
        completed = db_manager.session.get(ImportRecord, record.id)
        assert completed.status == "COMPLETED"
        assert completed.completed_at is not None
        assert completed.subject_count == 100

    def test_fail_record(self, db_manager):
        """标记导入失败"""
        record = db_manager.create_import_record(mode="season", season_key="2024-spring")
        db_manager.fail_import_record(record.id, error="Connection timeout")
        failed = db_manager.session.get(ImportRecord, record.id)
        assert failed.status == "FAILED"
        assert "Connection timeout" in (failed.error_message or "")
