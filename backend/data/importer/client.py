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
