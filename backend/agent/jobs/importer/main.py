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
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.adapters.mysql.import_records import get_engine, sanitize_import_error
from app.adapters.redis.import_lock import (
    acquire as acquire_import_lock,
    release as release_import_lock,
    renew as renew_import_lock,
)
from app.rag.seasons import SEASON_QUARTERS, season_month_range
from app.shared.observability import log_event

try:
    from .client import BangumiClient
    from .db import upsert_subject, upsert_episodes, upsert_tags, \
        upsert_relations, create_import_record, complete_import_record, update_import_progress, load_resume_record, resume_import_record
    from .normalize import normalize_subject
    from .repository import ImportBundle, ImportCheckpoint, ImportRepository
    from .storage import ObjectStorage
except ImportError:
    from client import BangumiClient
    from db import upsert_subject, upsert_episodes, upsert_tags, \
        upsert_relations, create_import_record, complete_import_record, update_import_progress, load_resume_record, resume_import_record
    from normalize import normalize_subject
    from repository import ImportBundle, ImportCheckpoint, ImportRepository
    from storage import ObjectStorage

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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

# Redis 客户端单例：导入锁 + 进度计数器共用（连接获取同 R4）
_redis_client = None

# import_record.subject_count 的 Redis 中间计数键；导入终态读出后删除
_PROGRESS_KEY_TEMPLATE = "animetracker:import:{record_id}:done"


def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
    return _redis_client


def _progress_key(record_id: int) -> str:
    return _PROGRESS_KEY_TEMPLATE.format(record_id=record_id)


def _incr_done(record_id: int) -> None:
    """成功导入一条即 INCR 一次；Redis 故障只告警，不影响导入主流程。"""
    try:
        _get_redis().incr(_progress_key(record_id))
    except Exception as e:
        logger.warning("Redis 导入进度计数失败: %s", sanitize_import_error(e))


def _clear_done(record_id: int) -> None:
    try:
        _get_redis().delete(_progress_key(record_id))
    except Exception as e:
        logger.warning("清理 Redis 导入进度计数失败: %s", sanitize_import_error(e))


def _read_and_clear_done(record_id: int) -> int | None:
    """读出累计成功数并删除计数键。

    读取异常时返回 None（而非 0）——调用方需回退到本次运行的内存计数，
    否则一次成功的导入会被静默记成 `subject_count=0`。
    """
    key = _progress_key(record_id)
    count: int | None = None
    try:
        raw = _get_redis().get(key)
        count = int(raw) if raw else 0
    except Exception as e:
        logger.warning("读取 Redis 导入进度计数失败: %s", sanitize_import_error(e))
    _clear_done(record_id)
    return count


def _start_lock_renewer(token: str, every: float = 600.0):
    """后台守护线程：每 600s 校验 token 并 PEXPIRE 续期；token 丢失即停止。"""
    stop = threading.Event()

    def _loop():
        while not stop.wait(every):
            try:
                if not renew_import_lock(_get_redis(), token):
                    logger.error("导入锁续期失败（token 已不持有），停止续期")
                    return
            except Exception as e:
                logger.warning("导入锁续期异常: %s", sanitize_import_error(e))

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return stop, thread

# jobs/importer launcher 靠这个 PID 文件跨 worker 重启识别仍存活的导入子进程
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


def _get_object_storage() -> ObjectStorage:
    global _object_storage
    if _object_storage is None:
        _object_storage = ObjectStorage()
    return _object_storage


def _import_worker(bangumi_id, resume, access_token, user_agent, engine, import_record_id=None):
    """Thread worker: 独立 Client + Session 导入单个条目。"""
    client = BangumiClient(access_token=access_token, user_agent=user_agent, request_delay=1.5)
    db = Session(engine)
    try:
        return import_single_subject(
            client, db, bangumi_id, resume, import_record_id=import_record_id
        )
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
               record_id=None, mode="", resume_checkpoint=None,
               entity_import_record_id=None):
    """并行导入一批 subject_id，返回成功数。

    base_done: 扫描阶段已发现条数，导入进度从该值继续累加（full 模式页面计数连续）。
    """
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
    worker_import_record_id = record_id if entity_import_record_id is None else entity_import_record_id
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _import_worker, bid, resume, access_token, user_agent, engine, worker_import_record_id
            ): bid
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
                if worker_import_record_id is not None:
                    _incr_done(worker_import_record_id)
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
    parser = argparse.ArgumentParser(description="Bangumi 数据导入器")
    parser.add_argument("--mode", required=True,
                        choices=["full", "season", "recent", "since", "sample"],
                        help="导入模式")
    parser.add_argument("--key", help="season key，例如 2026-summer（season 模式必填）")
    parser.add_argument("--since", help="起始日期，例如 2026-01-01（since 模式必填）")
    parser.add_argument("--resume", action="store_true",
                        help="跳过已导入的条目")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help=f"导入线程数（默认: {MAX_WORKERS}，上限: {MAX_WORKERS_LIMIT}）")
    parser.add_argument("--limit", type=int,
                        help="full/sample 模式的最大条目数；full 默认不限")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅扫描；不打开数据库，也不写远端存储")
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
        raise ValueError("采样 limit 与 strata 必须为正数")
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
        raise ValueError(f"无效的 season key: {key}")
    year = int(parts[0])
    season = parts[1].lower()
    if season not in SEASON_QUARTERS:
        raise ValueError(f"无效的 season: {season}")
    ms, me = season_month_range(season)
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


def import_single_subject(client, db, bangumi_id, resume, *, import_record_id=None):
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

            # 关联集合是相互独立的 API 调用。某次调用失败不得阻止核心 Subject 刷新，
            # 但其旧集合必须保持活动（仓储会收到完整性标记，
            # 并因此不对其执行 replace-set）。
            persons_complete = True
            try:
                persons = client.get_subject_persons(bangumi_id)
                if not isinstance(persons, list):
                    raise ValueError("persons 响应必须是列表")
                _validate_summary_items(persons, "persons")
            except Exception as e:
                persons = []
                persons_complete = False
                logger.warning("  -> 人物列表获取失败 subject %d，保留旧关系: %s", bangumi_id, sanitize_import_error(e))

            characters_complete = True
            try:
                characters = client.get_subject_characters(bangumi_id)
                if not isinstance(characters, list):
                    raise ValueError("characters 响应必须是列表")
                _validate_summary_items(characters, "characters")
            except Exception as e:
                characters = []
                characters_complete = False
                logger.warning("  -> 角色列表获取失败 subject %d，保留旧关系: %s", bangumi_id, sanitize_import_error(e))

            normalized = normalize_subject(data, persons, characters)
            if normalized is None:
                logger.info("  -> 跳过非公开动画条目 %d", bangumi_id)
                return OUTCOME_SKIPPED

            episodes = []
            # 显式 0 表示"完整来源集为空"。若两个计数字段都缺失，
            # 则该载荷是部分数据，必须保留旧的剧集记录。
            episode_count_present = any(
                _is_non_negative_int(data.get(field)) for field in ("eps", "total_episodes")
            )
            episodes_complete = episode_count_present
            total_eps = max(
                _non_negative_int(data.get("eps")),
                _non_negative_int(data.get("total_episodes")),
            )
            if total_eps > 0:
                logger.info("  -> 获取剧集 subject %d（共 %d 集）", bangumi_id, total_eps)
                try:
                    episodes = client.get_all_episodes(bangumi_id)
                    if not isinstance(episodes, list):
                        raise ValueError("episodes 响应必须是列表")
                except Exception as e:
                    episodes_complete = False
                    logger.warning("  -> 剧集列表获取失败 subject %d，保留旧剧集: %s", bangumi_id, sanitize_import_error(e))

            # 关联条目只保留动画关系；仓储层按本地自然键写入已存在的关联目标。
            anime_relations = []
            relations_complete = True
            try:
                relations = client.get_relations(bangumi_id)
                if not isinstance(relations, list):
                    raise ValueError("relations 响应必须是列表")
                _validate_relation_items(relations)
                if relations:
                    for relation in relations:
                        relation_id = relation.get("id")
                        try:
                            target = client.get_subject(relation_id)
                        except Exception as e:
                            logger.warning("  -> 关联目标校验失败 subject %d -> %d: %s", bangumi_id, relation_id, sanitize_import_error(e))
                            relations_complete = False
                            continue
                        if (
                            not isinstance(target, dict)
                            or not isinstance(target.get("type"), int)
                            or isinstance(target.get("type"), bool)
                            or not isinstance(target.get("nsfw"), bool)
                        ):
                            logger.warning("  -> 关联目标响应不完整 subject %d -> %d，保留旧关系", bangumi_id, relation_id)
                            relations_complete = False
                            continue
                        if target.get("type") == 2 and target.get("nsfw") is False:
                            anime_relations.append(relation)
            except Exception as e:
                logger.warning("  -> 关联条目导入失败 subject %d: %s", bangumi_id, sanitize_import_error(e))
                relations_complete = False

            # 每个主条目及其索引任务均由 repository 的同一事务提交。
            with _db_lock:
                ImportRepository(db).write_bundle(
                    ImportBundle(
                        normalized,
                        cover,
                        tuple(episodes),
                        tuple(anime_relations),
                        persons=normalized.persons,
                        characters=normalized.characters,
                        # 字段存在但为 null 表示来源响应不完整，
                        # 而非权威的空集合。
                        aliases_complete=isinstance(data.get("infobox"), list),
                        tags_complete=isinstance(data.get("tags"), list),
                        meta_tags_complete=isinstance(data.get("meta_tags"), list),
                        persons_complete=persons_complete,
                        characters_complete=characters_complete,
                        episodes_complete=episodes_complete,
                        relations_complete=relations_complete,
                        import_record_id=import_record_id,
                    ),
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
    ids = _full_catalog_ids(client, limit)
    imported = _run_batch(ids, resume, base_done=len(ids), **kw)
    # full 的断点只描述完整目录；追赶批次不覆盖它，也不复用它。
    catchup_kw = dict(kw)
    catchup_kw.pop("record_id", None)
    catchup_kw.pop("mode", None)
    catchup_kw.pop("resume_checkpoint", None)
    # 补跑批次出于实体血缘归属同一条导入记录，
    # 但不得覆盖全量目录的检查点/进度计数。
    catchup_kw["entity_import_record_id"] = kw.get("record_id")
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
        # 日历是 recent 模式的扫描来源；失败时不能把“未扫描到条目”
        # 当作成功，否则 main() 会将 import_record 错误标记为 COMPLETED，
        # 也会阻断基于 checkpoint/success_count 的 --resume。
        raise RuntimeError("日历获取失败") from e
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
            raise ValueError("dry-run 目前仅支持 full 模式")
        return _dry_run_full(client, args.limit)
    engine = get_engine(db_host, db_port, db_user, db_password, db_name)
    # 主连接仍用于 import_record 读写；导入锁已迁到 Redis，不再依赖连接被持续检出。
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
    lock_token = f"{os.getpid()}:{time.time()}"
    lock_acquired = False
    stop_renewer = renewer_thread = None
    resume_checkpoint = None
    try:
        if not acquire_import_lock(_get_redis(), lock_token):
            raise RuntimeError("已有导入任务正在运行，未获得 animetracker:import:lock 锁")
        lock_acquired = True
        stop_renewer, renewer_thread = _start_lock_renewer(lock_token)
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
        # 计数键无 TTL，只在 finally 删除；被 SIGKILL 会残留。--resume 复用同一
        # record_id，残留值会被叠加进终态 subject_count。此处已持有导入锁（无其他
        # importer 在跑），任何既存值都是残留，清零后再开始计数。
        _clear_done(record_id)
        db.commit()
        pool_kw.update(record_id=record_id, mode=args.mode, resume_checkpoint=resume_checkpoint)

        logger.info("Bangumi 数据导入模式: %s", args.mode)
        if args.mode == "full":
            count = run_full(client, db, args.resume, limit=args.limit, **pool_kw)
        elif args.mode == "season":
            if not args.key:
                raise ValueError("season 模式需要 --key")
            count = run_season(client, db, args.key, args.resume, **pool_kw)
        elif args.mode == "recent":
            count = run_recent(client, db, args.resume, **pool_kw)
        elif args.mode == "since":
            if not args.since:
                raise ValueError("since 模式需要 --since")
            count = run_since(client, db, args.since, args.resume, **pool_kw)
        elif args.mode == "sample":
            summary = run_sample(client, db, args.resume, limit=args.limit or 500, **pool_kw)
            count = summary.processed
            logger.info("样本实际分布: %s", summary.distribution)
        else:
            raise ValueError(f"未知模式: {args.mode}")

        # 终态以 Redis 累计成功数为准（含 full 追赶批次），读出后立即删键。
        # Redis 不可用时回退到本次运行的内存计数：run_full 返回
        # `主批次 + 追赶批次`，与 Redis 计数语义一致。
        redis_count = _read_and_clear_done(record_id)
        if redis_count is None:
            logger.warning("Redis 进度计数不可用，subject_count 回退为本次运行计数 %d", count)
        else:
            count = redis_count
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
        if stop_renewer is not None:
            stop_renewer.set()
            renewer_thread.join(timeout=5)
        PID_FILE.unlink(missing_ok=True)
        if lock_acquired:
            try:
                release_import_lock(_get_redis(), lock_token)
            except Exception as e:
                logger.warning("释放导入锁失败: %s", sanitize_import_error(e))
        if record_id is not None:
            _clear_done(record_id)
        db.close()
        main_connection.close()
    log_event("rag.import.completed", jobId=record_id, candidateCount=count, success=True)
    return 0


def _validate_summary_items(items: list[object], kind: str) -> None:
    """在任何 replace-set 执行前拒绝格式错误的成功响应。"""
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"{kind} 响应包含无效的摘要")
        # v0 的 RelatedPerson 载荷是带顶层 ``relation`` 字段的裸 Person 对象。
        # 同时兼容更旧的嵌套结构；若拒绝文档化的裸结构，
        # 所有合法的 persons 响应都会被判定为不完整，陈旧演职员信息将永远保留。
        nested_person = item.get("person") if kind == "persons" else None
        entity = nested_person if isinstance(nested_person, dict) else item
        if (
            not isinstance(entity, dict)
            or not isinstance(entity.get("id"), int)
            or isinstance(entity.get("id"), bool)
            or entity.get("id") <= 0
            or not isinstance(entity.get("name"), str)
            or not entity.get("name", "").strip()
        ):
            raise ValueError(f"{kind} 响应包含无效的摘要")
        if kind == "persons" and (
            not isinstance(item.get("relation"), str) or not item.get("relation", "").strip()
        ):
            raise ValueError("persons 响应包含无效的关系")
        if kind != "characters":
            continue
        if not isinstance(item.get("relation"), str) or not item.get("relation", "").strip():
            raise ValueError("characters 响应包含无效的关系")
        actors = item.get("actors") or []
        if not isinstance(actors, list):
            raise ValueError("characters.actors 响应必须是列表")
        for actor in actors:
            if (
                not isinstance(actor, dict)
                or not isinstance(actor.get("id"), int)
                or isinstance(actor.get("id"), bool)
                or actor.get("id") <= 0
                or not isinstance(actor.get("name"), str)
                or not actor.get("name", "").strip()
            ):
                raise ValueError("characters 响应包含无效的演员摘要")


def _validate_relation_items(items: list[object]) -> None:
    """在 replace-set 删除旧边之前拒绝格式错误的关系载荷。"""
    for item in items:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), int)
            or isinstance(item.get("id"), bool)
            or item.get("id") <= 0
            or not isinstance(item.get("relation"), str)
            or not item.get("relation", "").strip()
        ):
            raise ValueError("relations 响应包含无效的关系")


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _non_negative_int(value: object) -> int:
    return value if _is_non_negative_int(value) else 0


if __name__ == "__main__":
    raise SystemExit(main())
