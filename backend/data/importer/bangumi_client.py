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
                trust_env=False,
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
