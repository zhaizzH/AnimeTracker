from app.agent.client.discover import get_popular_subjects, get_schedule
from app.agent.client.search import search_subjects
from app.agent.client.search import search_agent
from app.agent.client.discover import discover_agent
from app.agent.client.recommend import recommend_agent
from app.agent.client.collections import get_my_collections, get_my_stats, get_my_watch_profile
from app.agent.time_tool import get_current_time


def test_tools_are_registered():
    assert search_subjects.name == "search_subjects"
    assert get_schedule.name == "get_schedule"
    assert get_popular_subjects.name == "get_popular_subjects"
    assert get_current_time.name == "get_current_time"


def test_nodes_are_callable():
    assert callable(search_agent)
    assert callable(discover_agent)
    assert callable(recommend_agent)


def test_user_tools_registered():
    assert get_my_collections.name == "get_my_collections"
    assert get_my_stats.name == "get_my_stats"
    assert get_my_watch_profile.name == "get_my_watch_profile"
