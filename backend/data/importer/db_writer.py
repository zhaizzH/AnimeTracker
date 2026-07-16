"""
数据库写入器。

使用 SQLAlchemy 将数据 UPSERT 写入 MySQL。
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models import Subject, Episode, SubjectTag, ImportRecord

logger = logging.getLogger(__name__)


class DatabaseManager:
    """封装数据库写入操作。"""

    def __init__(self, session: Session | None = None):
        from database import SessionFactory
        self.session = session or SessionFactory()

    def close(self):
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    # ── Subject ──────────────────────────────────────────

    def upsert_subject(
        self,
        bangumi_id: int,
        name: str,
        name_cn: str | None = None,
        summary: str | None = None,
        type: int = 2,
        eps: int | None = None,
        volumes: int | None = None,
        air_date: date | None = None,
        air_weekday: int | None = None,
        image: str | None = None,
        score: Decimal | None = None,
        rank: int | None = None,
        collection_total: int | None = None,
        nsfw: bool = False,
    ) -> Subject:
        """插入或更新条目。返回 Subject 实例。"""
        subject = self.session.query(Subject).filter_by(bangumi_id=bangumi_id).first()
        if subject is None:
            subject = Subject(bangumi_id=bangumi_id)
            self.session.add(subject)

        subject.name = name
        subject.name_cn = name_cn
        subject.summary = summary
        subject.type = type
        subject.eps = eps
        subject.volumes = volumes
        subject.air_date = air_date
        subject.air_weekday = air_weekday
        subject.image = image
        subject.score = score
        subject.rank = rank
        subject.collection_total = collection_total
        subject.nsfw = nsfw
        subject.import_status = 1  # 标记为已导入
        subject.last_imported_at = datetime.now()

        self.session.flush()
        return subject

    def get_subject_by_bangumi_id(self, bangumi_id: int) -> Subject | None:
        """通过 bangumi_id 查询本地条目。"""
        return self.session.query(Subject).filter_by(bangumi_id=bangumi_id).first()

    # ── Episode ──────────────────────────────────────────

    def upsert_episodes(self, local_subject_id: int, episodes: list[dict[str, Any]]):
        """批量写入剧集。已存在的按 bangumi_ep_id 更新。"""
        for ep_data in episodes:
            bangumi_ep_id = ep_data.get("bangumi_ep_id")
            episode = self.session.query(Episode).filter_by(
                subject_id=local_subject_id,
                bangumi_ep_id=bangumi_ep_id,
            ).first()
            if episode is None:
                episode = Episode(subject_id=local_subject_id, bangumi_ep_id=bangumi_ep_id)
                self.session.add(episode)

            episode.type = ep_data.get("type", 0)
            if ep_data.get("sort") is not None:
                episode.sort = Decimal(str(ep_data["sort"])) if not isinstance(ep_data["sort"], Decimal) else ep_data["sort"]
            episode.name = ep_data.get("name")
            episode.name_cn = ep_data.get("name_cn")
            episode.duration = ep_data.get("duration")
            if isinstance(ep_data.get("airdate"), date):
                episode.airdate = ep_data["airdate"]
            elif isinstance(ep_data.get("airdate"), str) and ep_data["airdate"]:
                episode.airdate = datetime.strptime(ep_data["airdate"], "%Y-%m-%d").date()
            episode.description = ep_data.get("desc") or ep_data.get("description")
            episode.status = ep_data.get("status", "NA")

        self.session.flush()

    # ── Tag ──────────────────────────────────────────────

    def upsert_tags(self, local_subject_id: int, tags: list[dict[str, Any]]):
        """批量写入标签。已存在的按 (subject_id, name) 更新 count。"""
        for tag_data in tags:
            name = tag_data.get("name", "").strip()
            if not name:
                continue

            tag = self.session.query(SubjectTag).filter_by(
                subject_id=local_subject_id,
                name=name,
            ).first()
            if tag is None:
                tag = SubjectTag(subject_id=local_subject_id, name=name)
                self.session.add(tag)

            tag.count = tag_data.get("count", 0)

        self.session.flush()

    # ── Import Record ────────────────────────────────────

    def create_import_record(
        self,
        mode: str,
        season_key: str | None = None,
    ) -> ImportRecord:
        """创建导入记录。"""
        record = ImportRecord(mode=mode, season_key=season_key, status="RUNNING")
        self.session.add(record)
        self.session.flush()
        return record

    def complete_import_record(self, record_id: int, subject_count: int):
        """标记导入为完成。"""
        record = self.session.get(ImportRecord, record_id)
        if record:
            record.status = "COMPLETED"
            record.completed_at = datetime.now()
            record.subject_count = subject_count
            self.session.flush()

    def fail_import_record(self, record_id: int, error: str):
        """标记导入为失败。"""
        record = self.session.get(ImportRecord, record_id)
        if record:
            record.status = "FAILED"
            record.completed_at = datetime.now()
            record.error_message = error
            self.session.flush()
