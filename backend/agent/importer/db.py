"""数据库模型与 upsert 操作"""

import logging
import re
import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from storage import CoverResult

# ponytail: 直接写 SQL 和 SQLAlchemy ORM 配合，不用 declarative base 减少一层概念


def sanitize_import_error(error: Exception | str) -> str:
    """保留可诊断的异常类型，同时移除连接串、凭据与令牌。"""
    message = str(error).replace("\r", " ").replace("\n", " ")
    message = re.sub(r"(?i)\b(?:authorization|password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*[^\s,;]+", "***", message)
    message = re.sub(r"(?i)\bbearer\s+[^\s,;]+", "Bearer ***", message)
    message = re.sub(r"//[^:/@\s]+:[^@/\s]+@", "//***:***@", message)
    message = re.sub(r"\beyJ[A-Za-z0-9._-]+", "***", message)
    message = re.sub(r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key|authorization)\b", "***", message)
    return f"{type(error).__name__}: {message[:240]}"


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


def upsert_subject(session: Session, data: dict, cover: "CoverResult | None" = None) -> int:
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
                "image": cover.display_url if cover else (data.get("images") or {}).get("large"),
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
                "image": cover.display_url if cover else (data.get("images") or {}).get("large"),
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
    today = now.date()
    for ep in episodes:
        bangumi_ep_id = ep["id"]
        existing_id = session.execute(
            text("SELECT id FROM episode WHERE subject_id = :sid AND bangumi_ep_id = :eid"),
            {"sid": subject_id, "eid": bangumi_ep_id},
        ).scalar()

        airdate = ep.get("airdate") or None  # empty string → NULL
        # ponytail: Bangumi API 有时返回中文日期格式
        if airdate:
            airdate = airdate.replace("年", "-").replace("月", "-").replace("日", "")
            airdate = airdate.replace(" ", "")

        # ponytail: airdate 推 status，不用 API 返回的值
        ep_status = "NA"
        if airdate:
            try:
                ep_date = datetime.strptime(airdate, "%Y-%m-%d").date()
                if ep_date < today:
                    ep_status = "Air"
                elif ep_date == today:
                    ep_status = "Today"
            except ValueError:
                airdate = None

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
                    "airdate": airdate,
                    "description": ep.get("desc", ""),
                    "status": ep_status,
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
                    "airdate": airdate,
                    "description": ep.get("desc", ""),
                    "status": ep_status,
                    "now": now,
                },
            )


def upsert_tags(session: Session, subject_id: int, tags: list[dict]):
    """upsert 标签。使用 (subject_id, name) 作为匹配键（表中有唯一索引）。"""
    # ponytail: 按 name 排序，让并发线程以相同顺序获取行锁，消除死锁环
    for tag in sorted(tags, key=lambda t: t.get("name", "")):
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


def upsert_relations(session: Session, subject_id: int, relations: list[dict]) -> bool:
    """验证全部关系目标后，再替换条目关联并双向写入。

    subject_id 为本地 PK。relations 中每个元素的 id 为 Bangumi API ID，
    需先解析为本地 subject.id 再写入，否则 FK 约束会失败。
    """
    resolved = []
    for rel in relations:
        bangumi_id = rel.get("id")
        relation_type = rel.get("relation", "")

        if not bangumi_id or not relation_type:
            continue

        # bangumi_id → 本地 subject.id
        local_id = session.execute(
            text("SELECT id FROM subject WHERE bangumi_id = :bid"),
            {"bid": bangumi_id},
        ).scalar()
        if not local_id:
            logger.warning("  -> 跳过关联条目 %d（bangumi_id），数据库中不存在（主条目 %d）", bangumi_id, subject_id)
            return False
        resolved.append((int(local_id), relation_type))

    # 只有所有可写关系均已解析才删除旧边，避免临时缺失造成图谱退化。
    session.execute(
        text("DELETE FROM subject_relation WHERE subject_id = :sid OR related_subject_id = :sid2"),
        {"sid": subject_id, "sid2": subject_id},
    )

    for local_id, relation_type in resolved:

        # 正向：subject_id → local_id
        session.execute(
            text("""
                INSERT INTO subject_relation (subject_id, related_subject_id, relation)
                VALUES (:sid, :rid, :rel)
                ON DUPLICATE KEY UPDATE relation = :rel2
            """),
            {"sid": subject_id, "rid": local_id, "rel": relation_type, "rel2": relation_type},
        )

        # 反向：local_id → subject_id（双向）
        inverse_rel = _inverse_relation(relation_type)
        session.execute(
            text("""
                INSERT INTO subject_relation (subject_id, related_subject_id, relation)
                VALUES (:sid, :rid, :rel)
                ON DUPLICATE KEY UPDATE relation = :rel2
            """),
            {"sid": local_id, "rid": subject_id, "rel": inverse_rel, "rel2": inverse_rel},
        )
    return True


def _inverse_relation(relation: str) -> str:
    """返回关联类型的反向关系。"""
    # Bangumi API 返回中文关系名，映射表必须用中文 key（英文 key 永远匹配不上）
    mapping = {
        "prequel": "sequel",
        "sequel": "prequel",
        "前传": "续集",
        "续集": "前传",
        "side_story": "parent_story",
        "parent_story": "side_story",
        "spin_off": "parent_story",
        "衍生": "主线故事",
        "主线故事": "衍生",
    }
    return mapping.get(relation, relation)


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


def acquire_import_lock(session: Session) -> None:
    """在 importer 主连接上取得 MySQL 单飞锁。"""
    locked = session.execute(text("SELECT GET_LOCK('animetracker:import', 0)")).scalar()
    if locked != 1:
        raise RuntimeError("已有导入任务正在运行，未获得 animetracker:import 锁")


def release_import_lock(session: Session) -> None:
    """释放当前主连接持有的 MySQL 单飞锁。"""
    session.execute(text("SELECT RELEASE_LOCK('animetracker:import')"))


def update_import_progress(
    session: Session,
    record_id: int,
    *,
    checkpoint_json: str,
    success: int = 0,
    failure: int = 0,
    skipped: int = 0,
) -> None:
    """每处理一项刷新断点、计数和心跳；调用方负责所属事务。"""
    session.execute(
        text(
            "UPDATE import_record SET checkpoint_json=CAST(:checkpoint_json AS JSON), "
            "scanned_count=GREATEST(scanned_count, :offset), success_count=success_count+:success, failure_count=failure_count+:failure, "
            "skipped_count=skipped_count+:skipped, heartbeat_at=:now WHERE id=:id"
        ),
        {
            "id": record_id,
            "checkpoint_json": checkpoint_json,
            "offset": json.loads(checkpoint_json)["offset"],
            "success": success,
            "failure": failure,
            "skipped": skipped,
            "now": datetime.now(),
        },
    )


def complete_import_record(session: Session, record_id: int, subject_count: int,
                           status: str = "COMPLETED", error_message: Exception | str | None = None):
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
            "error_message": sanitize_import_error(error_message) if error_message else None,
        },
    )


def fail_stale_running_records(session: Session, message: str = "导入进程提前退出"):
    """把未正常结束的 RUNNING 导入记录翻为 FAILED（进程硬退兜底）。"""
    session.execute(
        text("""
            UPDATE import_record
            SET status = 'FAILED', completed_at = :now, error_message = :message
            WHERE status = 'RUNNING'
              AND (heartbeat_at IS NULL OR heartbeat_at < DATE_SUB(:now, INTERVAL 10 MINUTE))
        """),
        {"now": datetime.now(), "message": sanitize_import_error(message)},
    )


def load_resume_record(session: Session, mode: str, season_key: Optional[str] = None):
    """读取最近一个可恢复记录；已完成记录绝不复用。"""
    row = session.execute(
        text(
            "SELECT id, checkpoint_json FROM import_record WHERE mode=:mode "
            "AND ((:season_key IS NULL AND season_key IS NULL) OR season_key=:season_key) "
            "AND status IN ('RUNNING', 'FAILED') AND checkpoint_json IS NOT NULL "
            "ORDER BY heartbeat_at DESC, id DESC LIMIT 1"
        ),
        {"mode": mode, "season_key": season_key},
    ).mappings().first()
    if row is None:
        return None
    checkpoint = row["checkpoint_json"]
    return int(row["id"]), (json.loads(checkpoint) if isinstance(checkpoint, str) else checkpoint)


def resume_import_record(session: Session, record_id: int) -> None:
    session.execute(
        text(
            "UPDATE import_record SET status='RUNNING', completed_at=NULL, error_message=NULL, "
            "heartbeat_at=:now WHERE id=:id"
        ),
        {"id": record_id, "now": datetime.now()},
    )
