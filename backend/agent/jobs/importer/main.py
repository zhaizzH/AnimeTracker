#!/usr/bin/env python3
"""Bangumi 数据导入器 CLI

Usage:
    python main.py --mode full
    python main.py --mode season --key 2026-summer
    python main.py --mode recent
    python main.py --mode since --since "2026-01-01"
    python main.py --mode season --key 2026-summer --workers 5
"""

import argparse
import hashlib
import json
from dataclasses import dataclass
import logging
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.shared.observability import log_event

try:
    from .client import BangumiClient
    from .db import get_engine, upsert_subject, upsert_episodes, upsert_tags, \
        upsert_relations, create_import_record, complete_import_record, acquire_import_lock, release_import_lock, update_import_progress, load_resume_record, resume_import_record, sanitize_import_error
    from .normalize import normalize_subject
    from .repository import ImportBundle, ImportCheckpoint, ImportRepository
    from .storage import ObjectStorage
except ImportError:
    from client import BangumiClient
    from db import get_engine, upsert_subject, upsert_episodes, upsert_tags, \
        upsert_relations, create_import_record, complete_import_record, acquire_import_lock, release_import_lock, update_import_progress, load_resume_record, resume_import_record, sanitize_import_error
    from normalize import normalize_subject
    from repository import ImportBundle, ImportCheckpoint, ImportRepository
    from storage import ObjectStorage

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SEASON_MONTHS = {
    "spring": (1, 3),
    "summer": (4, 6),
    "autumn": (7, 9),
    "winter": (10, 12),
}

MAX_WORKERS = 10
MAX_WORKERS_LIMIT = 10
SAMPLE_STRATA = (50, 100, 150, 200)
OUTCOME_SUCCESS = "success"
OUTCOME_SKIPPED = "skipped"
OUTCOME_FAILURE = "failure"

_progress_lock = threading.Lock()
_db_lock = threading.Lock()

# ponytail: 模块级单例，避免层层传递
_object_storage = None
_start_time = None
_done_count = 0  # 已处理成功条目数，后台线程周期刷到 import_record.subject_count

# import_runner 靠这个 PID 文件跨 worker 重启识别仍存活的导入子进程
PID_FILE = Path(__file__).with_name("importer.pid")


def _safe_progress(done: int, total: int | None = None):
    with _progress_lock:
        elapsed = time.time() - _start_time
        if total:
            pct = done * 100 // total
            logger.info("  进度: %d/%d (%d%%) [%s]", done, total, pct, _fmt_duration(elapsed))
        else:
            logger.info("  进度: %d 个条目已导入 [%s]", done, _fmt_duration(elapsed))


def _fmt_duration(secs: float) -> str:
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"


def _start_count_flusher(record_id: int, engine, every: float = 3.0):
    """后台守护线程：周期把已处理数刷到 import_record.subject_count。

    3s 刷新足够实时且写库次数有限（full 全程仅几十次）。
    返回 stop Event；导入结束先 set()+join() 再写最终值，避免与 complete 竞态。
    """
    stop = threading.Event()

    def _flush(db):
        n = _done_count
        try:
            db.execute(
                text("UPDATE import_record SET subject_count = :n WHERE id = :id"),
                {"n": n, "id": record_id},
            )
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning("刷新 import_record.subject_count 失败: %s", sanitize_import_error(e))

    def _loop():
        db = Session(engine)
        try:
            while not stop.wait(every):
                _flush(db)
        finally:
            db.close()

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return stop, thread


def _get_object_storage() -> ObjectStorage:
    global _object_storage
    if _object_storage is None:
        _object_storage = ObjectStorage()
    return _object_storage


def _import_worker(bangumi_id, resume, access_token, user_agent, engine):
    """Thread worker: 独立 Client + Session 导入单个条目。"""
    client = BangumiClient(access_token=access_token, user_agent=user_agent, request_delay=1.5)
    db = Session(engine)
    try:
        return import_single_subject(client, db, bangumi_id, resume)
    finally:
        db.close()


def _stagger(ids, workers):
    """按线程数交错重排任务，使并发线程起步点均匀分散在任务区间，降低同区段锁竞争导致的死锁。"""
    if workers <= 1 or len(ids) <= workers:
        return ids
    reordered = []
    for i in range(workers):
        reordered.extend(ids[i::workers])
    assert len(reordered) == len(ids) and len(set(reordered)) == len(ids), "stagger 重排必须是完整置换"
    return reordered


def _run_batch(bangumi_ids, resume, access_token, user_agent,
               host, port, user, password, db_name, max_workers=MAX_WORKERS, base_done=0,
               record_id=None, mode="", resume_checkpoint=None, track_progress=True):
    """并行导入一批 subject_id，返回成功数。

    base_done: 扫描阶段已发现条数，导入进度从该值继续累加（full 模式页面计数连续）。
    """
    global _done_count
    source_ids = list(bangumi_ids)
    if resume_checkpoint is not None:
        bangumi_ids = _resume_batch_ids(source_ids, resume_checkpoint)
    total = len(bangumi_ids)
    if not total:
        return 0
    engine = get_engine(host, port, user, password, db_name)
    scanned_ids_sha256 = _ids_sha256(source_ids)
    start_offset = resume_checkpoint.offset if resume_checkpoint else 0
    done = base_done
    ordered_ids = _stagger(bangumi_ids, max_workers)
    positions = {subject_id: index for index, subject_id in enumerate(source_ids)}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_import_worker, bid, resume, access_token, user_agent, engine): bid
            for bid in ordered_ids
        }
        completed_positions = set()
        confirmed_offset = start_offset
        for future in as_completed(futures):
            subject_id = futures[future]
            outcome = future.result()
            success = outcome == OUTCOME_SUCCESS
            skipped = outcome == OUTCOME_SKIPPED
            if success:
                done += 1
            if outcome != OUTCOME_FAILURE:
                completed_positions.add(positions[subject_id])
                while confirmed_offset in completed_positions:
                    confirmed_offset += 1
            if record_id is not None:
                progress_db = Session(engine)
                try:
                    last_subject_id = source_ids[confirmed_offset - 1] if confirmed_offset else None
                    checkpoint = ImportCheckpoint(mode, confirmed_offset, last_subject_id, scanned_ids_sha256)
                    update_import_progress(
                        progress_db,
                        record_id,
                        checkpoint_json=json.dumps(checkpoint.as_json()),
                        success=int(success),
                        failure=int(outcome == OUTCOME_FAILURE),
                        skipped=int(skipped),
                    )
                    progress_db.commit()
                finally:
                    progress_db.close()
            if track_progress:
                _done_count = done
            _safe_progress(done - base_done, total)
    return done - base_done


def _ids_sha256(ids) -> str:
    return hashlib.sha256(",".join(map(str, ids)).encode()).hexdigest()


def _resume_batch_ids(ids, checkpoint: ImportCheckpoint):
    if checkpoint.offset < 0 or checkpoint.offset > len(ids):
        raise ValueError("导入断点 offset 无效")
    if checkpoint.scanned_ids_sha256 != _ids_sha256(ids):
        raise ValueError("扫描结果已变化，拒绝使用旧断点")
    if checkpoint.offset and checkpoint.last_subject_id != ids[checkpoint.offset - 1]:
        raise ValueError("导入断点最后条目不匹配")
    return ids[checkpoint.offset:]


def _progress(done: int, total: int | None = None):
    elapsed = time.time() - _start_time
    if total:
        pct = done * 100 // total
        logger.info("  进度: %d/%d (%d%%) [%s]", done, total, pct, _fmt_duration(elapsed))
    else:
        logger.info("  进度: %d 个条目已导入 [%s]", done, _fmt_duration(elapsed))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bangumi data importer")
    parser.add_argument("--mode", required=True,
                        choices=["full", "season", "recent", "since", "sample"],
                        help="import mode")
    parser.add_argument("--key", help="season key, e.g. 2026-summer (required for season mode)")
    parser.add_argument("--since", help="start date, e.g. 2026-01-01 (required for since mode)")
    parser.add_argument("--resume", action="store_true",
                        help="skip already imported subjects")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help=f"number of import threads (default: {MAX_WORKERS}, max: {MAX_WORKERS_LIMIT})")
    parser.add_argument("--limit", type=int,
                        help="maximum items for full/sample mode; full defaults to no limit")
    parser.add_argument("--dry-run", action="store_true",
                        help="scan only; never open the database or write remote storage")
    return parser.parse_args(argv)


@dataclass(frozen=True)
class ImportSummary:
    processed: int
    distribution: dict[str, int]


def _sample_bucket(date: str) -> int:
    year = int(date[:4]) if len(date) >= 4 and date[:4].isdigit() else 2020
    if year < 1990:
        return 0
    if year < 2010:
        return 1
    if year < 2020:
        return 2
    return 3


def _sample_ids(items, *, limit: int = 500, strata: tuple[int, int, int, int] = SAMPLE_STRATA):
    """在内存中挑选样本；不足配额按最近年代层补齐。"""
    if limit < 1 or len(strata) != 4 or any(value < 0 for value in strata):
        raise ValueError("sample limit and strata must be positive")
    buckets = [[] for _ in strata]
    for subject_id, date in items:
        if subject_id:
            buckets[_sample_bucket(date or "")].append(subject_id)
    wanted = list(strata)
    if sum(wanted) > limit:
        remaining = limit
        wanted = [min(value, remaining) for value in wanted]
        remaining -= sum(wanted)
    chosen = [bucket[:wanted[index]] for index, bucket in enumerate(buckets)]
    deficit = min(limit, sum(len(bucket) for bucket in buckets)) - sum(map(len, chosen))
    while deficit:
        progress = False
        for target in range(4):
            if deficit == 0:
                break
            for distance in range(1, 4):
                candidates = (target - distance, target + distance)
                for source in candidates:
                    if 0 <= source < 4 and len(chosen[source]) < len(buckets[source]):
                        chosen[source].append(buckets[source][len(chosen[source])])
                        deficit -= 1
                        progress = True
                        break
                if progress or deficit == 0:
                    break
        if not progress:
            break
    selected_set = {subject_id for bucket in chosen for subject_id in bucket}
    selected = [subject_id for subject_id, _ in items if subject_id in selected_set]
    labels = ("before_1990", "1990_2009", "2010_2019", "2020_plus")
    return selected, dict(zip(labels, map(len, chosen)))


def run_sample(client, db, resume=False, *, limit: int = 500, strata: tuple[int, int, int, int] = SAMPLE_STRATA, **kw) -> ImportSummary:
    """仅供样本门禁；不影响 full 的扫描与导入顺序。"""
    offset = 0
    items = []
    while True:
        page = client.browse_subjects(type=2, offset=offset, limit=100)
        page_items = page.get("data") or []
        items.extend((entry.get("id"), entry.get("date") or "") for entry in page_items)
        offset += len(page_items)
        if not page_items or offset >= int(page.get("total") or 0):
            break
    ids, distribution = _sample_ids(items, limit=limit, strata=strata)
    return ImportSummary(_run_batch(ids, resume, **kw), distribution)


def parse_season_key(key: str):
    parts = key.split("-")
    if len(parts) != 2:
        raise ValueError(f"invalid season key: {key}")
    year = int(parts[0])
    season = parts[1].lower()
    if season not in SEASON_MONTHS:
        raise ValueError(f"invalid season: {season}")
    ms, me = SEASON_MONTHS[season]
    return year, ms, me


def _fetch_related(client, bangumi_id):
    """网络预取关联条目（subject + 封面 + 剧集），不写库；nsfw 返回 None。"""
    data = client.get_subject(bangumi_id)
    if data.get("type") != 2 or data.get("nsfw"):
        return None

    storage = _get_object_storage()
    storage.put_raw_subject(data["id"], data)
    cover = storage.put_cover(data["id"], (data.get("images") or {}).get("large") or "")

    episodes = []
    total_eps = data.get("eps") or data.get("total_episodes") or 0
    if total_eps > 0:
        episodes = client.get_all_episodes(bangumi_id)

    return {"data": data, "cover": cover, "episodes": episodes}


def _write_related(db, pkg):
    """把预取的关联条目写入 DB（仅在 _db_lock 内调用）。"""
    data = pkg["data"]
    subject_id = upsert_subject(db, data, pkg["cover"])

    tags = data.get("tags") or []
    if tags:
        upsert_tags(db, subject_id, tags)

    if pkg["episodes"]:
        upsert_episodes(db, subject_id, pkg["episodes"])


def import_single_subject(client, db, bangumi_id, resume):
    """预取公开资料后，将单条目交给仓储层原子写入。"""
    for _retry in range(5):
        try:
            if resume:
                existing = db.execute(
                    text("SELECT id FROM subject WHERE bangumi_id = :bid AND import_status = 1"),
                    {"bid": bangumi_id},
                ).scalar()
                if existing:
                    logger.info("  -> 跳过已导入条目 %d", bangumi_id)
                    return OUTCOME_SKIPPED
                db.rollback()  # 让 write_bundle 自己建立唯一的写事务

            logger.info("  -> 获取条目 %d", bangumi_id)
            data = client.get_subject(bangumi_id)

            if data.get("type") != 2 or data.get("nsfw"):
                logger.info("  -> 跳过非公开动画条目 %d", bangumi_id)
                return OUTCOME_SKIPPED

            storage = _get_object_storage()
            storage.put_raw_subject(data["id"], data)
            cover = storage.put_cover(data["id"], (data.get("images") or {}).get("large") or "")

            persons = client.get_subject_persons(bangumi_id)
            normalized = normalize_subject(data, persons)
            if normalized is None:
                logger.info("  -> 跳过非公开动画条目 %d", bangumi_id)
                return OUTCOME_SKIPPED

            episodes = []
            total_eps = data.get("eps") or data.get("total_episodes") or 0
            if total_eps > 0:
                logger.info("  -> 获取剧集 subject %d（共 %d 集）", bangumi_id, total_eps)
                episodes = client.get_all_episodes(bangumi_id)

            # 关联条目只保留动画关系；仓储层按本地自然键写入已存在的关联目标。
            anime_relations = []
            try:
                relations = client.get_relations(bangumi_id)
                if relations:
                    for relation in relations:
                        relation_id = relation.get("id")
                        if not isinstance(relation_id, int):
                            continue
                        try:
                            target = client.get_subject(relation_id)
                        except Exception as e:
                            logger.warning("  -> 关联目标校验失败 subject %d -> %d: %s", bangumi_id, relation_id, sanitize_import_error(e))
                            continue
                        if target.get("type") == 2 and target.get("nsfw") is False:
                            anime_relations.append(relation)
            except Exception as e:
                logger.warning("  -> 关联条目导入失败 subject %d: %s", bangumi_id, sanitize_import_error(e))

            # 每个主条目及其索引任务均由 repository 的同一事务提交。
            with _db_lock:
                ImportRepository(db).write_bundle(
                    ImportBundle(normalized, cover, tuple(episodes), tuple(anime_relations)),
                    os.getenv("RAG_INDEX_VERSION", "v1"),
                )
            return OUTCOME_SUCCESS

        except Exception as e:
            db.rollback()
            if "Deadlock" in sanitize_import_error(e) and _retry < 4:
                delay = random.uniform(0.3, 1.0) * (_retry + 1)
                logger.warning("  -> subject %d 死锁，重试 (%d/4) delay=%.1fs", bangumi_id, _retry + 1, delay)
                time.sleep(delay)
                time.sleep(0.5 * (_retry + 1))
                continue
            logger.error("  x subject %d 导入失败: %s", bangumi_id, sanitize_import_error(e))
            return OUTCOME_FAILURE


def _full_catalog_ids(client, limit: int | None = None) -> list[int]:
    """读取 type=2 全目录，保持首次出现顺序并限制实际导入数。"""
    ids = []
    seen = set()
    for subject_id in client.iter_subject_ids(2, limit=100):
        if subject_id in seen:
            continue
        seen.add(subject_id)
        ids.append(subject_id)
        if limit is not None and len(ids) >= limit:
            break
    return ids


def run_full(client, db, resume, *, limit: int | None = None, **kw):
    global _done_count
    ids = _full_catalog_ids(client, limit)
    _done_count = len(ids)
    imported = _run_batch(ids, resume, base_done=len(ids), **kw)
    # full 的断点只描述完整目录；追赶批次不覆盖它，也不复用它。
    catchup_kw = dict(kw)
    catchup_kw.pop("record_id", None)
    catchup_kw.pop("mode", None)
    catchup_kw.pop("resume_checkpoint", None)
    catchup_kw["track_progress"] = False
    return imported + run_recent(client, db, resume, **catchup_kw)


def run_season(client, db, key, resume, **kw):
    year, ms, me = parse_season_key(key)
    ids = []
    for month in range(ms, me + 1):
        logger.info("扫描 %d-%d...", year, month)
        offset = 0
        while True:
            try:
                result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
            except Exception as e:
                logger.error("扫描 %d-%d 失败: %s", year, month, sanitize_import_error(e))
                break
            items = result.get("data") or []
            if not items:
                break
            ids.extend(item["id"] for item in items if item.get("id"))
            total_count = result.get("total", 0)
            offset += len(items)
            if offset >= total_count:
                break
    return _run_batch(ids, resume, **kw)


def run_recent(client, db, resume, **kw):
    logger.info("获取日历...")
    try:
        calendar = client.get_calendar()
    except Exception as e:
        logger.error("日历获取失败: %s", sanitize_import_error(e))
        return 0
    seen = set()
    ids = []
    for day in calendar:
        for item in day.get("items") or []:
            bid = item.get("id")
            if bid and bid not in seen:
                seen.add(bid)
                ids.append(bid)
    return _run_batch(ids, resume, **kw)


def run_since(client, db, since_date, resume, **kw):
    since = datetime.strptime(since_date, "%Y-%m-%d")
    now = datetime.now()
    ids = []
    for year in range(since.year, now.year + 1):
        start_month = since.month if year == since.year else 1
        end_month = now.month if year == now.year else 12
        for month in range(start_month, end_month + 1):
            logger.info("扫描 %d-%d...", year, month)
            offset = 0
            while True:
                try:
                    result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
                except Exception as e:
                    logger.error("扫描 %d-%d 失败: %s", year, month, sanitize_import_error(e))
                    break
                items = result.get("data") or []
                if not items:
                    break
                for item in items:
                    bid = item.get("id")
                    item_date = item.get("date") or ""
                    if bid and item_date >= since_date:
                        ids.append(bid)
                total_count = result.get("total", 0)
                offset += len(items)
                if offset >= total_count:
                    break
    return _run_batch(ids, resume, **kw)


def _dry_run_full(client, limit: int | None) -> int:
    ids = _full_catalog_ids(client, limit)
    logger.info("dry-run full：预计导入 %d 个条目；只读取 Bangumi 目录，不创建 import_record，也不写 MySQL/MinIO/Redis", len(ids))
    return 0


def main(argv=None):
    args = parse_args(argv)

    load_dotenv()
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "anime_tracker")
    access_token = os.getenv("BANGUMI_ACCESS_TOKEN", "")
    user_agent = os.getenv("BANGUMI_USER_AGENT", "zhaizzH/AnimeTracker")

    client = BangumiClient(access_token=access_token, user_agent=user_agent)
    if args.dry_run:
        if args.mode != "full":
            raise ValueError("dry-run currently supports full mode only")
        return _dry_run_full(client, args.limit)
    engine = get_engine(db_host, db_port, db_user, db_password, db_name)
    # 保持主连接在整个导入期间被检出，MySQL GET_LOCK 不会在 commit 后漂移到连接池。
    main_connection = engine.connect()
    db = Session(bind=main_connection)

    # 线程池共享参数
    pool_kw = dict(
        access_token=access_token, user_agent=user_agent,
        host=db_host, port=db_port, user=db_user, password=db_password, db_name=db_name,
        max_workers=min(args.workers, MAX_WORKERS_LIMIT),
    )

    global _start_time
    _start_time = time.time()
    record_id = None
    stop_flusher = flusher_thread = None
    lock_acquired = False
    resume_checkpoint = None
    try:
        acquire_import_lock(db)
        lock_acquired = True
        PID_FILE.write_text(str(os.getpid()))
        if args.resume:
            saved = load_resume_record(db, args.mode, getattr(args, "key", None))
            if saved is not None:
                record_id, checkpoint_json = saved
                resume_checkpoint = ImportCheckpoint.from_json(checkpoint_json)
                if resume_checkpoint.mode != args.mode:
                    raise ValueError("导入断点模式不匹配")
                resume_import_record(db, record_id)
        if record_id is None:
            record_id = create_import_record(db, args.mode, getattr(args, "key", None))
            ImportRepository(db).save_checkpoint(
                record_id,
                ImportCheckpoint(args.mode, 0, None, hashlib.sha256(b"").hexdigest()),
            )
        db.commit()
        stop_flusher, flusher_thread = _start_count_flusher(record_id, engine)
        pool_kw.update(record_id=record_id, mode=args.mode, resume_checkpoint=resume_checkpoint)

        logger.info("Bangumi 数据导入模式: %s", args.mode)
        if args.mode == "full":
            count = run_full(client, db, args.resume, limit=args.limit, **pool_kw)
        elif args.mode == "season":
            if not args.key:
                raise ValueError("season mode needs --key")
            count = run_season(client, db, args.key, args.resume, **pool_kw)
        elif args.mode == "recent":
            count = run_recent(client, db, args.resume, **pool_kw)
        elif args.mode == "since":
            if not args.since:
                raise ValueError("since mode needs --since")
            count = run_since(client, db, args.since, args.resume, **pool_kw)
        elif args.mode == "sample":
            summary = run_sample(client, db, args.resume, limit=args.limit or 500, **pool_kw)
            count = summary.processed
            logger.info("样本实际分布: %s", summary.distribution)
        else:
            raise ValueError(f"Unknown mode: {args.mode}")

        stop_flusher.set()
        flusher_thread.join(timeout=5)
        stop_flusher = flusher_thread = None
        complete_import_record(db, record_id, count, "COMPLETED")
        db.commit()
        elapsed = _fmt_duration(time.time() - _start_time)
        logger.info("")
        logger.info("=" * 60)
        logger.info("  导入完成！共 %d 个条目", count)
        logger.info("  耗时: %s", elapsed)
        logger.info("=" * 60)
        logger.info("")

    except Exception as e:
        elapsed = _fmt_duration(time.time() - _start_time)
        sanitized = sanitize_import_error(e)
        logger.error("导入异常终止（耗时 %s）: %s", elapsed, sanitized)
        if record_id is not None:
            complete_import_record(db, record_id, 0, "FAILED", sanitized)
            db.commit()
        log_event("rag.import.completed", jobId=record_id, success=False, errorType=type(e).__name__)
        return 1
    finally:
        if stop_flusher is not None:
            stop_flusher.set()
            flusher_thread.join(timeout=5)
        PID_FILE.unlink(missing_ok=True)
        if lock_acquired:
            release_import_lock(db)
        db.close()
        main_connection.close()
    log_event("rag.import.completed", jobId=record_id, candidateCount=count, success=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
