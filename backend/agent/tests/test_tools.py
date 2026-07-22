import pytest
import respx
from httpx import Response
from app.tools.user_tools import (
    search_subjects, get_subject_detail, get_episodes,
    get_schedule, get_season_subjects, get_popular_subjects,
    get_top_rated, get_tags, get_subjects_by_tag, get_stats,
)
from app.config import settings

BASE = settings.backend_base_url


class TestUserTools:
    @respx.mock
    def test_search_subjects(self):
        route = respx.get(f"{BASE}/api/user/subjects/search").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1, "name": "Test"}], "total": 1}
        }))
        result = search_subjects.invoke({"query": "热血"})
        assert route.called
        assert result[0]["id"] == 1

    @respx.mock
    def test_get_subject_detail(self):
        respx.get(f"{BASE}/api/user/subjects/42").mock(Response(200, json={
            "code": 200, "data": {"id": 42, "name": "钢之炼金术师"}
        }))
        result = get_subject_detail.invoke({"subject_id": 42})
        assert result["name"] == "钢之炼金术师"

    @respx.mock
    def test_get_episodes(self):
        respx.get(f"{BASE}/api/user/subjects/1/episodes").mock(Response(200, json={
            "code": 200, "data": [{"id": 1, "sort": 1.0}]
        }))
        result = get_episodes.invoke({"subject_id": 1})
        assert len(result) == 1

    @respx.mock
    def test_get_schedule(self):
        respx.get(f"{BASE}/api/user/subjects/schedule").mock(Response(200, json={
            "code": 200, "data": {"content": [], "total": 0}
        }))
        result = get_schedule.invoke({"weekday": 1})
        assert "content" in result

    @respx.mock
    def test_get_tags(self):
        respx.get(f"{BASE}/api/user/tags").mock(Response(200, json={
            "code": 200, "data": [{"name": "热血", "count": 50}]
        }))
        result = get_tags.invoke({})
        assert result[0]["name"] == "热血"

    @respx.mock
    def test_get_stats(self):
        respx.get(f"{BASE}/api/user/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [], "total": 500, "page": 1, "size": 1}
        }))
        result = get_stats.invoke({})
        assert result["total"] == 500

    @respx.mock
    def test_tool_http_error(self):
        respx.get(f"{BASE}/api/user/subjects/search").mock(Response(500))
        result = search_subjects.invoke({"query": "error"})
        # 工具应返回错误 dict 而非抛异常
        assert isinstance(result, dict)
        assert result.get("error") is True

    @respx.mock
    def test_get_season_subjects(self):
        respx.get(f"{BASE}/api/user/subjects/season").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1}], "total": 1}
        }))
        result = get_season_subjects.invoke({"year": 2026, "quarter": "spring"})
        assert len(result) == 1

    @respx.mock
    def test_get_popular_subjects(self):
        respx.get(f"{BASE}/api/user/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1}], "total": 1}
        }))
        result = get_popular_subjects.invoke({"page": 1})
        assert result[0]["id"] == 1

    @respx.mock
    def test_get_top_rated(self):
        respx.get(f"{BASE}/api/user/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1}], "total": 1}
        }))
        result = get_top_rated.invoke({"page": 1})
        assert result[0]["id"] == 1

    @respx.mock
    def test_get_subjects_by_tag(self):
        respx.get(f"{BASE}/api/user/tags/热血/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1}], "total": 1}
        }))
        result = get_subjects_by_tag.invoke({"tag": "热血"})
        assert len(result) == 1
