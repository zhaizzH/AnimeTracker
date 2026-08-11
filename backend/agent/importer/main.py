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
import logging
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from minio import Minio
from sqlalchemy import text
from sqlalchemy.orm import Session

from client import BangumiClient
from db import get_engine, upsert_subject, upsert_episodes, upsert_tags, \
    upsert_relations, create_import_record, complete_import_record

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

_progress_lock = threading.Lock()
_db_lock = threading.Lock()

# ponytail: 模块级单例，避免层层传递
_minio_client = None
_start_time = None
_done_count = 0  # 已处理成功条目数，后台线程周期刷到 import_record.subject_count

EXT_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

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
            logger.warning("刷新 import_record.subject_count 失败: %s", e)

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


def _minio_secure() -> bool:
    return os.getenv("MINIO_SECURE", "false").lower() == "true"


def _get_minio_client():
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=_minio_secure(),
        )
    return _minio_client


def _get_ext_from_url(url: str) -> str | None:
    path = urlparse(url).path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        if path.endswith(ext):
            return ext.lstrip(".")
    return None


def upload_cover(subject_id: int, image_url: str) -> str:
    """下载封面 → 上传 MinIO → 返回 MinIO 公开 URL；失败重试 2 次后回退。"""
    if not image_url:
        return image_url
    proxy = os.getenv("BANGUMI_IMAGE_PROXY_URL", "").rstrip("/")
    if proxy:
        image_url = f"{proxy}/{image_url}"
    for attempt in range(3):
        try:
            resp = requests.get(image_url, timeout=15, stream=True)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            ext = EXT_MAP.get(content_type) or _get_ext_from_url(image_url) or "jpg"
            object_name = f"covers/{subject_id}.{ext}"

            mc = _get_minio_client()
            bucket = os.getenv("MINIO_BUCKET", "anime-tracker")
            if not mc.bucket_exists(bucket):
                mc.make_bucket(bucket)

            mc.put_object(bucket, object_name, resp.raw, length=-1, part_size=10 * 1024 * 1024,
                          content_type=content_type or "image/jpeg")
            scheme = "https" if _minio_secure() else "http"
            public_url = f"{scheme}://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}".rstrip("/")
            return f"{public_url}/{bucket}/{object_name}"
        except Exception as e:
            if attempt < 2:
                logger.warning("  封面上传失败 subject %d（第 %d 次重试）: %s", subject_id, attempt + 1, e)
            else:
                logger.warning("  封面上传失败 subject %d（已重试 2 次），回退到原始 URL: %s", subject_id, e)
    return image_url


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
               host, port, user, password, db_name, max_workers=MAX_WORKERS, base_done=0):
    """并行导入一批 subject_id，返回成功数。

    base_done: 扫描阶段已发现条数，导入进度从该值继续累加（full 模式页面计数连续）。
    """
    global _done_count
    total = len(bangumi_ids)
    if not total:
        return 0
    engine = get_engine(host, port, user, password, db_name)
    done = base_done
    ordered_ids = _stagger(bangumi_ids, max_workers)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_import_worker, bid, resume, access_token, user_agent, engine): bid
            for bid in ordered_ids
        }
        for future in as_completed(futures):
            if future.result():
                done += 1
            _done_count = done
            _safe_progress(done - base_done, total)
    return done - base_done


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
                        choices=["full", "season", "recent", "since"],
                        help="import mode")
    parser.add_argument("--key", help="season key, e.g. 2026-summer (required for season mode)")
    parser.add_argument("--since", help="start date, e.g. 2026-01-01 (required for since mode)")
    parser.add_argument("--resume", action="store_true",
                        help="skip already imported subjects")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help=f"number of import threads (default: {MAX_WORKERS}, max: {MAX_WORKERS_LIMIT})")
    return parser.parse_args(argv)


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
    if data.get("nsfw"):
        return None

    raw_image = (data.get("images") or {}).get("large")
    if raw_image:
        minio_url = upload_cover(data["id"], raw_image)
        if minio_url != raw_image:
            data.setdefault("images", {})["large"] = minio_url

    episodes = []
    total_eps = data.get("eps") or data.get("total_episodes") or 0
    if total_eps > 0:
        eps_data = client.get_episodes(bangumi_id)
        episodes = eps_data.get("data") or []

    return {"data": data, "episodes": episodes}


def _write_related(db, pkg):
    """把预取的关联条目写入 DB（仅在 _db_lock 内调用）。"""
    data = pkg["data"]
    subject_id = upsert_subject(db, data)

    tags = data.get("tags") or []
    if tags:
        upsert_tags(db, subject_id, tags)

    if pkg["episodes"]:
        upsert_episodes(db, subject_id, pkg["episodes"])


def import_single_subject(client, db, bangumi_id, resume):
    """网络请求（锁外并行）与 DB 写（锁内串行）分离。

    并发事务各自拿到多把行/间隙锁再互相等待，是死锁环的成因；全局锁保证
    同一时刻只有一个事务在写库，从结构上消除死锁。网络是耗时大头，不受影响。
    """
    for _retry in range(5):
        try:
            if resume:
                existing = db.execute(
                    "SELECT id FROM subject WHERE bangumi_id = :bid AND import_status = 1",
                    {"bid": bangumi_id},
                ).scalar()
                if existing:
                    logger.info("  -> 跳过已导入条目 %d", bangumi_id)
                    return True

            logger.info("  -> 获取条目 %d", bangumi_id)
            data = client.get_subject(bangumi_id)

            if data.get("nsfw"):
                logger.info("  -> 跳过 NSFW 条目 %d", bangumi_id)
                return True

            # 封面下载 → MinIO 转存 → 替换 URL 让 upsert_subject 直接写入 MinIO 路径
            raw_image = (data.get("images") or {}).get("large")
            if raw_image:
                minio_url = upload_cover(data["id"], raw_image)
                if minio_url != raw_image:
                    data.setdefault("images", {})["large"] = minio_url

            episodes = []
            total_eps = data.get("eps") or data.get("total_episodes") or 0
            if total_eps > 0:
                logger.info("  -> 获取剧集 subject %d（共 %d 集）", bangumi_id, total_eps)
                eps_data = client.get_episodes(bangumi_id)
                episodes = eps_data.get("data") or []

            # 关联条目：网络部分（拉取 + 判缺失 + 预取数据）全部在加锁前完成
            anime_relations = []
            related_pkgs = []
            try:
                relations = client.get_relations(bangumi_id)
                if relations:
                    anime_relations = [r for r in relations if r.get("type") == 2]
                    if not anime_relations:
                        logger.info("  -> 无非番剧关联条目")
                    else:
                        for rel in anime_relations:
                            related_bid = rel.get("id")
                            if not related_bid:
                                continue
                            exists = db.execute(
                                text("SELECT 1 FROM subject WHERE bangumi_id = :bid"),
                                {"bid": related_bid},
                            ).scalar()
                            if not exists:
                                logger.info("  -> 导入缺失的关联条目 %d（主条目 %d）", related_bid, bangumi_id)
                                try:
                                    pkg = _fetch_related(client, related_bid)
                                    if pkg:
                                        related_pkgs.append(pkg)
                                except Exception as e:
                                    logger.warning("  -> 关联条目 %d 预导入失败: %s", related_bid, e)

                    non_anime = [r for r in relations if r.get("type") not in (None, 2)]
                    if non_anime:
                        for r in non_anime:
                            logger.info("  -> 跳过非番剧关联条目 %d（type=%s）", r["id"], r.get("type"))
            except Exception as e:
                logger.warning("  -> 关联条目导入失败 subject %d: %s", bangumi_id, e)

            # DB 写阶段：同一时刻仅一个事务在写，commit 后即释放锁
            with _db_lock:
                subject_id = upsert_subject(db, data)

                tags = data.get("tags") or []
                if tags:
                    upsert_tags(db, subject_id, tags)

                if episodes:
                    upsert_episodes(db, subject_id, episodes)

                for pkg in related_pkgs:
                    _write_related(db, pkg)

                if anime_relations:
                    upsert_relations(db, subject_id, anime_relations)

                db.commit()
            return True

        except Exception as e:
            db.rollback()
            if "Deadlock" in str(e) and _retry < 4:
                delay = random.uniform(0.3, 1.0) * (_retry + 1)
                logger.warning("  -> subject %d 死锁，重试 (%d/4) delay=%.1fs", bangumi_id, _retry + 1, delay)
                time.sleep(delay)
                time.sleep(0.5 * (_retry + 1))
                continue
            logger.error("  x subject %d 导入失败: %s", bangumi_id, e)
            return False


def run_full(client, db, resume, **kw):
    global _done_count
    now = datetime.now()
    ids = []
    for year in range(2000, now.year + 1):
        max_month = now.month if year == now.year else 12
        for month in range(1, max_month + 1):
            logger.info("扫描 %d-%d...", year, month)
            offset = 0
            while True:
                try:
                    result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
                except Exception as e:
                    logger.error("扫描 %d-%d 失败: %s", year, month, e)
                    break
                items = result.get("data") or []
                if not items:
                    break
                ids.extend(item["id"] for item in items if item.get("id"))
                total_count = result.get("total", 0)
                offset += len(items)
                if offset >= total_count:
                    break
            # 扫描进度实时刷到 import_record.subject_count，页面可看到数量增长
            _done_count = len(ids)
    return _run_batch(ids, resume, base_done=len(ids), **kw)


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
                logger.error("扫描 %d-%d 失败: %s", year, month, e)
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
        logger.error("日历获取失败: %s", e)
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
                    logger.error("扫描 %d-%d 失败: %s", year, month, e)
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


def main():
    args = parse_args()

    load_dotenv()
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "anime_tracker")
    access_token = os.getenv("BANGUMI_ACCESS_TOKEN", "")
    user_agent = os.getenv("BANGUMI_USER_AGENT", "zhaizzH/AnimeTracker")

    client = BangumiClient(access_token=access_token, user_agent=user_agent)
    engine = get_engine(db_host, db_port, db_user, db_password, db_name)
    db = Session(engine)

    # 线程池共享参数
    pool_kw = dict(
        access_token=access_token, user_agent=user_agent,
        host=db_host, port=db_port, user=db_user, password=db_password, db_name=db_name,
        max_workers=min(args.workers, MAX_WORKERS_LIMIT),
    )

    PID_FILE.write_text(str(os.getpid()))
    record_id = create_import_record(db, args.mode, getattr(args, "key", None))
    db.commit()
    stop_flusher, flusher_thread = _start_count_flusher(record_id, engine)

    global _start_time
    _start_time = time.time()

    logger.info("")
    logger.info("=" * 60)
    logger.info("  Bangumi 数据导入")
    logger.info("  模式: %s", args.mode)
    if args.key:
        logger.info("  季度: %s", args.key)
    if args.since:
        logger.info("  起始: %s", args.since)
    if args.resume:
        logger.info("  启用跳过已导入条目")
    logger.info("=" * 60)
    logger.info("")
    try:
        if args.mode == "full":
            count = run_full(client, db, args.resume, **pool_kw)
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
        else:
            raise ValueError(f"Unknown mode: {args.mode}")

        stop_flusher.set()
        flusher_thread.join(timeout=5)
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
        logger.exception("导入异常终止（耗时 %s）", elapsed)
        complete_import_record(db, record_id, 0, "FAILED", str(e))
        db.commit()
        sys.exit(1)
    finally:
        PID_FILE.unlink(missing_ok=True)
        db.close()


if __name__ == "__main__":
    main()
