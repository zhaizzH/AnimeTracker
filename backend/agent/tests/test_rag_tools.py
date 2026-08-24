from __future__ import annotations

from app.agent.client.rag_tools import build_rag_tools
from app.chat.user import UserInfo


class FakeUseCase:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, query, *, mode, user):
        self.calls.append((query, mode, user))
        return {
            "available": True,
            "reason": "",
            "personalizationNotice": "",
            "items": [{
                "subjectId": 7,
                "title": "摇曳露营",
                "score": 0.99,
                "reason": "lexical+semantic",
            }],
        }


def _tool(tools, name):
    return next(item for item in tools if item.name == name)


def test_rag_tool_module_does_not_construct_redis_or_embedding_clients():
    source = open("app/agent/client/rag_tools.py", encoding="utf-8").read()
    assert "Redis.from_url" not in source
    assert "DashScopeEmbeddingClient(" not in source


def test_search_tool_returns_use_case_compact_candidates():
    use_case = FakeUseCase()
    search_tool = _tool(build_rag_tools(use_case), "rag_search_subjects")

    result = search_tool.invoke({"semantic_query": "治愈露营"})

    assert result == [{
        "subjectId": 7,
        "title": "摇曳露营",
        "score": 0.99,
        "reason": "lexical+semantic",
    }]
    query, mode, user = use_case.calls[0]
    assert query.semantic_query == "治愈露营"
    assert query.keywords == ["治愈露营"]
    assert mode == "search"
    assert user.user_id == 0 and user.token == ""


def test_search_forwards_only_injected_user_token_to_use_case():
    use_case = FakeUseCase()
    user = UserInfo(user_id=5, username="tester", role="USER", token="signed-token")
    search_tool = _tool(build_rag_tools(use_case), "rag_search_subjects")

    search_tool.func("露营", user=user)

    assert use_case.calls[0][2] is user


def test_discover_uses_structured_filters_before_semantic_text():
    use_case = FakeUseCase()
    discover_tool = _tool(build_rag_tools(use_case), "rag_discover_subjects")

    discover_tool.func(year_from=2024, year_to=2024, quarter="spring", score_min=8.0)

    query, mode, _user = use_case.calls[0]
    assert mode == "discover"
    assert query.semantic_query == ""
    assert query.year_from == 2024 and query.year_to == 2024
    assert query.quarter == "spring" and query.score_min == 8.0


def test_recommend_empty_query_uses_the_default_query():
    use_case = FakeUseCase()
    recommend_tool = _tool(build_rag_tools(use_case), "rag_recommend_subjects")

    result = recommend_tool.func("")

    assert result[0]["subjectId"] == 7
    assert use_case.calls[0][0].semantic_query == "热门动画"
    assert use_case.calls[0][1] == "recommend"
