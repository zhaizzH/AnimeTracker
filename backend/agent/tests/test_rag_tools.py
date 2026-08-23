from app.agent.client import rag_tools
from app.rag import retrieval
from app.rag.retrieval import RetrievalCandidate, RetrievalResult
from app.schemas.auth import UserInfo


class FakeRetrieval:
    def __init__(self) -> None:
        self.calls = []

    def retrieve(self, query, mode, token=None, preference=None, personalization_missing=False):
        self.calls.append((query, mode, token, preference, personalization_missing))
        return RetrievalResult(
            available=True,
            items=[
                RetrievalCandidate(
                    subject_id=7,
                    retrieval_score=0.99,
                    retrieval_reason="lexical+semantic",
                    title="摇曳露营",
                    details={
                        "id": 7,
                        "nameCn": "摇曳露营",
                        "score": 9.1,
                        "ratingTotal": 1234,
                        "tags": [{"name": "治愈"}, {"name": "露营"}],
                        "credits": ["京极义昭"],
                    },
                )
            ],
        )


def test_retrieval_service_and_index_share_configured_active_alias(monkeypatch):
    class FakeRedis:
        pass

    class FakeIndex:
        def __init__(self, _client, *, active_alias):
            self.active_alias = active_alias

    class FakeService:
        def __init__(self, index, _embeddings, *, business_search):
            self.index = index

    alias = "idx:custom:subject:active"
    monkeypatch.setattr(rag_tools.settings, "rag_enabled", True)
    monkeypatch.setattr(rag_tools.settings, "rag_index_alias", alias)
    monkeypatch.setattr(rag_tools.redis.Redis, "from_url", lambda *_args, **_kwargs: FakeRedis())
    monkeypatch.setattr(rag_tools, "RedisSubjectIndex", FakeIndex)
    monkeypatch.setattr(rag_tools, "RagRetrievalService", FakeService)

    service = rag_tools.get_retrieval_service("search")
    assert service.index.active_alias == alias


def test_search_tool_returns_only_verified_compact_evidence(monkeypatch):
    fake = FakeRetrieval()
    monkeypatch.setattr(rag_tools, "get_retrieval_service", lambda mode: fake)

    result = rag_tools.rag_search_subjects.invoke({"semantic_query": "治愈露营"})

    assert result == [{
        "subjectId": 7,
        "name": "摇曳露营",
        "score": 9.1,
        "ratingTotal": 1234,
        "matchedTags": ["治愈", "露营"],
        "matchedCredits": ["京极义昭"],
        "retrievalReason": "lexical+semantic",
    }]
    query, mode, token, preference, personalization_missing = fake.calls[0]
    assert query.semantic_query == "治愈露营"
    assert query.keywords == ["治愈露营"]
    assert mode == "search"
    assert token is None and preference is None and personalization_missing is False


def test_search_forwards_only_injected_user_token_to_retrieval(monkeypatch):
    fake = FakeRetrieval()
    monkeypatch.setattr(rag_tools, "get_retrieval_service", lambda mode: fake)
    user = UserInfo(user_id=5, username="tester", role="USER", token="signed-token")

    rag_tools.rag_search_subjects.func("露营", user=user)

    assert fake.calls[0][2] == "signed-token"


def test_discover_uses_structured_filters_before_semantic_text(monkeypatch):
    fake = FakeRetrieval()
    monkeypatch.setattr(rag_tools, "get_retrieval_service", lambda mode: fake)

    rag_tools.rag_discover_subjects.func(year_from=2024, year_to=2024, quarter="spring", score_min=8.0)

    query, mode, *_ = fake.calls[0]
    assert mode == "discover"
    assert query.year_from == 2024 and query.year_to == 2024
    assert query.quarter == "spring" and query.score_min == 8.0



def test_disabled_rag_uses_business_search_then_batch_authority_lookup(monkeypatch):
    calls = []

    def fallback_call(method, path, **kwargs):
        calls.append((method, path, kwargs.get("token")))
        return {"content": [{"id": 7}]}

    def batch_call(method, path, **kwargs):
        calls.append((method, path, kwargs.get("token")))
        return [{"id": 7, "name": "摇曳露营", "type": 2, "nsfw": False}]

    monkeypatch.setattr(rag_tools.settings, "rag_enabled", False)
    monkeypatch.setattr(rag_tools, "call_api", fallback_call)
    monkeypatch.setattr(retrieval, "call_api", batch_call)
    user = UserInfo(user_id=5, username="tester", role="USER", token="signed-token")

    result = rag_tools.rag_search_subjects.func("露营", user=user)

    assert result[0]["subjectId"] == 7
    assert calls == [
        ("GET", "/api/client/subjects/search", "signed-token"),
        ("POST", "/api/client/subjects/batch", "signed-token"),
    ]


def test_redis_failure_uses_discover_season_then_batch_authority_lookup(monkeypatch):
    calls = []

    class BrokenRedis:
        def execute_command(self, *_args):
            raise RuntimeError("redis unavailable")

    def fallback_call(method, path, **kwargs):
        calls.append((method, path))
        return {"content": [{"id": 8}]}

    def batch_call(method, path, **kwargs):
        calls.append((method, path))
        return [{"id": 8, "name": "春季番", "type": 2, "nsfw": False}]

    monkeypatch.setattr(rag_tools.settings, "rag_enabled", True)
    monkeypatch.setattr(rag_tools.redis.Redis, "from_url", lambda *_args, **_kwargs: BrokenRedis())
    monkeypatch.setattr(rag_tools, "call_api", fallback_call)
    monkeypatch.setattr(retrieval, "call_api", batch_call)

    result = rag_tools.rag_discover_subjects.func(year_from=2024, year_to=2024, quarter="spring")

    assert result[0]["subjectId"] == 8
    assert calls == [("GET", "/api/client/subjects/season"), ("POST", "/api/client/subjects/batch")]

def test_recommend_injects_user_preference_and_excludes_collections(monkeypatch):
    fake = FakeRetrieval()
    preference = rag_tools.UserPreference(
        vector=(0.0,) * 1024,
        exclude_subject_ids=(11, 12),
        sample_count=3,
        collection_version="version",
    )
    user = UserInfo(user_id=5, username="tester", role="USER", token="signed-token")
    monkeypatch.setattr(rag_tools.settings, "rag_enabled", True)
    monkeypatch.setattr(rag_tools, "get_retrieval_service", lambda mode: fake)
    monkeypatch.setattr(rag_tools, "_load_preference", lambda actual_user: (preference, False))

    rag_tools.rag_recommend_subjects.func("治愈", user=user)

    query, mode, token, actual_preference, personalization_missing = fake.calls[0]
    assert mode == "recommend" and token == "signed-token"
    assert query.exclude_subject_ids == [11, 12]
    assert actual_preference is preference and personalization_missing is False


def test_discover_keeps_semantic_query_empty_for_structured_filters(monkeypatch):
    fake = FakeRetrieval()
    monkeypatch.setattr(rag_tools, "get_retrieval_service", lambda mode: fake)

    result = rag_tools.rag_discover_subjects.func(year_from=2024, year_to=2024, quarter="spring")

    query, mode, *_ = fake.calls[0]
    assert result[0]["subjectId"] == 7
    assert mode == "discover"
    assert query.semantic_query == ""
    assert "热门动画" not in query.semantic_query

def test_recommend_without_query_builds_a_valid_default_query(monkeypatch):
    fake = FakeRetrieval()
    monkeypatch.setattr(rag_tools, "get_retrieval_service", lambda mode: fake)

    result = rag_tools.rag_recommend_subjects.func()

    assert result[0]["subjectId"] == 7
    assert len(fake.calls) == 1
    assert fake.calls[0][0].semantic_query == "热门动画"

def test_recommend_empty_query_uses_the_default_query(monkeypatch):
    fake = FakeRetrieval()
    monkeypatch.setattr(rag_tools, "get_retrieval_service", lambda mode: fake)

    result = rag_tools.rag_recommend_subjects.func("")

    assert result[0]["subjectId"] == 7
    assert len(fake.calls) == 1
    assert fake.calls[0][0].semantic_query == "热门动画"
