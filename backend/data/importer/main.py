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
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from client import BangumiClient
from db import get_engine, upsert_subject, upsert_episodes, upsert_tags, \
    create_import_record, complete_import_record

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
                logger.info("  -> skip already imported subject %d", bangumi_id)
                return True

        logger.info("  -> fetch subject %d", bangumi_id)
        data = client.get_subject(bangumi_id)
        client.rate_limit()

        subject_id = upsert_subject(db, data)

        tags = data.get("tags") or []
        if tags:
            upsert_tags(db, subject_id, tags)

        total_eps = data.get("eps") or data.get("total_episodes") or 0
        if total_eps > 0:
            logger.info("  -> fetch episodes for subject %d (%d eps)", bangumi_id, total_eps)
            eps_data = client.get_episodes(bangumi_id)
            client.rate_limit()
            episodes = eps_data.get("data") or []
            if episodes:
                upsert_episodes(db, subject_id, episodes)

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.error("  x subject %d failed: %s", bangumi_id, e)
        return False


def run_full(client, db, resume):
    now = datetime.now()
    total = 0
    for year in range(2000, now.year + 1):
        max_month = now.month if year == now.year else 12
        for month in range(1, max_month + 1):
            logger.info("Processing %d-%d...", year, month)
            offset = 0
            while True:
                try:
                    result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
                    client.rate_limit()
                except Exception as e:
                    logger.error("Browse %d-%d failed: %s", year, month, e)
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

                total_count = result.get("total", 0)
                offset += len(items)
                if offset >= total_count:
                    break
    return total


def run_season(client, db, key, resume):
    year, ms, me = parse_season_key(key)
    total = 0
    for month in range(ms, me + 1):
        logger.info("Processing %d-%d...", year, month)
        offset = 0
        while True:
            try:
                result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
                client.rate_limit()
            except Exception as e:
                logger.error("Browse %d-%d failed: %s", year, month, e)
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

            total_count = result.get("total", 0)
            offset += len(items)
            if offset >= total_count:
                break
    return total


def run_recent(client, db, resume):
    logger.info("Fetching calendar...")
    try:
        calendar = client.get_calendar()
        client.rate_limit()
    except Exception as e:
        logger.error("Calendar failed: %s", e)
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
    return total


def run_since(client, db, since_date, resume):
    since = datetime.strptime(since_date, "%Y-%m-%d")
    now = datetime.now()
    total = 0

    for year in range(since.year, now.year + 1):
        start_month = since.month if year == since.year else 1
        end_month = now.month if year == now.year else 12
        for month in range(start_month, end_month + 1):
            logger.info("Processing %d-%d...", year, month)
            offset = 0
            while True:
                try:
                    result = client.browse_subjects(type=2, year=year, month=month, offset=offset)
                    client.rate_limit()
                except Exception as e:
                    logger.error("Browse %d-%d failed: %s", year, month, e)
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

    logger.info("=== Import started [mode=%s] ===", args.mode)
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
        logger.info("=== Import complete, %d subjects ===", count)

    except Exception as e:
        logger.exception("Import aborted")
        complete_import_record(db, record_id, 0, "FAILED", str(e))
        db.commit()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
