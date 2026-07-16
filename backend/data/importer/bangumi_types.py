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
