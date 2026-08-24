from typing import Protocol, runtime_checkable


@runtime_checkable
class BusinessGateway(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        token: str | None = None,
        json_body: dict | None = None,
    ) -> dict | list: ...
    def batch_subjects(
        self,
        subject_ids: list[int],
        *,
        token: str | None,
        exclude_collected: bool,
    ) -> dict | list: ...
    def search_subjects(
        self,
        query: str,
        *,
        token: str | None,
        size: int = 15,
    ) -> dict | list: ...
