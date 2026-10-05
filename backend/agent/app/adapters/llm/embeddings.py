from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from typing import Any


EMBEDDING_MODEL = "text-embedding-v4"
EMBEDDING_DIMENSIONS = 1024
_MAX_BATCH_SIZE = 10


class EmbeddingError(RuntimeError):
    """Embedding 供应商失败的稳定基类。"""


class EmbeddingRateLimited(EmbeddingError):
    pass


class EmbeddingUnavailable(EmbeddingError):
    pass


class EmbeddingResponseError(EmbeddingError):
    pass


Transport = Callable[..., Any]


class DashScopeEmbeddingClient:
    """DashScope text-embedding-v4 的小型同步适配器。"""

    def __init__(
        self,
        api_key: str,
        model: str = EMBEDDING_MODEL,
        dimensions: int = EMBEDDING_DIMENSIONS,
        *,
        transport: Transport | None = None,
    ) -> None:
        if model != EMBEDDING_MODEL:
            raise ValueError(f"不支持的向量模型: {model}")
        if dimensions != EMBEDDING_DIMENSIONS:
            raise ValueError(f"不支持的向量维度: {dimensions}")
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._transport = transport or _dashscope_transport

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for start in range(0, len(texts), _MAX_BATCH_SIZE):
            batch = list(texts[start : start + _MAX_BATCH_SIZE])
            embeddings.extend(self._embed_batch(batch))
        return embeddings

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._transport(
                api_key=self._api_key,
                model=self._model,
                input=texts,
                dimension=self._dimensions,
            )
        except Exception as exc:
            if _is_rate_limited(exc):
                raise EmbeddingRateLimited("向量接口限流") from None
            raise EmbeddingUnavailable("向量服务不可用") from None

        _validate_status(response)
        items = _embedding_items(response)
        if len(items) != len(texts):
            raise EmbeddingResponseError("向量响应条数不匹配")
        return [_validate_embedding(item, index, self._dimensions) for index, item in enumerate(items)]


def _dashscope_transport(**kwargs: Any) -> Any:
    import dashscope

    return dashscope.TextEmbedding.call(**kwargs)


def _validate_status(response: Any) -> None:
    status_code = _field(response, "status_code")
    code = _field(response, "code")
    if status_code is not None and status_code != 200:
        if status_code == 429 or _is_rate_limited(code):
            raise EmbeddingRateLimited("向量接口限流")
        if isinstance(status_code, int) and status_code >= 500:
            raise EmbeddingUnavailable("向量服务不可用")
        raise EmbeddingResponseError("向量响应状态码无效")

    if code not in (None, "", 0, 200, "200", "Success", "success"):
        if _is_rate_limited(code):
            raise EmbeddingRateLimited("向量接口限流")
        raise EmbeddingResponseError("向量 API 状态码无效")


def _embedding_items(response: Any) -> Sequence[Any]:
    if _is_vector_sequence(response):
        return response
    if _is_embedding_item_sequence(response):
        return response

    output = _field(response, "output")
    embeddings = _field(output, "embeddings")
    if not _is_embedding_item_sequence(embeddings):
        raise EmbeddingResponseError("向量响应无效")
    return embeddings


def _validate_embedding(item: Any, index: int, dimensions: int) -> list[float]:
    text_index = _field(item, "text_index")
    if text_index is not None and text_index != index:
        raise EmbeddingResponseError("向量响应顺序不匹配")
    vector = _field(item, "embedding") if text_index is not None else item
    if not _is_vector_sequence(vector):
        raise EmbeddingResponseError("向量数据无效")
    if len(vector) != dimensions:
        raise EmbeddingResponseError(f"向量维度必须为 {dimensions}")
    values: list[float] = []
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EmbeddingResponseError("向量元素值无效")
        try:
            normalized = float(value)
        except (OverflowError, TypeError):
            raise EmbeddingResponseError("embedding vector must contain 有限浮点数") from None
        if not math.isfinite(normalized):
            raise EmbeddingResponseError("embedding vector must contain 有限浮点数")
        values.append(normalized)
    return values


def _field(value: Any, name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _is_vector_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and (
        not value or isinstance(value[0], (int, float))
    )


def _is_embedding_item_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and (
        not value or not isinstance(value[0], (int, float))
    )


def _is_rate_limited(value: object) -> bool:
    return "rate" in str(value).lower() or "throttl" in str(value).lower()
