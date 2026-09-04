"""Bangumi API HTTP 客户端，自动限流 + 重试"""

import logging
import os
import time
from typing import Any, Iterator, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.bgm.tv"


class BangumiClient:
    """对 Bangumi v0 API 的轻量封装。"""

    def __init__(self, access_token: str = "", user_agent: str = "zhaizzH/AnimeTracker",
                 request_delay: float = 0, base_url: str | None = None):
        # ponytail: 惰性读 env——client 在 load_dotenv() 前就被 import，模块级读取会拿默认值
        self._base_url = base_url or os.getenv("BANGUMI_BASE_URL", DEFAULT_BASE_URL)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": user_agent,
        })
        if access_token:
            self._session.headers["Authorization"] = f"Bearer {access_token}"
        self._access_token = access_token
        self._request_delay = request_delay

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """发送请求，自动处理限流和重试。"""
        url = f"{self._base_url}{path}"
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
                result = resp.json()
                if self._request_delay:
                    time.sleep(self._request_delay)
                return result
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

    def get_all_episodes(self, subject_id: int, limit: int = 200) -> list[dict]:
        """获取条目的全部剧集，按响应实际条数推进分页偏移量。"""
        offset = 0
        episodes = []
        while True:
            page = self.get_episodes(subject_id, limit=limit, offset=offset)
            items = page.get("data") or []
            episodes.extend(items)
            offset += len(items)
            if not items or offset >= int(page.get("total") or 0):
                return episodes

    def get_subject_persons(self, subject_id: int) -> list[dict]:
        """GET /v0/subjects/{subject_id}/persons — 条目的关联人物。"""
        return self._request("GET", f"/v0/subjects/{subject_id}/persons")

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

    def iter_subject_ids(self, subject_type: int = 2, limit: int = 100) -> Iterator[int]:
        """按页遍历 Bangumi 条目 ID，保留首次出现的顺序。"""
        offset = 0
        seen = set()
        while True:
            page = self.browse_subjects(type=subject_type, offset=offset, limit=limit)
            items = page.get("data") or []
            for item in items:
                subject_id = item.get("id")
                if subject_id and subject_id not in seen:
                    seen.add(subject_id)
                    yield subject_id
            offset += len(items)
            if not items or offset >= int(page.get("total") or 0):
                return

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

    def get_relations(self, subject_id: int) -> list[dict]:
        """GET /v0/subjects/{subject_id}/subjects — 条目关联列表。"""
        return self._request("GET", f"/v0/subjects/{subject_id}/subjects")

    def get_subject_characters(self, subject_id: int) -> list[dict]:
        """GET /v0/subjects/{subject_id}/characters — 条目的关联角色（含声优）。"""
        return self._request("GET", f"/v0/subjects/{subject_id}/characters")

    def get_person(self, person_id: int) -> dict:
        """GET /v0/persons/{person_id} — 人物详情。"""
        return self._request("GET", f"/v0/persons/{person_id}")

    def get_character(self, character_id: int) -> dict:
        """GET /v0/characters/{character_id} — 角色详情。"""
        return self._request("GET", f"/v0/characters/{character_id}")

    def get_person_subjects(self, person_id: int, limit: int = 100, offset: int = 0) -> dict:
        """GET /v0/persons/{person_id}/subjects — 人物参与的条目。"""
        params = {"limit": limit, "offset": offset}
        return self._request("GET", f"/v0/persons/{person_id}/subjects", params=params)

    def get_character_subjects(self, character_id: int, limit: int = 100, offset: int = 0) -> dict:
        """GET /v0/characters/{character_id}/subjects — 角色出现的条目。"""
        params = {"limit": limit, "offset": offset}
        return self._request("GET", f"/v0/characters/{character_id}/subjects", params=params)
