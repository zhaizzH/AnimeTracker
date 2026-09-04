from enum import Enum
from typing import Protocol, runtime_checkable


class AgentChatModelSlot(str, Enum):
    CLIENT_ROUTE = "client_route"
    CLIENT_SEARCH = "client_search"
    CLIENT_DISCOVER = "client_discover"
    CLIENT_RECOMMEND = "client_recommend"
    ADMIN_NODE = "admin_node"


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
    def batch_evidence(
        self,
        subject_ids: list[int],
        *,
        token: str | None,
    ) -> dict | list: ...
    def resolve_evidence(
        self,
        entity_type: str,
        entity_ids: list[int],
        *,
        token: str | None,
    ) -> dict | list: ...


@runtime_checkable
class AgentLlmFactoryPort(Protocol):
    @property
    def provider(self) -> str: ...
    def create(self, slot: AgentChatModelSlot, *, temperature: float | None = None): ...
