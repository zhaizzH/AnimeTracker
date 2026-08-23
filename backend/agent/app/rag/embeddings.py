from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol


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


class EmbeddingClient(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...


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
            raise ValueError(f"unsupported embedding model: {model}")
        if dimensions != EMBEDDING_DIMENSIONS:
            raise ValueError(f"unsupported embedding dimensions: {dimensions}")
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
                raise EmbeddingRateLimited("embedding rate limited") from None
            raise EmbeddingUnavailable("embedding unavailable") from None

        _validate_status(response)
        items = _embedding_items(response)
        if len(items) != len(texts):
            raise EmbeddingResponseError("embedding response 条数不匹配")
        return [_validate_embedding(item, index, self._dimensions) for index, item in enumerate(items)]


def _dashscope_transport(**kwargs: Any) -> Any:
    import dashscope

    return dashscope.TextEmbedding.call(**kwargs)


def _validate_status(response: Any) -> None:
    status_code = _field(response, "status_code")
    code = _field(response, "code")
    if status_code is not None and status_code != 200:
        if status_code == 429 or _is_rate_limited(code):
            raise EmbeddingRateLimited("embedding rate limited")
        if isinstance(status_code, int) and status_code >= 500:
            raise EmbeddingUnavailable("embedding unavailable")
        raise EmbeddingResponseError("embedding response status invalid")

    if code not in (None, "", 0, 200, "200", "Success", "success"):
        if _is_rate_limited(code):
            raise EmbeddingRateLimited("embedding rate limited")
        raise EmbeddingResponseError("embedding API status invalid")


def _embedding_items(response: Any) -> Sequence[Any]:
    if _is_vector_sequence(response):
        return response
    if _is_embedding_item_sequence(response):
        return response

    output = _field(response, "output")
    embeddings = _field(output, "embeddings")
    if not _is_embedding_item_sequence(embeddings):
        raise EmbeddingResponseError("embedding response invalid")
    return embeddings


def _validate_embedding(item: Any, index: int, dimensions: int) -> list[float]:
    text_index = _field(item, "text_index")
    if text_index is not None and text_index != index:
        raise EmbeddingResponseError("embedding response 顺序不匹配")
    vector = _field(item, "embedding") if text_index is not None else item
    if not _is_vector_sequence(vector):
        raise EmbeddingResponseError("embedding vector invalid")
    if len(vector) != dimensions:
        raise EmbeddingResponseError(f"embedding dimension must be {dimensions}")
    values: list[float] = []
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EmbeddingResponseError("embedding vector value invalid")
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
