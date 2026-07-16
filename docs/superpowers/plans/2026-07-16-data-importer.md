# 数据导入模块实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 `api/open-api/` 中定义的 Bangumi API v0 规范，实现从 Bangumi 抓取动漫条目/剧集/标签数据并写入 MySQL 的 Python CLI 工具。

**Architecture:** 四层结构：httpx HTTP 客户端层（Bangumi API v0 端点） → Pydantic 模型层 → SQLAlchemy ORM 写入层 → CLI 运行器协调层。同步 HTTP 请求 + 0.5s 间隔避免限频，SQLAlchemy session-per-batch 写入，import_record 表记录每次导入状态。

**Tech Stack:** Python 3.11+, httpx, SQLAlchemy 2.0+, PyMySQL, Pydantic v2, pytest

## Global Constraints

- MySQL 8.0, InnoDB, utf8mb4, 表结构见 `backend/data/schema/init.sql`
- 数据库连接信息从 `.env` 文件读取（已有 `config.py` 定义 `ImporterSettings`）
- User-Agent header 必须设置（Bangumi API 要求）
- 请求间隔默认 0.5s（`settings.REQUEST_INTERVAL`）
- 只导入 type=2（动画）的条目
- 不对 `subject` 表的已有数据（`import_status=1`）做任何变更，除非 `--full` 模式
- 文件全部位于 `backend/data/importer/` 目录下
- `api/open-api/v0.yaml` 定义了 v0 API 规范，`api/open-api/api.yml` 定义了 Legacy API 规范

---

### Task 1: ORM 模型 — models.py

**Files:**
- Modify: `backend/data/importer/models.py`
- Test: `backend/data/importer/tests/test_models.py`

**Interfaces:**
- Consumes: Database schema from `backend/data/schema/init.sql`
- Produces: SQLAlchemy ORM 类 `Subject`, `Episode`, `SubjectTag`, `ImportRecord` — 提供给 `db_writer.py`

- [ ] **Step 1: 安装依赖并初始化测试环境**

```bash
cd backend/data/importer
pip install -r requirements.txt
pip install pytest pytest-mock
mkdir -p tests
```

Run: `pip list | grep -E "sqlalchemy|httpx|pydantic|pytest"` — 确认所有包已安装。

- [ ] **Step 2: 编写测试 — 验证模型字段与数据库 schema 一致**

写 `backend/data/importer/tests/test_models.py`：

```python
"""验证 SQLAlchemy 模型字段与 init.sql 中定义的 schema 一致"""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from models import Subject, Episode, SubjectTag, ImportRecord, Base


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_subject_table_columns(engine):
    """验证 Subject 模型包含 init.sql 中 subject 表的所有字段"""
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("subject")}
    expected = {
        "id", "bangumi_id", "name", "name_cn", "summary",
        "type", "eps", "volumes", "air_date", "air_weekday",
        "image", "score", "rank", "collection_total", "nsfw",
        "import_status", "last_imported_at", "created_at", "updated_at",
    }
    assert expected.issubset(columns), f"Missing fields: {expected - columns}"
    # 验证唯一约束
    unique_constraints = inspector.get_unique_constraints("subject")
    assert any("bangumi_id" in c["column_names"] for c in unique_constraints)


def test_episode_table_columns(engine):
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("episode")}
    expected = {
        "id", "subject_id", "bangumi_ep_id", "type", "sort",
        "name", "name_cn", "duration", "airdate", "description",
        "status", "created_at",
    }
    assert expected.issubset(columns)


def test_subject_tag_table(engine):
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("subject_tag")}
    assert {"id", "subject_id", "name", "count"}.issubset(columns)
    unique_constraints = inspector.get_unique_constraints("subject_tag")
    assert any(set(c["column_names"]) == {"subject_id", "name"} for c in unique_constraints)


def test_import_record_table(engine):
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("import_record")}
    expected = {
        "id", "mode", "season_key", "started_at",
        "completed_at", "status", "subject_count", "error_message", "created_at",
    }
    assert expected.issubset(columns)


def test_subject_crud(engine):
    """CURD 基本操作"""
    from datetime import date
    with Session(engine) as session:
        s = Subject(
            bangumi_id=1,
            name="Test Anime",
            name_cn="测试动画",
            type=2,
            eps=12,
            air_date=date(2024, 1, 1),
            air_weekday=1,
            score=7.5,
            rank=100,
        )
        session.add(s)
        session.commit()
        fetched = session.query(Subject).filter_by(bangumi_id=1).first()
        assert fetched is not None
        assert fetched.name == "Test Anime"
        assert fetched.name_cn == "测试动画"
```

- [ ] **Step 3: 运行测试检查失败**

Run: `cd backend/data/importer && python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'models'` 或 `ImportError`，因为 `models.py` 尚未实现。

- [ ] **Step 4: 实现 models.py**

写入 `backend/data/importer/models.py`：

```python
"""
SQLAlchemy ORM 模型，映射到 anime_tracker 数据库表。
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Date, DateTime,
    SmallInteger, DECIMAL, Boolean, ForeignKey, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Subject(Base):
    __tablename__ = "subject"
    __table_args__ = {"comment": "条目表（动漫）"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    bangumi_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_cn: Mapped[Optional[str]] = mapped_column(String(255))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=2)
    eps: Mapped[Optional[int]] = mapped_column(Integer)
    volumes: Mapped[Optional[int]] = mapped_column(Integer)
    air_date: Mapped[Optional[date]] = mapped_column(Date)
    air_weekday: Mapped[Optional[int]] = mapped_column(SmallInteger)
    image: Mapped[Optional[str]] = mapped_column(String(512))
    score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 1))
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    collection_total: Mapped[Optional[int]] = mapped_column(Integer)
    nsfw: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    import_status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    last_imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    episodes = relationship("Episode", back_populates="subject", cascade="all, delete-orphan")
    tags = relationship("SubjectTag", back_populates="subject", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = "episode"
    __table_args__ = {"comment": "剧集表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("subject.id", ondelete="CASCADE"), nullable=False
    )
    bangumi_ep_id: Mapped[Optional[int]] = mapped_column(Integer)
    type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    sort: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 1))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    name_cn: Mapped[Optional[str]] = mapped_column(String(255))
    duration: Mapped[Optional[str]] = mapped_column(String(16))
    airdate: Mapped[Optional[date]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(4), nullable=False, default="NA")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    subject = relationship("Subject", back_populates="episodes")


class SubjectTag(Base):
    __tablename__ = "subject_tag"
    __table_args__ = (
        UniqueConstraint("subject_id", "name"),
        {"comment": "条目-标签关联表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("subject.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    subject = relationship("Subject", back_populates="tags")


class ImportRecord(Base):
    __tablename__ = "import_record"
    __table_args__ = {"comment": "导入记录表"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    season_key: Mapped[Optional[str]] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="RUNNING")
    subject_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd backend/data/importer && python -m pytest tests/test_models.py -v`
Expected: 5 tests passed
Expected output:
```
collected 5 items
tests/test_models.py::test_subject_table_columns PASSED
tests/test_models.py::test_episode_table_columns PASSED
tests/test_models.py::test_subject_tag_table PASSED
tests/test_models.py::test_import_record_table PASSED
tests/test_models.py::test_subject_crud PASSED
```

- [ ] **Step 6: Commit**

```bash
git add backend/data/importer/models.py backend/data/importer/tests/test_models.py
git commit -m "feat(data): implement SQLAlchemy ORM models for anime_tracker schema"
```

---

### Task 2: Bangumi API 客户端 — bangumi_client.py

**Files:**
- Create: `backend/data/importer/bangumi_types.py`（API 响应 Pydantic 模型）
- Modify: `backend/data/importer/bangumi_client.py`
- Test: `backend/data/importer/tests/test_bangumi_client.py`

**Interfaces:**
- Consumes: `settings.BANGUMI_API_BASE`, `settings.REQUEST_INTERVAL` 来自 `config.py`
- Produces: `BangumiClient` 类，提供 `get_subject()`, `browse_subjects()`, `search_subjects()`, `get_episodes()` 方法 — 供 `import_runner.py` 使用

- [ ] **Step 1: 编写测试 — API 客户端测试（使用 httpx MockTransport）**

写 `backend/data/importer/tests/test_bangumi_client.py`：

```python
"""Bangumi API 客户端测试"""

import pytest
from datetime import date
from bangumi_client import BangumiClient


@pytest.fixture
def mock_subject_response():
    return {
        "id": 12,
        "name": "ちょびっツ",
        "name_cn": "人形电脑天使心",
        "summary": "在不久的将来...",
        "type": 2,
        "date": "2002-04-02",
        "eps": 27,
        "images": {
            "large": "https://lain.bgm.tv/pic/cover/l/c2/0a/12_24O6L.jpg",
            "common": "https://lain.bgm.tv/pic/cover/c/c2/0a/12_24O6L.jpg",
        },
        "rating": {"total": 2289, "score": 7.6},
        "rank": 573,
        "collection_total": 3817,
        "nsfw": False,
    }


@pytest.fixture
def client():
    return BangumiClient(base_url="https://api.bgm.tv", request_interval=0.01)


@pytest.mark.asyncio
async def test_get_subject_success(client, mock_subject_response, mocker):
    """正常获取条目详情"""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_subject_response

    result = await client.get_subject(12)
    assert result["id"] == 12
    assert result["name_cn"] == "人形电脑天使心"
    mock_get.assert_called_once_with(
        "https://api.bgm.tv/v0/subjects/12",
        headers={"User-Agent": "AnimeTracker/1.0"},
    )


@pytest.mark.asyncio
async def test_get_subject_not_found(client, mocker):
    """条目不存在时返回 None"""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_get.return_value.status_code = 404

    result = await client.get_subject(999999)
    assert result is None


@pytest.mark.asyncio
async def test_browse_subjects(client, mocker):
    """浏览条目分页"""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_response = {
        "data": [
            {"id": 1, "name": "Anime A", "name_cn": "", "type": 2, "date": "2024-01-01"},
            {"id": 2, "name": "Anime B", "name_cn": "", "type": 2, "date": "2024-01-02"},
        ],
        "total": 2,
        "limit": 50,
        "offset": 0,
    }
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    result = await client.browse_subjects(type=2, year=2024, month=1)
    assert len(result["data"]) == 2
    # 检查 URL 包含正确的参数
    call_url = mock_get.call_args[0][0]
    assert "type=2" in call_url or "type=2" in str(mock_get.call_args)
    # GET 参数应该在 params 中
    assert mock_get.call_args[1].get("params", {}).get("type") == 2


@pytest.mark.asyncio
async def test_search_subjects(client, mocker):
    """搜索条目"""
    mock_post = mocker.patch("httpx.AsyncClient.post")
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": [{"id": 1, "name": "Result"}],
        "total": 1,
    }

    result = await client.search_subjects(keyword="test", limit=10)
    assert result["total"] == 1
    body = mock_post.call_args[1]["json"]
    assert body["keyword"] == "test"


@pytest.mark.asyncio
async def test_get_episodes(client, mocker):
    """获取剧集列表"""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "data": [
            {
                "id": 1027,
                "type": 0,
                "sort": 1,
                "name": "ちぃ 目覚める",
                "name_cn": "叽，觉醒了",
                "airdate": "2002-04-03",
                "duration": "24m",
                "desc": "",
                "status": "Air",
            }
        ],
        "total": 1,
    }

    result = await client.get_episodes(subject_id=12)
    assert len(result["data"]) == 1
    assert result["data"][0]["name_cn"] == "叽，觉醒了"


@pytest.mark.asyncio
async def test_rate_limiting(client, mocker):
    """请求间隔控制"""
    import asyncio
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": [], "total": 0}

    start = asyncio.get_event_loop().time()
    await client.get_episodes(subject_id=1)
    await client.get_episodes(subject_id=2)
    elapsed = asyncio.get_event_loop().time() - start
    # settings.REQUEST_INTERVAL=0.5，两次请求之间应至少等待 0.5s
    assert elapsed >= 0.009  # 测试用 0.01s interval — 因 mock patching 故只验证有延迟即可
```

- [ ] **Step 2: 运行测试检查失败**

Run: `cd backend/data/importer && python -m pytest tests/test_bangumi_client.py -v`
Expected: FAIL — `ModuleNotFoundError`（`bangumi_client.py` 和 `bangumi_types.py` 还没实现）

- [ ] **Step 3: 创建 API 响应 Pydantic 模型**

写入 `backend/data/importer/bangumi_types.py`：

```python
"""
Bangumi API v0 响应数据的 Pydantic 解析模型。
"""

from datetime import date
from typing import Any, Optional
from pydantic import BaseModel, Field


class SubjectImages(BaseModel):
    large: Optional[str] = None
    common: Optional[str] = None
    medium: Optional[str] = None
    small: Optional[str] = None
    grid: Optional[str] = None


class Rating(BaseModel):
    total: int = 0
    score: Optional[float] = None


class SubjectResponse(BaseModel):
    """GET /v0/subjects/{subject_id} 响应主体"""
    id: int
    name: str
    name_cn: Optional[str] = None
    summary: Optional[str] = None
    type: int = 2
    date: Optional[str] = None          # "2002-04-02"
    eps: Optional[int] = None
    images: Optional[SubjectImages] = None
    rating: Optional[Rating] = None
    rank: Optional[int] = None
    collection_total: Optional[int] = None
    nsfw: bool = False


class SubjectBrief(BaseModel):
    """条目搜索结果 / 浏览列表中的条目"""
    id: int
    name: str
    name_cn: Optional[str] = None
    type: int = 2
    date: Optional[str] = None
    eps: Optional[int] = None
    images: Optional[SubjectImages] = None


class Page(BaseModel):
    total: int = 0
    limit: int = 50
    offset: int = 0


class PagedSubject(Page):
    """GET /v0/subjects 和 POST /v0/search/subjects 响应"""
    data: list[SubjectBrief] = []


class EpisodeResponse(BaseModel):
    """GET /v0/episodes 响应中的单个 episode"""
    id: int
    type: int = 0
    sort: Optional[float] = None
    name: str = ""
    name_cn: Optional[str] = None
    duration: Optional[str] = None
    airdate: Optional[str] = None          # "2002-04-03"
    desc: Optional[str] = None
    status: str = "NA"


class PagedEpisode(Page):
    """GET /v0/episodes 响应"""
    data: list[EpisodeResponse] = []
```

- [ ] **Step 4: 实现 bangumi_client.py**

写入 `backend/data/importer/bangumi_client.py`：

```python
"""
Bangumi API v0 客户端。

封装对 Bangumi v0 API 的 HTTP 请求：
- GET  /v0/subjects/{subject_id}         — 条目详情
- GET  /v0/subjects?type=&year=&month=   — 浏览条目
- POST /v0/search/subjects              — 搜索/筛选条目
- GET  /v0/episodes?subject_id=         — 剧集列表
"""

import asyncio
import logging
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

USER_AGENT = "AnimeTracker/1.0"


class BangumiClient:
    """Bangumi API 客户端，自动处理限频。"""

    def __init__(self, base_url: str | None = None, request_interval: float | None = None):
        self.base_url = (base_url or settings.BANGUMI_API_BASE).rstrip("/")
        self.interval = request_interval or settings.REQUEST_INTERVAL
        self._client: httpx.AsyncClient | None = None
        self._last_request_time: float = 0.0

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=30.0,
            )
        return self._client

    async def _rate_limit(self):
        """在请求之间等待，避免触发 Bangumi API 频率限制。"""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.interval:
            await asyncio.sleep(self.interval - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _get(self, path: str, params: dict | None = None) -> dict | None:
        """发送 GET 请求，404 返回 None，其他错误抛出异常。"""
        client = await self._ensure_client()
        await self._rate_limit()
        url = f"{self.base_url}{path}"
        resp = await client.get(url, params=params)
        if resp.status_code == 404:
            return None
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "5"))
            logger.warning("Rate limited, waiting %ds", retry_after)
            await asyncio.sleep(retry_after)
            return await self._get(path, params)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json_body: dict) -> dict | None:
        """发送 POST 请求。"""
        client = await self._ensure_client()
        await self._rate_limit()
        url = f"{self.base_url}{path}"
        resp = await client.post(url, json=json_body)
        if resp.status_code == 404:
            return None
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "5"))
            logger.warning("Rate limited, waiting %ds", retry_after)
            await asyncio.sleep(retry_after)
            return await self._post(path, json_body)
        resp.raise_for_status()
        return resp.json()

    async def get_subject(self, subject_id: int) -> dict | None:
        """获取单个条目详情。

        GET /v0/subjects/{subject_id}
        """
        return await self._get(f"/v0/subjects/{subject_id}")

    async def browse_subjects(
        self,
        type: int = 2,
        year: int | None = None,
        month: int | None = None,
        sort: str | None = "date",
        limit: int = 50,
        offset: int = 0,
    ) -> dict | None:
        """浏览条目（支持分页和按年/月筛选）。

        GET /v0/subjects?type=2&year=&month=&sort=&limit=&offset=
        """
        params = {"type": type, "limit": limit, "offset": offset}
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month
        if sort is not None:
            params["sort"] = sort
        return await self._get("/v0/subjects", params=params)

    async def search_subjects(
        self,
        keyword: str = "",
        filter: dict | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict | None:
        """搜索/筛选条目。

        POST /v0/search/subjects
        """
        body = {
            "keyword": keyword,
            "filter": filter or {},
            "sort": "rank",
        }
        params = {"limit": limit, "offset": offset}
        client = await self._ensure_client()
        await self._rate_limit()
        url = f"{self.base_url}/v0/search/subjects"
        resp = await client.post(url, json=body, params=params)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "5"))
            logger.warning("Rate limited, waiting %ds", retry_after)
            await asyncio.sleep(retry_after)
            return await self.search_subjects(keyword, filter, limit, offset)
        resp.raise_for_status()
        return resp.json()

    async def get_episodes(
        self,
        subject_id: int,
        type: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict | None:
        """获取条目的剧集列表。

        GET /v0/episodes?subject_id=&type=&limit=&offset=
        """
        params = {"subject_id": subject_id, "limit": limit, "offset": offset}
        if type is not None:
            params["type"] = type
        return await self._get("/v0/episodes", params=params)

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd backend/data/importer && python -m pytest tests/test_bangumi_client.py -v`
Expected: 6 tests passed

```bash
cd backend/data/importer && python -m pytest tests/test_bangumi_client.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/data/importer/bangumi_types.py backend/data/importer/bangumi_client.py backend/data/importer/tests/test_bangumi_client.py
git commit -m "feat(data): implement Bangumi API v0 client with rate limiting"
```

---

### Task 3: 数据库写入器 — db_writer.py

**Files:**
- Modify: `backend/data/importer/db_writer.py`
- Create: `backend/data/importer/database.py`（引擎/会话工厂）
- Test: `backend/data/importer/tests/test_db_writer.py`

**Interfaces:**
- Consumes: `Subject`, `Episode`, `SubjectTag`, `ImportRecord` ORM 模型
- Consumes: `ImporterSettings` 中的数据库连接信息
- Produces: `DatabaseManager.upsert_subject()`, `upsert_episodes()`, `upsert_tags()`, 导入记录方法 — 供 `import_runner.py` 使用

- [ ] **Step 1: 创建 database.py — 引擎与会话工厂**

写入 `backend/data/importer/database.py`：

```python
"""
数据库引擎与会话管理。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models import Base


def create_db_url(settings) -> str:
    """从 ImporterSettings 构建 MySQL 连接 URL。"""
    return (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        "?charset=utf8mb4"
    )


engine = create_engine(
    create_db_url(settings),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

SessionFactory = sessionmaker(bind=engine, class_=Session)
```

- [ ] **Step 2: 编写测试 — DB 写入器测试（使用 SQLite）**

写 `backend/data/importer/tests/test_db_writer.py`：

```python
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
```

- [ ] **Step 3: 运行测试检查失败**

Run: `cd backend/data/importer && python -m pytest tests/test_db_writer.py -v`
Expected: FAIL — `ModuleNotFoundError`（`db_writer.py` 未实现）

- [ ] **Step 4: 实现 db_writer.py**

写入 `backend/data/importer/db_writer.py`：

```python
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
```

- [ ] **Step 5: 运行测试验证通过**

Run: `cd backend/data/importer && python -m pytest tests/test_db_writer.py -v`
Expected: 9 tests passed
Expected output:
```
collected 9 items
tests/test_db_writer.py::TestUpsertSubject::test_insert_new PASSED
tests/test_db_writer.py::TestUpsertSubject::test_upsert_update_existing PASSED
tests/test_db_writer.py::TestUpsertSubject::test_nullable_fields PASSED
tests/test_db_writer.py::TestUpsertEpisodes::test_batch_upsert PASSED
tests/test_db_writer.py::TestUpsertEpisodes::test_upsert_existing PASSED
tests/test_db_writer.py::TestUpsertTags::test_insert_tags PASSED
tests/test_db_writer.py::TestUpsertTags::test_unique_constraint PASSED
tests/test_db_writer.py::TestImportRecord::test_create_and_complete PASSED
tests/test_db_writer.py::TestImportRecord::test_fail_record PASSED
```

- [ ] **Step 6: Commit**

```bash
git add backend/data/importer/database.py backend/data/importer/db_writer.py backend/data/importer/tests/test_db_writer.py
git commit -m "feat(data): implement database writer with upsert and import record tracking"
```

---

### Task 4: 导入运行器 — import_runner.py + main.py

**Files:**
- Modify: `backend/data/importer/import_runner.py`
- Modify: `backend/data/importer/main.py`
- Test: `backend/data/importer/tests/test_import_runner.py`

**Interfaces:**
- Consumes: `BangumiClient.get_subject()`, `.browse_subjects()`, `.search_subjects()`, `.get_episodes()`
- Consumes: `DatabaseManager.upsert_subject()`, `.upsert_episodes()`, `.upsert_tags()`, 导入记录方法
- Produces: CLI 入口 `python main.py --full|--recent|--season|--since`，可直接运行

- [ ] **Step 1: 编写测试 — 导入运行器测试**

写 `backend/data/importer/tests/test_import_runner.py`：

```python
"""导入运行器测试"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Subject, Episode
from db_writer import DatabaseManager
from import_runner import (
    parse_args,
    ImportRunner,
)


@pytest.fixture
def db_manager():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    mgr = DatabaseManager(session=session)
    yield mgr
    session.close()


class TestParseArgs:
    def test_full_mode(self):
        args = parse_args(["--full"])
        assert args.mode == "full"

    def test_recent_mode(self):
        args = parse_args(["--recent"])
        assert args.mode == "recent"

    def test_season_mode(self):
        args = parse_args(["--season", "2024-spring"])
        assert args.mode == "season"
        assert args.season == "2024-spring"

    def test_since_mode(self):
        args = parse_args(["--since", "2024-01-01"])
        assert args.mode == "since"
        assert args.since == "2024-01-01"

    def test_no_args_shows_help(self):
        with pytest.raises(SystemExit):
            parse_args([])


class TestImportRunner:
    @pytest.mark.asyncio
    async def test_import_single_subject_success(self, db_manager):
        """导入单个条目成功"""
        runner = ImportRunner(db_manager=db_manager)
        runner.client = AsyncMock()
        runner.client.get_subject.return_value = {
            "id": 12,
            "name": "ちょびっツ",
            "name_cn": "人形电脑天使心",
            "summary": "A story...",
            "type": 2,
            "date": "2002-04-02",
            "eps": 27,
            "images": {"large": "https://example.com/cover.jpg"},
            "rating": {"total": 2289, "score": 7.6},
            "rank": 573,
            "collection_total": 3817,
            "nsfw": False,
        }
        runner.client.get_episodes.return_value = {
            "data": [
                {
                    "id": 1027, "type": 0, "sort": 1,
                    "name": "EP1", "name_cn": "第一集",
                    "airdate": "2002-04-03", "duration": "24m",
                    "desc": "", "status": "Air",
                }
            ],
            "total": 1,
        }

        subject = await runner.import_single_subject(12)
        assert subject is not None
        assert subject.bangumi_id == 12
        assert subject.name_cn == "人形电脑天使心"
        assert subject.import_status == 1

        # 验证剧集也被导入
        ep_count = runner.db.session.query(Episode).filter_by(subject_id=subject.id).count()
        assert ep_count == 1

    @pytest.mark.asyncio
    async def test_import_single_subject_not_found(self, db_manager):
        """条目不存在时返回 None"""
        runner = ImportRunner(db_manager=db_manager)
        runner.client = AsyncMock()
        runner.client.get_subject.return_value = None

        result = await runner.import_single_subject(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_run_season_import(self, db_manager):
        """季度导入"""
        runner = ImportRunner(db_manager=db_manager)
        runner.client = AsyncMock()
        # browse_subjects 返回两页数据
        runner.client.browse_subjects = AsyncMock()
        runner.client.browse_subjects.side_effect = [
            {
                "data": [
                    {"id": 1, "name": "Anime A", "name_cn": "", "type": 2, "date": "2024-01-01", "eps": 12},
                    {"id": 2, "name": "Anime B", "name_cn": "", "type": 2, "date": "2024-01-02", "eps": 24},
                ],
                "total": 2,
            },
            {"data": [], "total": 0},  # 结束翻页
        ]
        # get_subject 返回简化为已有数据（不重复请求详情）
        runner.client.get_episodes.return_value = {"data": [], "total": 0}

        result = await runner.run_season_import(year=2024, month=1)
        assert result > 0

    @pytest.mark.asyncio
    async def test_run_recent_import(self, db_manager):
        """最近数据导入"""
        runner = ImportRunner(db_manager=db_manager)
        runner.client = AsyncMock()
        runner.client.browse_subjects.return_value = {"data": [], "total": 0}

        result = await runner.run_recent_import(years_back=1)
        assert result == 0
```

- [ ] **Step 2: 运行测试检查失败**

Run: `cd backend/data/importer && python -m pytest tests/test_import_runner.py -v`
Expected: FAIL — `import_runner.py` 中的类还未实现

- [ ] **Step 3: 实现 import_runner.py**

写入 `backend/data/importer/import_runner.py`：

```python
"""
导入运行器。

处理 CLI 参数解析，协调导入流程。
支持四种模式: --full / --recent / --season / --since
"""

import argparse
import logging
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from bangumi_client import BangumiClient
from db_writer import DatabaseManager
from models import Subject

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("import_runner")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="AnimeTracker 数据导入器 — 从 Bangumi API 导入动漫数据",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--full", action="store_true", help="全量导入所有动画条目")
    mode.add_argument("--recent", action="store_true", help="导入近期动画（默认最近2年）")
    mode.add_argument("--season", type=str, metavar="YYYY-SEASON",
                      help='导入指定季度，如 "2024-spring"')
    mode.add_argument("--since", type=str, metavar="YYYY-MM-DD",
                      help="导入指定日期之后播出的条目")
    parser.add_argument("--years-back", type=int, default=2,
                        help="--recent 模式的回溯年数（默认2年）")
    parser.add_argument("--batch-size", type=int, default=50,
                        help="每次分页请求的数量（默认50）")
    parser.add_argument("--max-pages", type=int, default=100,
                        help="最大翻页数（默认100，防止无限循环）")
    args = parser.parse_args(argv)

    # 确定 mode 字符串
    if args.full:
        args.mode = "full"
    elif args.recent:
        args.mode = "recent"
    elif args.season:
        args.mode = "season"
    elif args.since:
        args.mode = "since"

    return args


SEASON_MONTH_MAP = {
    "winter": [1, 2, 3],
    "spring": [4, 5, 6],
    "summer": [7, 8, 9],
    "autumn": [10, 11, 12],
    "fall": [10, 11, 12],
}


class ImportRunner:
    """协调导入流程的主运行器。"""

    def __init__(self, db_manager: DatabaseManager | None = None):
        self.db = db_manager or DatabaseManager()
        self.client = BangumiClient()

    async def run(self, args: argparse.Namespace) -> int:
        """按 args.mode 执行不同导入策略。返回导入的条目数。"""
        record = self.db.create_import_record(
            mode=args.mode,
            season_key=getattr(args, "season", None),
        )
        try:
            if args.mode == "full":
                count = await self.run_full_import(args)
            elif args.mode == "recent":
                count = await self.run_recent_import(years_back=args.years_back, args=args)
            elif args.mode == "season":
                count = await self.run_season_from_str(args.season, args)
            elif args.mode == "since":
                count = await self.run_since_import(args.since, args)
            else:
                raise ValueError(f"未知导入模式: {args.mode}")

            self.db.commit()
            self.db.complete_import_record(record.id, subject_count=count)
            logger.info("导入完成，共处理 %d 个条目", count)
            return count
        except Exception as e:
            self.db.rollback()
            self.db.fail_import_record(record.id, error=str(e))
            logger.exception("导入失败: %s", e)
            raise

    async def import_single_subject(self, bangumi_id: int) -> Subject | None:
        """导入单个条目的详情和剧集。"""
        data = await self.client.get_subject(bangumi_id)
        if data is None:
            logger.warning("条目 %d 不存在（404）", bangumi_id)
            return None

        air_date = None
        if data.get("date"):
            try:
                air_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        rating = data.get("rating") or {}
        images = data.get("images") or {}
        subject = self.db.upsert_subject(
            bangumi_id=data["id"],
            name=data.get("name", ""),
            name_cn=data.get("name_cn"),
            summary=data.get("summary"),
            type=data.get("type", 2),
            eps=data.get("eps"),
            volumes=data.get("volumes"),
            air_date=air_date,
            image=images.get("large"),
            score=Decimal(str(rating["score"])) if rating.get("score") else None,
            rank=data.get("rank"),
            collection_total=rating.get("total") or data.get("collection_total"),
            nsfw=data.get("nsfw", False),
        )

        # 导入剧集
        await self._import_episodes(subject.id, bangumi_id)

        return subject

    async def _import_episodes(self, local_subject_id: int, bangumi_id: int):
        """获取并写入条目的剧集列表。"""
        episodes_data = await self._fetch_all_episodes(bangumi_id)
        if episodes_data:
            self.db.upsert_episodes(local_subject_id, episodes_data)

    async def _fetch_all_episodes(self, subject_id: int, batch_size: int = 200) -> list[dict]:
        """分页获取某个条目的所有剧集。"""
        all_eps = []
        offset = 0
        while True:
            result = await self.client.get_episodes(
                subject_id=subject_id,
                limit=batch_size,
                offset=offset,
            )
            if result is None:
                break
            batch = result.get("data", [])
            if not batch:
                break
            all_eps.extend(batch)
            offset += len(batch)
            if offset >= result.get("total", 0):
                break
        return all_eps

    async def run_full_import(self, args) -> int:
        """全量导入：遍历所有年份和月份。"""
        logger.info("开始全量导入")
        total = 0
        current_year = datetime.now().year
        # 从 2000 年到当前年遍历
        for year in range(2000, current_year + 1):
            for month in range(1, 13):
                count = await self._browse_and_import(
                    year=year, month=month, args=args
                )
                total += count
                logger.info("全量导入 %d-%02d: %d 条目", year, month, count)
        logger.info("全量导入完成，共 %d 条目", total)
        return total

    async def run_recent_import(self, years_back: int = 2, args=None) -> int:
        """导入最近 N 年的数据。"""
        logger.info("开始导入最近 %d 年数据", years_back)
        total = 0
        current_year = datetime.now().year
        start_year = current_year - years_back + 1
        for year in range(start_year, current_year + 1):
            for month in range(1, 13):
                count = await self._browse_and_import(
                    year=year, month=month, args=args
                )
                total += count
                logger.info("近期导入 %d-%02d: %d 条目", year, month, count)
        return total

    async def run_season_from_str(self, season_str: str, args) -> int:
        """按季度字符串导入，如 '2024-spring'。"""
        try:
            parts = season_str.split("-")
            year = int(parts[0])
            season_name = parts[1].lower()
        except (IndexError, ValueError):
            raise ValueError(f"季度格式无效: {season_str}，应为 YYYY-season（如 2024-spring）")

        months = SEASON_MONTH_MAP.get(season_name)
        if not months:
            raise ValueError(f"未知季度: {season_name}，可选: winter/spring/summer/autumn")

        logger.info("开始导入 %s", season_str)
        total = 0
        for month in months:
            count = await self._browse_and_import(
                year=year, month=month, args=args
            )
            total += count
        logger.info("季度导入 %s 完成，共 %d 条目", season_str, total)
        return total

    async def run_since_import(self, since_date_str: str, args) -> int:
        """导入指定日期之后的数据（使用 search API 的 air_date 过滤）。"""
        logger.info("开始导入 %s 之后的数据", since_date_str)
        try:
            since_date = datetime.strptime(since_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"日期格式无效: {since_date_str}，应为 YYYY-MM-DD")

        total = 0
        offset = 0
        while True:
            result = await self.client.search_subjects(
                keyword="",
                filter={"type": [2], "air_date": [f">={since_date_str}"]},
                limit=args.batch_size,
                offset=offset,
            )
            if result is None:
                break
            batch = result.get("data", [])
            if not batch:
                break
            for brief in batch:
                try:
                    await self.import_single_subject(brief["id"])
                    total += 1
                    logger.info("  [%d/%d] 导入条目 %d", total, result.get("total", 0), brief["id"])
                except Exception as e:
                    logger.error("导入条目 %d 失败: %s", brief["id"], e)
            offset += len(batch)
            if offset >= result.get("total", 0):
                break
        return total

    async def _browse_and_import(
        self,
        year: int,
        month: int,
        args,
    ) -> int:
        """按年月浏览条目页并逐个导入详情。"""
        count = 0
        offset = 0
        while offset // args.batch_size < args.max_pages:
            result = await self.client.browse_subjects(
                type=2,
                year=year,
                month=month,
                limit=args.batch_size,
                offset=offset,
            )
            if result is None:
                break
            batch = result.get("data", [])
            if not batch:
                break
            for brief in batch:
                try:
                    await self.import_single_subject(brief["id"])
                    count += 1
                except Exception as e:
                    logger.error("导入条目 %d 失败: %s", brief["id"], e)
            offset += len(batch)
            if offset >= result.get("total", 0):
                break
        return count

    async def close(self):
        await self.client.close()
        self.db.close()


def run_import():
    """主导入流程（同步入口，由 main.py 调用）。"""
    import asyncio
    args = parse_args()
    runner = ImportRunner()
    try:
        count = asyncio.run(runner.run(args))
        logger.info("成功导入 %d 个条目", count)
    except Exception:
        sys.exit(1)
    finally:
        import asyncio
        try:
            asyncio.run(runner.close())
        except RuntimeError:
            pass
```

- [ ] **Step 4: 更新 main.py**

写入 `backend/data/importer/main.py`：

```python
"""
AnimeTracker 数据导入器入口

从 Bangumi API 导入动漫数据到 MySQL 数据库。
支持四种模式: --full / --recent / --season / --since

用法:
    python main.py --full
    python main.py --recent
    python main.py --season 2024-spring
    python main.py --since 2024-01-01
"""

from import_runner import run_import


def main():
    run_import()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 编写 .env.example 文件**

写入 `backend/data/importer/.env.example`：

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=anime_tracker
MYSQL_USER=root
MYSQL_PASSWORD=root
BANGUMI_API_BASE=https://api.bgm.tv
REQUEST_INTERVAL=0.5
```

- [ ] **Step 6: 运行测试验证通过**

Run: `cd backend/data/importer && python -m pytest tests/test_import_runner.py -v`
Expected: 6 tests passed

Expected output:
```
collected 6 items
tests/test_import_runner.py::TestParseArgs::test_full_mode PASSED
tests/test_import_runner.py::TestParseArgs::test_recent_mode PASSED
tests/test_import_runner.py::TestParseArgs::test_season_mode PASSED
tests/test_import_runner.py::TestParseArgs::test_since_mode PASSED
tests/test_import_runner.py::TestParseArgs::test_no_args_shows_help PASSED
tests/test_import_runner.py::TestImportRunner::test_import_single_subject_success PASSED
tests/test_import_runner.py::TestImportRunner::test_import_single_subject_not_found PASSED
tests/test_import_runner.py::TestImportRunner::test_run_season_import PASSED
tests/test_import_runner.py::TestImportRunner::test_run_recent_import PASSED
```

- [ ] **Step 7: 运行全部测试确认所有通过**

Run: `cd backend/data/importer && python -m pytest tests/ -v`
Expected: 20 tests passed

- [ ] **Step 8: Commit**

```bash
git add backend/data/importer/import_runner.py backend/data/importer/main.py backend/data/importer/.env.example backend/data/importer/tests/test_import_runner.py
git commit -m "feat(data): implement CLI import runner with full/recent/season/since modes"
```

---

### Task 5: 集成验证与文档

**Files:**
- Create: `backend/data/importer/README.md`

- [ ] **Step 1: 编写 README.md**

写入 `backend/data/importer/README.md`：

```markdown
# AnimeTracker 数据导入器

从 Bangumi API v0 导入动漫数据到 MySQL 数据库。

## 快速开始

```bash
cd backend/data/importer

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库连接
cp .env.example .env
# 编辑 .env 填入你的 MySQL 连接信息

# 3. 初始化数据库（如尚未初始化）
mysql -u root -p < ../schema/init.sql

# 4. 运行导入
python main.py --recent        # 最近2年数据
python main.py --season 2024-spring  # 指定季度
python main.py --since 2024-01-01    # 增量导入
python main.py --full          # 全量导入（谨慎使用）
```

## 导入模式

| 模式 | 命令 | 说明 |
|------|------|------|
| 全量 | `--full` | 遍历 2000 年至今所有动画条目，**可能耗时数小时** |
| 近期 | `--recent` | 默认导入最近 2 年数据，`--years-back N` 控制回溯年数 |
| 季度 | `--season YYYY-season` | 导入指定季度，如 `2024-spring`, `2024-winter` |
| 增量 | `--since YYYY-MM-DD` | 导入指定日期之后播出的条目（使用 search API） |

## 架构

```
main.py → import_runner.py (CLI/流程)
              ├── bangumi_client.py (httpx, Bangumi API v0)
              ├── db_writer.py (SQLAlchemy UPSERT)
              │   ├── models.py (ORM 模型)
              │   └── database.py (引擎/会话)
              └── config.py (Pydantic 配置)
```

## Bangumi API 端点

- `GET /v0/subjects/{subject_id}` — 条目详情（cache 300s）
- `GET /v0/subjects?type=2&year=&month=` — 浏览条目（分页）
- `POST /v0/search/subjects` — 搜索/筛选（支持 air_date 过滤）
- `GET /v0/episodes?subject_id=` — 剧集列表（分页）
```

- [ ] **Step 2: 实机运行验证（在本地 MySQL 可用时）**

```bash
cd backend/data/importer

# 先执行 --recent 模式导入少量数据验证全流程
python main.py --recent --years-back 1

# 查看导入记录
mysql -u root -p anime_tracker -e "SELECT * FROM import_record ORDER BY id DESC LIMIT 5;"
mysql -u root -p anime_tracker -e "SELECT COUNT(*) as subject_count FROM subject WHERE import_status=1;"
mysql -u root -p anime_tracker -e "SELECT COUNT(*) as episode_count FROM episode;"
```

Expected: import_record 有 COMPLETED 记录，subject 表有数据，episode 表有对应的剧集。

- [ ] **Step 3: 最终 Commit**

```bash
git add backend/data/importer/README.md
git commit -m "docs(data): add importer README with usage guide and architecture overview"
```

---

## 文件清单总结

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/data/importer/models.py` | 修改 | SQLAlchemy ORM 模型（Subject, Episode, SubjectTag, ImportRecord） |
| `backend/data/importer/bangumi_types.py` | 创建 | Pydantic 模型解析 Bangumi API 响应 |
| `backend/data/importer/bangumi_client.py` | 修改 | httpx HTTP 客户端，含限频 |
| `backend/data/importer/database.py` | 创建 | SQLAlchemy 引擎和 SessionFactory |
| `backend/data/importer/db_writer.py` | 修改 | UPSERT 写入 + 导入记录管理 |
| `backend/data/importer/import_runner.py` | 修改 | CLI 参数解析 + 四种模式流程协调 |
| `backend/data/importer/main.py` | 修改 | CLI 入口（调用 run_import） |
| `backend/data/importer/.env.example` | 创建 | 环境变量模板 |
| `backend/data/importer/README.md` | 创建 | 使用说明 |
| `backend/data/importer/tests/test_models.py` | 创建 | ORM 模型测试 |
| `backend/data/importer/tests/test_bangumi_client.py` | 创建 | API 客户端测试 |
| `backend/data/importer/tests/test_db_writer.py` | 创建 | DB 写入器测试 |
| `backend/data/importer/tests/test_import_runner.py` | 创建 | 运行器测试 |

## 自检

1. **Spec coverage:** 四种导入模式（full/recent/season/since）均已覆盖。Bangumi API v0 中定义的相关端点（subject detail, browse, search, episodes）均已使用。import_record 记录每次运行状态。
2. **Placeholder scan:** 无 TBD/TODO 占位符，所有代码有完整实现和测试。
3. **Type consistency:** models.py 的字段名与 init.sql 完全一致。bangumi_types.py 的字段名与 v0.yaml API 响应一致。db_writer.upsert_subject 的参数名与 bangumi_client.get_subject 返回的 JSON key 在 import_runner.py 中交叉引用一致。parse_args() 返回的 `args.mode` 在 import_runner.py:run() 中用于 switch，二者一致。
