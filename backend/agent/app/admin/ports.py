from typing import Protocol, runtime_checkable


@runtime_checkable
class ModelConfigRepository(Protocol):
    def get(self) -> dict | None: ...
    def set(self, config: dict) -> None: ...


@runtime_checkable
class PromptRepository(Protocol):
    def list_keys(self) -> tuple[str, ...]: ...
    def get(self, key: str, fallback_path: str | None = None) -> str: ...
    def set(self, key: str, content: str) -> None: ...
    def reset(self, key: str) -> str: ...


@runtime_checkable
class JobLauncher(Protocol):
    def start_import(
        self,
        mode: str,
        *,
        key: str | None = None,
        since: str | None = None,
        workers: int | None = None,
    ) -> None: ...
