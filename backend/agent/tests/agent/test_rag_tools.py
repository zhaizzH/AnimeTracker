from app.agent.client.rag_tools import _items, build_rag_tools
from app.chat.user import UserInfo


class _UseCase:
    def __init__(self) -> None:
        self.query = None

    def execute(self, query, *, mode, user):
        self.query = (query, mode, user)
        return {"available": True, "reason": "", "items": []}


def test_recommend_tool_preserves_structured_filters() -> None:
    use_case = _UseCase()
    recommend = build_rag_tools(use_case)[2]

    result = recommend.func(
        semantic_query="高分动画",
        year_from=2024,
        year_to=2026,
        quarter="spring",
        score_min=8.0,
        rating_total_min=1000,
        meta_tags=["热血"],
        air_status="UPCOMING",
        user=UserInfo(user_id=1, username="tester", role="USER", token="token"),
    )

    assert result == []
    query, mode, _user = use_case.query
    assert mode == "recommend"
    assert query.year_from == 2024
    assert query.year_to == 2026
    assert query.quarter == "spring"
    assert query.score_min == 8.0
    assert query.rating_total_min == 1000
    assert query.air_status == "UPCOMING"


def test_rag_unavailable_keeps_reason_for_callers() -> None:
    result = _items({"available": False, "reason": "evidence_unavailable", "items": []})

    assert result == {
        "available": False,
        "reason": "evidence_unavailable",
        "items": [],
    }
