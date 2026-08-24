from __future__ import annotations

import pytest

from app.chat.user import UserInfo
from app.rag.retrieval import RagRetrievalService
from app.rag.schemas import RetrievalQuery


class FakeIndex:
    def lexical_search(self, _expression, limit):
        assert limit == 50
        return {"items": [{"subject_id": 1, "title": "Yuru Camp", "vector": [0.25] * 1024}]}

    def semantic_search(self, _expression, _vector, limit):
        assert limit == 50
        return {"items": [{"subject_id": 1, "title": "Yuru Camp", "vector": [0.25] * 1024}]}


class FakeEmbeddings:
    def embed_documents(self, texts):
        assert texts == ["治愈露营"]
        return [[0.25] * 1024]


class FakePreferenceProvider:
    def __init__(self) -> None:
        self.calls = []

    def load(self, user_id, token):
        self.calls.append((user_id, token))
        return None, False


@pytest.fixture
def fake_rag_dependencies():
    def authority(subject_ids, *, token, exclude_collected):
        assert subject_ids == [1]
        assert token == "jwt"
        assert exclude_collected is True
        return [{
            "id": 1,
            "name": "Yuru Camp",
            "nameCn": "摇曳露营△",
            "type": 2,
            "nsfw": False,
            "score": 8.2,
            "ratingTotal": 1000,
            "collectionTotal": 2000,
            "airDate": "2018-01-04",
        }]

    def business_search(_query, *, token):
        assert token == "jwt"
        return []

    return {
        "retrieval": RagRetrievalService(
            FakeIndex(),
            FakeEmbeddings(),
            authority_lookup=authority,
            business_search=business_search,
        ),
        "preference_provider": FakePreferenceProvider(),
    }


def test_use_case_returns_only_compact_authoritative_candidates(fake_rag_dependencies):
    from app.rag.use_case import RetrieveSubjectsUseCase

    use_case = RetrieveSubjectsUseCase(**fake_rag_dependencies)
    result = use_case.execute(
        RetrievalQuery(semantic_query="治愈露营"),
        mode="search",
        user=UserInfo(user_id=7, username="", role="USER", token="jwt"),
    )

    assert result["available"] is True
    assert result["items"] == [{
        "subjectId": 1,
        "title": "摇曳露营△",
        "score": result["items"][0]["score"],
        "reason": result["items"][0]["reason"],
    }]
    assert "vector" not in result["items"][0]


def test_use_case_loads_preference_with_user_identity(fake_rag_dependencies):
    from app.rag.use_case import RetrieveSubjectsUseCase

    provider = fake_rag_dependencies["preference_provider"]
    use_case = RetrieveSubjectsUseCase(**fake_rag_dependencies)

    use_case.execute(
        RetrievalQuery(semantic_query="治愈露营"),
        mode="recommend",
        user=UserInfo(user_id=7, username="", role="USER", token="jwt"),
    )

    assert provider.calls == [(7, "jwt")]
