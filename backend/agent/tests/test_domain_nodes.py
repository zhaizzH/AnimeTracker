from app.agent.client.domain.discover.tools import get_popular_subjects, get_schedule
from app.agent.client.domain.search.tools import search_subjects
from app.agent.client.domain.search.node import search_agent
from app.agent.client.domain.discover.node import discover_agent
from app.agent.client.domain.recommend.node import recommend_agent


def test_tools_are_registered():
    assert search_subjects.name == "search_subjects"
    assert get_schedule.name == "get_schedule"
    assert get_popular_subjects.name == "get_popular_subjects"


def test_nodes_are_callable():
    assert callable(search_agent)
    assert callable(discover_agent)
    assert callable(recommend_agent)
