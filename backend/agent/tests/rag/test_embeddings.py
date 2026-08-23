from __future__ import annotations

import math

import pytest

from app.rag.embeddings import (
    DashScopeEmbeddingClient,
    EmbeddingRateLimited,
    EmbeddingResponseError,
    EmbeddingUnavailable,
)


VECTOR = [0.0] * 1024


def test_embedding_batches_at_ten_and_preserves_response_order():
    """一批最多十条，供应商必须按输入顺序返回。"""
    calls = []

    def transport(**kwargs):
        calls.append(kwargs)
        return [
            {"text_index": index, "embedding": [float(index)] * 1024}
            for index in range(len(kwargs["input"]))
        ]

    result = DashScopeEmbeddingClient("key", transport=transport).embed_documents(
        [f"档案-{index}" for index in range(11)]
    )

    assert [call["input"] for call in calls] == [
        [f"档案-{index}" for index in range(10)],
        ["档案-10"],
    ]
    assert all(call["model"] == "text-embedding-v4" for call in calls)
    assert all(call["dimension"] == 1024 for call in calls)
    assert result == [[float(index)] * 1024 for index in range(10)] + [VECTOR]


def test_embedding_rejects_out_of_order_response():
    """text_index 与输入顺序不符时不得静默错配档案。"""
    client = DashScopeEmbeddingClient(
        "key",
        transport=lambda **_: [
            {"text_index": 1, "embedding": VECTOR},
            {"text_index": 0, "embedding": VECTOR},
        ],
    )

    with pytest.raises(EmbeddingResponseError, match="顺序"):
        client.embed_documents(["档案一", "档案二"])


def test_embedding_rejects_wrong_dimension():
    """供应商维度漂移必须被拒绝。"""
    client = DashScopeEmbeddingClient("key", transport=lambda **_: [[0.0] * 8])

    with pytest.raises(EmbeddingResponseError, match="1024"):
        client.embed_documents(["档案"])


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_embedding_rejects_non_finite_values(value):
    """NaN 与无穷值不能进入向量索引。"""
    client = DashScopeEmbeddingClient("key", transport=lambda **_: [[value] * 1024])

    with pytest.raises(EmbeddingResponseError, match="有限"):
        client.embed_documents(["档案"])


def test_embedding_normalizes_overflowing_integer_values():
    """极大整数转换为浮点数失败时也必须返回稳定响应错误。"""
    client = DashScopeEmbeddingClient("key", transport=lambda **_: [[10**4000] * 1024])

    with pytest.raises(EmbeddingResponseError, match="有限"):
        client.embed_documents(["档案"])


def test_embedding_rejects_response_count_mismatch():
    """批次响应缺项必须失败，不能静默错配文本。"""
    client = DashScopeEmbeddingClient("key", transport=lambda **_: [])

    with pytest.raises(EmbeddingResponseError, match="条数"):
        client.embed_documents(["档案"])


def test_embedding_normalizes_rate_limit_and_unavailable_errors():
    """供应商错误只暴露稳定错误类型与非敏感消息。"""
    rate_limited = DashScopeEmbeddingClient(
        "key",
        transport=lambda **_: {"status_code": 429, "message": "secret provider body"},
    )
    unavailable = DashScopeEmbeddingClient(
        "key",
        transport=lambda **_: {"status_code": 503, "message": "secret provider body"},
    )

    with pytest.raises(EmbeddingRateLimited, match="embedding rate limited") as rate_error:
        rate_limited.embed_documents(["档案"])
    with pytest.raises(EmbeddingUnavailable, match="embedding unavailable") as unavailable_error:
        unavailable.embed_documents(["档案"])

    assert "secret provider body" not in str(rate_error.value)
    assert "secret provider body" not in str(unavailable_error.value)


def test_embedding_normalizes_api_rate_limit_code():
    """API 级限流码也必须映射到可重试的稳定错误。"""
    client = DashScopeEmbeddingClient(
        "key",
        transport=lambda **_: {"status_code": 400, "code": "Throttling.User"},
    )

    with pytest.raises(EmbeddingRateLimited, match="embedding rate limited"):
        client.embed_documents(["档案"])
