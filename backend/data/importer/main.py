#!/usr/bin/env python3
"""Bangumi 数据导入器 CLI

Usage:
    python main.py --mode full
    python main.py --mode season --key 2026-summer
    python main.py --mode recent
    python main.py --mode since --since "2026-01-01"
    python main.py --mode season --key 2026-summer --resume
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
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

COMMIT_EVERY = 50

# ponytail: 模块级单例，避免层层传递
_minio_client = None
_start_time = None

EXT_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _fmt_duration(secs: float) -> str:
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"


def _get_minio_client():
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False,
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
    for attempt in range(3):
        image_url="https://proxy.8000150.xyz/"+image_url
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
            public_url = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000").rstrip("/")
            return f"{public_url}/{bucket}/{object_name}"
        except Exception as e:
            if attempt < 2:
                logger.warning("  封面上传失败 subject %d（第 %d 次重试）: %s", subject_id, attempt + 1, e)
            else:
                logger.warning("  封面上传失败 subject %d（已重试 2 次），回退到原始 URL: %s", subject_id, e)
    return image_url


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


def import_single_subject(client, db, bangumi_id, resume):
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
        client.rate_limit()

        if data.get("nsfw"):
            logger.info("  -> 跳过 NSFW 条目 %d", bangumi_id)
            return True

        # 封面下载 → MinIO 转存 → 替换 URL 让 upsert_subject 直接写入 MinIO 路径
        raw_image = (data.get("images") or {}).get("large")
        if raw_image:
            minio_url = upload_cover(data["id"], raw_image)
            if minio_url != raw_image:
                data.setdefault("images", {})["large"] = minio_url

        subject_id = upsert_subject(db, data)

        tags = data.get("tags") or []
        if tags:
            upsert_tags(db, subject_id, tags)

        total_eps = data.get("eps") or data.get("total_episodes") or 0
        if total_eps > 0:
            logger.info("  -> 获取剧集 subject %d（共 %d 集）", bangumi_id, total_eps)
            eps_data = client.get_episodes(bangumi_id)
            client.rate_limit()
            episodes = eps_data.get("data") or []
            if episodes:
                upsert_episodes(db, subject_id, episodes)

        # 导入关联条目
        try:
            relations = client.get_relations(bangumi_id)
            client.rate_limit()
            if relations:
                # 仅保留番剧关联（type=2）
                anime_relations = [r for r in relations if r.get("type") == 2]
                if not anime_relations:
                    logger.info("  -> 无非番剧关联条目")
                else:
                    # 预导入缺失的关联条目，确保 upsert_relations 时 FK 约束满足
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
                            import_single_subject(client, db, related_bid, resume)

                    upsert_relations(db, subject_id, anime_relations)
                # 记录非番剧跳过
                non_anime = [r for r in relations if r.get("type") not in (None, 2)]
                if non_anime:
                    for r in non_anime:
                        logger.info("  -> 跳过非番剧关联条目 %d（type=%s）", r["id"], r.get("type"))
        except Exception as e:
            logger.warning("  -> 关联条目导入失败 subject %d: %s", bangumi_id, e)

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.error("  x subject %d 导入失败: %s", bangumi_id, e)
        return False


def run_full(client, db, resume):
    now = datetime.now()
    total = 0
    for year in range(2000, now.year + 1):
        max_month = now.month if year == now.year else 12
        for month in range(1, max_month + 1):
            logger.info("处理 %d-%d...", year, month)
            offset = 0
            while True:
                try:
                    result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
                    client.rate_limit()
                except Exception as e:
                    logger.error("浏览 %d-%d 失败: %s", year, month, e)
                    break

                items = result.get("data") or []
                if not items:
                    break

                for item in items:
                    bid = item.get("id")
                    if not bid:
                        continue
                    if import_single_subject(client, db, bid, resume):
                        total += 1
                    if total % COMMIT_EVERY == 0:
                        db.commit()
                        _progress(total)

                total_count = result.get("total", 0)
                offset += len(items)
                if offset >= total_count:
                    break
    return total


def run_season(client, db, key, resume):
    year, ms, me = parse_season_key(key)
    total = 0
    for month in range(ms, me + 1):
        logger.info("处理 %d-%d...", year, month)
        offset = 0
        while True:
            try:
                result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
                client.rate_limit()
            except Exception as e:
                logger.error("浏览 %d-%d 失败: %s", year, month, e)
                break

            items = result.get("data") or []
            if not items:
                break

            for item in items:
                bid = item.get("id")
                if not bid:
                    continue
                if import_single_subject(client, db, bid, resume):
                    total += 1
                if total % COMMIT_EVERY == 0:
                    db.commit()
                    _progress(total)

            total_count = result.get("total", 0)
            offset += len(items)
            if offset >= total_count:
                break
    return total


def run_recent(client, db, resume):
    logger.info("获取日历...")
    try:
        calendar = client.get_calendar()
        client.rate_limit()
    except Exception as e:
        logger.error("日历获取失败: %s", e)
        return 0

    seen = set()
    total = 0
    for day in calendar:
        items = day.get("items") or []
        for item in items:
            bid = item.get("id")
            if not bid or bid in seen:
                continue
            seen.add(bid)
            if import_single_subject(client, db, bid, resume):
                total += 1
            if total % COMMIT_EVERY == 0:
                db.commit()
                _progress(total)
    return total


def run_since(client, db, since_date, resume):
    since = datetime.strptime(since_date, "%Y-%m-%d")
    now = datetime.now()
    total = 0

    for year in range(since.year, now.year + 1):
        start_month = since.month if year == since.year else 1
        end_month = now.month if year == now.year else 12
        for month in range(start_month, end_month + 1):
            logger.info("处理 %d-%d...", year, month)
            offset = 0
            while True:
                try:
                    result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
                    client.rate_limit()
                except Exception as e:
                    logger.error("浏览 %d-%d 失败: %s", year, month, e)
                    break

                items = result.get("data") or []
                if not items:
                    break

                for item in items:
                    bid = item.get("id")
                    item_date = item.get("date") or ""
                    if not bid or item_date < since_date:
                        continue
                    if import_single_subject(client, db, bid, resume):
                        total += 1
                    if total % COMMIT_EVERY == 0:
                        db.commit()
                        _progress(total)

                total_count = result.get("total", 0)
                offset += len(items)
                if offset >= total_count:
                    break
    return total


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

    record_id = create_import_record(db, args.mode, getattr(args, "key", None))
    db.commit()

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
            count = run_full(client, db, args.resume)
        elif args.mode == "season":
            if not args.key:
                raise ValueError("season mode needs --key")
            count = run_season(client, db, args.key, args.resume)
        elif args.mode == "recent":
            count = run_recent(client, db, args.resume)
        elif args.mode == "since":
            if not args.since:
                raise ValueError("since mode needs --since")
            count = run_since(client, db, args.since, args.resume)
        else:
            raise ValueError(f"Unknown mode: {args.mode}")

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
        db.close()


if __name__ == "__main__":
    main()
