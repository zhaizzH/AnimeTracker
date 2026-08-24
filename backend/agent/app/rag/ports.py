from typing import Any, Protocol, Sequence, runtime_checkable


@runtime_checkable
class SubjectIndex(Protocol):
    def lexical_search(self, expression: str, limit: int) -> Any: ...
    def semantic_search(self, expression: str, vector: Sequence[float], limit: int) -> Any: ...


@runtime_checkable
class EmbeddingPort(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class UserPreferenceProvider(Protocol):
    def load(self, user_id: int, token: str | None) -> tuple[Any | None, bool]: ...
