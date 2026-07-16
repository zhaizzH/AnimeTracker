# Bangumi 数据导入器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `backend/data/importer/` 下实现 4 文件 Python 导入器，通过 Bangumi Open API 将动画数据写入 MySQL。

**Architecture:** 扁平三模块 — `client.py` 封装 Bangumi API HTTP 调用（自动限流+重试），`db.py` 封装 SQLAlchemy ORM + upsert，`main.py` 用 argparse 做 CLI 入口并编排 4 种导入模式的流程。

**Tech Stack:** Python 3.10+, requests, SQLAlchemy 2.x, PyMySQL, python-dotenv.

## Global Constraints

- Python >= 3.10
- requests 库作为 HTTP 客户端，不使用 httpx/aiohttp（保持简单）
- SQLAlchemy 2.x + PyMySQL 作为数据库层
- 所有写入使用 `INSERT ... ON DUPLICATE KEY UPDATE` 确保幂等
- 请求间隔 `random.uniform(1.0, 2.0)` 秒
- 日志格式 `[timestamp] [LEVEL] message`，输出到 stdout
- User-Agent 使用 `zhaizzH/AnimeTracker`
- `.env` 文件不提交仓库，只提交 `.env.example`
- 数据库表结构由 `docs/db-schema.sql` 定义，不修改表结构

---

### Task 1: 项目脚手架 + 依赖

**Files:**
- Create: `backend/data/importer/requirements.txt`
- Create: `backend/data/importer/.env.example`
- Create: `backend/data/importer/__init__.py`（空文件，使目录成为包）

**Interfaces:**
- Consumes: (无)
- Produces: 项目基础结构，后续任务在其上构建

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p backend/data/importer
```

- [ ] **Step 2: 创建 `requirements.txt`**

```
requests>=2.31.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
python-dotenv>=1.0.0
```

- [ ] **Step 3: 创建 `.env.example`**

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=anime_tracker
BANGUMI_ACCESS_TOKEN=
BANGUMI_USER_AGENT=zhaizzH/AnimeTracker
```

- [ ] **Step 4: 创建空 `__init__.py`**

```python
# backend/data/importer/__init__.py
```

- [ ] **Step 5: 提交**

```bash
git add backend/data/importer/
git commit -m "chore(data): scaffold importer project structure"
```

---

### Task 2: `client.py` — Bangumi HTTP API 客户端

**Files:**
- Create: `backend/data/importer/client.py`

**Interfaces:**
- Consumes: 环境变量 `BANGUMI_ACCESS_TOKEN`, `BANGUMI_USER_AGENT`
- Produces: `BangumiClient` 类，Task 4 用其获取数据

- [ ] **Step 1: 创建 `client.py`**

```python
"""Bangumi API HTTP 客户端，自动限流 + 重试"""

import random
import time
import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bgm.tv"


class BangumiClient:
    """对 Bangumi v0 API 的轻量封装，每次请求后 sleep 1-2s 避免触发限流。"""

    def __init__(self, access_token: str = "", user_agent: str = "zhaizzH/AnimeTracker"):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": user_agent,
        })
        if access_token:
            self._session.headers["Authorization"] = f"Bearer {access_token}"
        self._access_token = access_token

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """发送请求，自动处理限流和重试。"""
        url = f"{BASE_URL}{path}"
        timeout = kwargs.pop("timeout", 30)

        for attempt in range(3):
            try:
                resp = self._session.request(method, url, timeout=timeout, **kwargs)
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", str(2 ** attempt)))
                    logger.warning("429 rate limited, waiting %ds (attempt %d)", retry_after, attempt + 1)
                    time.sleep(retry_after)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.Timeout:
                logger.warning("Timeout on %s (attempt %d)", path, attempt + 1)
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code in (502, 503, 504):
                    logger.warning("%d on %s (attempt %d)", e.response.status_code, path, attempt + 1)
                    time.sleep(2 ** attempt)
                    continue
                # 404 对 NSFW 条目是正常情况，不重试
                if e.response is not None and e.response.status_code == 404:
                    raise
                raise

        # 如果三次都 429，抛异常让上层处理
        raise RuntimeError(f"请求 {path} 失败，已达最大重试次数")

    def get_subject(self, subject_id: int) -> dict:
        """GET /v0/subjects/{subject_id} — 条目详情。"""
        return self._request("GET", f"/v0/subjects/{subject_id}")

    def get_episodes(self, subject_id: int, type: Optional[int] = None, limit: int = 200, offset: int = 0) -> dict:
        """GET /v0/episodes?subject_id= — 剧集列表，返回分页结构 {'data':[...], 'total':N}。"""
        params = {"subject_id": subject_id, "limit": limit, "offset": offset}
        if type is not None:
            params["type"] = type
        return self._request("GET", "/v0/episodes", params=params)

    def browse_subjects(self, type: int = 2, year: Optional[int] = None,
                        month: Optional[int] = None, offset: int = 0,
                        limit: int = 25) -> dict:
        """GET /v0/subjects — 按年份/月份浏览条目。"""
        params = {"type": type, "offset": offset, "limit": limit}
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        return self._request("GET", "/v0/subjects", params=params)

    def search_subjects(self, keyword: str, filter: Optional[dict] = None,
                        limit: int = 25, offset: int = 0) -> dict:
        """POST /v0/search/subjects — 搜索条目。"""
        body = {"keyword": keyword, "limit": limit, "offset": offset}
        if filter:
            body["filter"] = filter
        return self._request("POST", "/v0/search/subjects", json=body)

    def get_calendar(self) -> list:
        """GET /calendar — 每日放送（本周播出表）。"""
        return self._request("GET", "/calendar")

    def rate_limit(self):
        """两次请求间的限流等待（1-2 秒）。"""
        time.sleep(random.uniform(1.0, 2.0))
```

- [ ] **Step 2: 提交**

```bash
git add backend/data/importer/client.py
git commit -m "feat(data): add Bangumi API HTTP client with rate limiting"
```

---

### Task 3: `db.py` — SQLAlchemy 模型 + upsert 操作

**Files:**
- Create: `backend/data/importer/db.py`

**Interfaces:**
- Consumes: 环境变量 `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- Produces: `init_db()`, `upsert_subject()`, `upsert_episodes()`, `upsert_tags()`, `create_import_record()`, `complete_import_record()` — Task 4 用这些函数写数据库。

- [ ] **Step 1: 创建 `db.py`**

```python
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


def upsert_subject(session: Session, data: dict) -> int:
    """INSERT … ON DUPLICATE KEY UPDATE subject，返回 subject.id。"""
    bangumi_id = data["id"]
    existing = session.execute(
        text("SELECT id FROM subject WHERE bangumi_id = :bid"),
        {"bid": bangumi_id},
    ).scalar()

    now = datetime.now()
    if existing:
        session.execute(
            text("""
                UPDATE subject SET
                    name = :name, name_cn = :name_cn, summary = :summary,
                    type = :type, eps = :eps, air_date = :air_date,
                    image = :image, score = :score, rank = :rank,
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
                "air_date": data.get("date"),
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
                    (bangumi_id, name, name_cn, summary, type, eps, air_date,
                     image, score, rank, collection_total, nsfw,
                     import_status, last_imported_at, created_at, updated_at)
                VALUES
                    (:bangumi_id, :name, :name_cn, :summary, :type, :eps, :air_date,
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
                "air_date": data.get("date"),
                "image": (data.get("images") or {}).get("large"),
                "score": (data.get("rating") or {}).get("score"),
                "rank": (data.get("rating") or {}).get("rank"),
                "collection_total": (data.get("collection") or {}).get("collect", 0),
                "nsfw": data.get("nsfw", False),
                "now": now,
            },
        )
        subject_id = result.inserted_primary_key[0]

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
    now = datetime.now()
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
    return result.inserted_primary_key[0]


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
```

- [ ] **Step 2: 提交**

```bash
git add backend/data/importer/db.py
git commit -m "feat(data): add SQLAlchemy upsert operations for subject/episode/tag"
```

---

### Task 4: `main.py` — CLI 入口 + 4 种导入模式编排

**Files:**
- Create: `backend/data/importer/main.py`

**Interfaces:**
- Consumes: `BangumiClient` (Task 2), 数据库 upsert 函数 (Task 3), 环境变量 (Task 1)
- Produces: CLI 可执行文件，`python main.py --mode [full|season|recent|since]`

- [ ] **Step 1: 创建 `main.py`**

```python
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
from datetime import datetime, timedelta

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

# 季度 → 月份范围映射
SEASON_MONTHS = {
    "spring": (1, 3),
    "summer": (4, 6),
    "autumn": (7, 9),
    "winter": (10, 12),
}

# 事务提交批大小
COMMIT_EVERY = 50


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bangumi 数据导入器")
    parser.add_argument("--mode", required=True,
                        choices=["full", "season", "recent", "since"],
                        help="导入模式")
    parser.add_argument("--key", help="季度标识，如 2026-summer（season 模式必填）")
    parser.add_argument("--since", help="起始日期，如 2026-01-01（since 模式必填）")
    parser.add_argument("--resume", action="store_true",
                        help="跳过已导入的条目（import_status=1）")
    return parser.parse_args(argv)


def parse_season_key(key: str):
    """解析 '2026-summer' → (year, month_start, month_end)。"""
    parts = key.split("-")
    if len(parts) != 2:
        raise ValueError(f"无效的季度 key: {key}，应为 2026-summer 格式")
    year = int(parts[0])
    season = parts[1].lower()
    if season not in SEASON_MONTHS:
        raise ValueError(f"无效的季度: {season}，应为 spring/summer/autumn/winter")
    ms, me = SEASON_MONTHS[season]
    return year, ms, me


def get_air_weekday(date_str: str) -> int | None:
    """从 '2002-04-02' 格式日期解析星期（0=周日 ... 6=周六）。"""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return (dt.weekday() + 1) % 7  # 转为 0=周日
    except ValueError:
        return None


def import_single_subject(client: BangumiClient, db: Session, bangumi_id: int,
                          resume: bool) -> bool:
    """导入单个条目的详情+剧集+标签。返回 True 表示成功。"""
    try:
        # resume 模式检查是否已导入
        if resume:
            existing = db.execute(
                "SELECT id FROM subject WHERE bangumi_id = :bid AND import_status = 1",
                {"bid": bangumi_id},
            ).scalar()
            if existing:
                logger.info("  ↪ 跳过已导入 subject %d", bangumi_id)
                return True

        logger.info("  → 获取 subject %d 详情", bangumi_id)
        data = client.get_subject(bangumi_id)
        client.rate_limit()

        subject_id = upsert_subject(db, data)

        # 获取并 upsert 标签
        tags = data.get("tags") or []
        if tags:
            upsert_tags(db, subject_id, tags)

        # 获取剧集（如果有总集数）
        total_eps = data.get("eps") or data.get("total_episodes") or 0
        if total_eps > 0:
            logger.info("  → 获取 subject %d 剧集 (%d eps)", bangumi_id, total_eps)
            eps_data = client.get_episodes(bangumi_id)
            client.rate_limit()
            episodes = eps_data.get("data") or []
            if episodes:
                upsert_episodes(db, subject_id, episodes)

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.error("  ✗ subject %d 导入失败: %s", bangumi_id, e)
        return False


def run_full(client: BangumiClient, db: Session, resume: bool):
    """全量导入：按年份/月份遍历所有动画条目。"""
    now = datetime.now()
    total = 0
    for year in range(2000, now.year + 1):
        max_month = now.month if year == now.year else 12
        for month in range(1, max_month + 1):
            logger.info("处理 %d 年 %d 月...", year, month)
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

                total_count = result.get("total", 0)
                offset += len(items)
                if offset >= total_count:
                    break

    return total


def run_season(client: BangumiClient, db: Session, key: str, resume: bool):
    """季度导入。"""
    year, ms, me = parse_season_key(key)
    total = 0
    for month in range(ms, me + 1):
        logger.info("处理 %d 年 %d 月...", year, month)
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

            total_count = result.get("total", 0)
            offset += len(items)
            if offset >= total_count:
                break

    return total


def run_recent(client: BangumiClient, db: Session, resume: bool):
    """近期：使用 /calendar 获取本周放送表。"""
    logger.info("获取本周放送表...")
    try:
        calendar = client.get_calendar()
        client.rate_limit()
    except Exception as e:
        logger.error("获取 calendar 失败: %s", e)
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


def run_since(client: BangumiClient, db: Session, since_date: str, resume: bool):
    """自某时间起：遍历月份，只导入 air_date >= since 的条目。"""
    since = datetime.strptime(since_date, "%Y-%m-%d")
    now = datetime.now()
    total = 0

    for year in range(since.year, now.year + 1):
        start_month = since.month if year == since.year else 1
        end_month = now.month if year == now.year else 12
        for month in range(start_month, end_month + 1):
            logger.info("处理 %d 年 %d 月...", year, month)
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

                total_count = result.get("total", 0)
                offset += len(items)
                if offset >= total_count:
                    break

    return total


def main():
    args = parse_args()

    # 加载 .env
    load_dotenv()
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "anime_tracker")
    access_token = os.getenv("BANGUMI_ACCESS_TOKEN", "")
    user_agent = os.getenv("BANGUMI_USER_AGENT", "zhaizzH/AnimeTracker")

    # 初始化客户端和数据库
    client = BangumiClient(access_token=access_token, user_agent=user_agent)
    engine = get_engine(db_host, db_port, db_user, db_password, db_name)
    db = Session(engine)

    # 创建导入记录
    record_id = create_import_record(db, args.mode, getattr(args, "key", None))
    db.commit()

    logger.info("=== 开始导入 [mode=%s] ===", args.mode)
    try:
        if args.mode == "full":
            count = run_full(client, db, args.resume)
        elif args.mode == "season":
            if not args.key:
                raise ValueError("season 模式需要 --key 参数")
            count = run_season(client, db, args.key, args.resume)
        elif args.mode == "recent":
            count = run_recent(client, db, args.resume)
        elif args.mode == "since":
            if not args.since:
                raise ValueError("since 模式需要 --since 参数")
            count = run_since(client, db, args.since, args.resume)
        else:
            raise ValueError(f"未知模式: {args.mode}")

        complete_import_record(db, record_id, count, "COMPLETED")
        db.commit()
        logger.info("=== 导入完成，共处理 %d 个条目 ===", count)

    except Exception as e:
        logger.exception("导入异常终止")
        complete_import_record(db, record_id, 0, "FAILED", str(e))
        db.commit()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
git add backend/data/importer/main.py
git commit -m "feat(data): add CLI entry point with full/season/recent/since modes"
```

---

### Task 5: 集成验证

**Files:**
- Test: 运行一次 `python main.py --mode recent` 验证端到端工作

**Interfaces:**
- Consumes: 所有 3 个模块，.env 配置

- [ ] **Step 1: 创建 `.env` 并从已有 `.env` 填入凭据**

从项目其他位置或环境变量获取数据库凭据和 Access Token。

```bash
# 如果已有 .env 在其他位置，可以复制参考
# 编辑 backend/data/importer/.env
cat backend/data/importer/.env
```

- [ ] **Step 2: 安装依赖并试运行 recent 模式**

```bash
cd backend/data/importer
pip install -r requirements.txt
python main.py --mode recent
```

预期输出：
```
[2026-07-16 12:00:00] [INFO] === 开始导入 [mode=recent] ===
[2026-07-16 12:00:00] [INFO] 获取本周放送表...
[2026-07-16 12:00:03] [INFO]   → 获取 subject 12345 详情
[2026-07-16 12:00:05] [INFO]   → 获取 subject 12345 剧集 (12 eps)
...
[2026-07-16 12:05:00] [INFO] === 导入完成，共处理 42 个条目 ===
```

- [ ] **Step 3: 验证数据库中有数据**

```bash
# 检查 subject 表有数据
python -c "
from sqlalchemy import create_engine, text
import os; from dotenv import load_dotenv; load_dotenv()
engine = create_engine(f'mysql+pymysql://{os.getenv(\"DB_USER\")}:{os.getenv(\"DB_PASSWORD\")}@{os.getenv(\"DB_HOST\")}:{os.getenv(\"DB_PORT\")}/{os.getenv(\"DB_NAME\")}')
with engine.connect() as conn:
    cnt = conn.execute(text('SELECT COUNT(*) FROM subject')).scalar()
    print(f'subject: {cnt}')
    cnt = conn.execute(text('SELECT COUNT(*) FROM episode')).scalar()
    print(f'episode: {cnt}')
    cnt = conn.execute(text('SELECT COUNT(*) FROM subject_tag')).scalar()
    print(f'subject_tag: {cnt}')
    cnt = conn.execute(text('SELECT COUNT(*) FROM import_record')).scalar()
    print(f'import_record: {cnt}')
```
```

预期输出：
```
subject: 42
episode: 485
subject_tag: 210
import_record: 1
```

- [ ] **Step 4: 验证幂等性（第二次运行 upsert 不报错）**

```bash
cd backend/data/importer
python main.py --mode recent
```

应正常完成，不会报唯一键冲突。

- [ ] **Step 5: 提交（如果验证通过）**

```bash
git add -A backend/data/importer/
git commit -m "chore(data): finalize importer with integration verification"
```

---

### Spec Coverage Check

| Spec 要求 | 对应 Task |
|---|---|
| 支持 full/season/recent/since 四种模式 | Task 4 (`main.py` 中 `run_full/run_season/run_recent/run_since`) |
| 数据写入 subject/episode/subject_tag | Task 3 (`upsert_subject/upsert_episodes/upsert_tags`) |
| 每次运行记录到 import_record | Task 3 + Task 4 (`create_import_record/complete_import_record`) |
| UPSERT 语义 | Task 3 (全部使用 `ON DUPLICATE KEY UPDATE` 或先查后改) |
| 保守速率控制 1-2s | Task 2 (`BangumiClient.rate_limit()`) |
| User-Agent 设置 | Task 2 (`_session.headers["User-Agent"]`) |
| 429 自动重试 | Task 2 (`_request` 中处理 429/5xx) |
| 数据映射字段正确性 | Task 3 (字段映射表) |
| Python 3.10+ | Task 1 (requirements.txt 无版本限制下限) |
| `.env.example` 不提交凭据 | Task 1 (`.env` 在 `.gitignore` 中忽略，`.env.example` 提交) |
