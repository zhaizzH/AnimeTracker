from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.rag.schemas import RetrievalQuery
from app.rag.retrieval import escape_redis_term


def test_query_escapes_raw_redis_syntax():
    """Removing escaping would turn a keyword into a RediSearch expression."""
    query = RetrievalQuery(semantic_query="x", keywords=["*)|(@nsfw:{true}"])

    assert escape_redis_term(query.keywords[0]) == r"\*\)\|\(\@nsfw\:\{true\}"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"semantic_query": "\x00"},
        {"keywords": ["ok\nno"]},
        {"semantic_query": "x", "unknown": "no"},
        {"semantic_query": "x", "year_from": 2025, "year_to": 2024},
    ],
)
def test_query_rejects_empty_injected_or_inconsistent_boundaries(payload):
    """Removing model validation would accept unsafe or meaningless retrieval input."""
    with pytest.raises(ValidationError):
        RetrievalQuery(**payload)


def test_structured_filter_is_a_valid_retrieval_intent():
    query = RetrievalQuery(year_from=2024, air_status="AIRING")

    assert query.year_from == 2024
    assert query.air_status == "AIRING"
