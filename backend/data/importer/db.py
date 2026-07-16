"""数据库模型与 upsert 操作"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# ponytail: 直接写 SQL 和 SQLAlchemy ORM 配合，不用 declarative base 减少一层概念


def get_engine(host: str, port: int, user: str, password: str, db: str):
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def _infer_weekday(air_date: str | None) -> int | None:
    """从 YYYY-MM-DD 推出星期（0=周日, 1=周一 … 6=周六）。"""
    if not air_date:
        return None
    try:
        dt = datetime.strptime(air_date, "%Y-%m-%d")
        return (dt.weekday() + 1) % 7
    except (ValueError, TypeError):
        return None


def upsert_subject(session: Session, data: dict) -> int:
    """INSERT … ON DUPLICATE KEY UPDATE subject，返回 subject.id。"""
    bangumi_id = data["id"]
    existing = session.execute(
        text("SELECT id FROM subject WHERE bangumi_id = :bid"),
        {"bid": bangumi_id},
    ).scalar()

    now = datetime.now()
    air_date = data.get("date")
    air_weekday = _infer_weekday(air_date)

    if existing:
        session.execute(
            text("""
                UPDATE subject SET
                    name = :name, name_cn = :name_cn, summary = :summary,
                    type = :type, eps = :eps, air_date = :air_date,
                    air_weekday = :air_weekday,
                    image = :image, score = :score, `rank` = :rank,
                    collection_total = :collection_total, nsfw = :nsfw,
                    import_status = 1, last_imported_at = :now,
                    updated_at = :now
                WHERE id = :id
            """),
            {
                "id": existing,
                "name": data.get("name", ""),
                "name_cn": data.get("name_cn"),
                "summary": data.get("summary", ""),
                "type": data.get("type", 2),
                "eps": max(data.get("eps") or 0, data.get("total_episodes") or 0) or None,
                "air_date": air_date,
                "air_weekday": air_weekday,
                "image": (data.get("images") or {}).get("large"),
                "score": (data.get("rating") or {}).get("score"),
                "rank": (data.get("rating") or {}).get("rank"),
                "collection_total": (data.get("collection") or {}).get("collect", 0),
                "nsfw": data.get("nsfw", False),
                "now": now,
            },
        )
        subject_id = existing
    else:
        result = session.execute(
            text("""
                INSERT INTO subject
                    (bangumi_id, name, name_cn, summary, type, eps, air_date, air_weekday,
                     image, score, `rank`, collection_total, nsfw,
                     import_status, last_imported_at, created_at, updated_at)
                VALUES
                    (:bangumi_id, :name, :name_cn, :summary, :type, :eps, :air_date, :air_weekday,
                     :image, :score, :rank, :collection_total, :nsfw,
                     1, :now, :now, :now)
            """),
            {
                "bangumi_id": bangumi_id,
                "name": data.get("name", ""),
                "name_cn": data.get("name_cn"),
                "summary": data.get("summary", ""),
                "type": data.get("type", 2),
                "eps": max(data.get("eps") or 0, data.get("total_episodes") or 0) or None,
                "air_date": air_date,
                "air_weekday": air_weekday,
                "image": (data.get("images") or {}).get("large"),
                "score": (data.get("rating") or {}).get("score"),
                "rank": (data.get("rating") or {}).get("rank"),
                "collection_total": (data.get("collection") or {}).get("collect", 0),
                "nsfw": data.get("nsfw", False),
                "now": now,
            },
        )
        subject_id = result.lastrowid

    return subject_id


def upsert_episodes(session: Session, subject_id: int, episodes: list[dict]):
    """upsert 剧集列表。使用 (subject_id, bangumi_ep_id) 作为匹配键。"""
    now = datetime.now()
    for ep in episodes:
        bangumi_ep_id = ep["id"]
        existing_id = session.execute(
            text("SELECT id FROM episode WHERE subject_id = :sid AND bangumi_ep_id = :eid"),
            {"sid": subject_id, "eid": bangumi_ep_id},
        ).scalar()

        if existing_id:
            session.execute(
                text("""
                    UPDATE episode SET
                        type = :type, sort = :sort, name = :name, name_cn = :name_cn,
                        duration = :duration, airdate = :airdate,
                        description = :description, status = :status
                    WHERE id = :id
                """),
                {
                    "id": existing_id,
                    "type": ep.get("type", 0),
                    "sort": ep.get("sort"),
                    "name": ep.get("name"),
                    "name_cn": ep.get("name_cn"),
                    "duration": ep.get("duration"),
                    "airdate": ep.get("airdate"),
                    "description": ep.get("desc", ""),
                    "status": ep.get("status", "NA"),
                },
            )
        else:
            session.execute(
                text("""
                    INSERT INTO episode
                        (subject_id, bangumi_ep_id, type, sort, name, name_cn,
                         duration, airdate, description, status, created_at)
                    VALUES
                        (:subject_id, :bangumi_ep_id, :type, :sort, :name, :name_cn,
                         :duration, :airdate, :description, :status, :now)
                """),
                {
                    "subject_id": subject_id,
                    "bangumi_ep_id": bangumi_ep_id,
                    "type": ep.get("type", 0),
                    "sort": ep.get("sort"),
                    "name": ep.get("name"),
                    "name_cn": ep.get("name_cn"),
                    "duration": ep.get("duration"),
                    "airdate": ep.get("airdate"),
                    "description": ep.get("desc", ""),
                    "status": ep.get("status", "NA"),
                    "now": now,
                },
            )


def upsert_tags(session: Session, subject_id: int, tags: list[dict]):
    """upsert 标签。使用 (subject_id, name) 作为匹配键（表中有唯一索引）。"""
    for tag in tags:
        name = tag.get("name", "")
        count = tag.get("count", 0)
        session.execute(
            text("""
                INSERT INTO subject_tag (subject_id, name, count)
                VALUES (:subject_id, :name, :count)
                ON DUPLICATE KEY UPDATE count = :count2
            """),
            {"subject_id": subject_id, "name": name, "count": count, "count2": count},
        )


def create_import_record(session: Session, mode: str, season_key: Optional[str] = None) -> int:
    """创建导入记录，返回 record_id。"""
    result = session.execute(
        text("""
            INSERT INTO import_record (mode, season_key, started_at, status, created_at)
            VALUES (:mode, :season_key, :now, 'RUNNING', :now)
        """),
        {"mode": mode, "season_key": season_key, "now": datetime.now()},
    )
    return result.lastrowid


def complete_import_record(session: Session, record_id: int, subject_count: int,
                           status: str = "COMPLETED", error_message: Optional[str] = None):
    """完成导入记录。"""
    session.execute(
        text("""
            UPDATE import_record SET
                completed_at = :now, status = :status,
                subject_count = :subject_count, error_message = :error_message
            WHERE id = :id
        """),
        {
            "id": record_id,
            "now": datetime.now(),
            "status": status,
            "subject_count": subject_count,
            "error_message": error_message,
        },
    )
