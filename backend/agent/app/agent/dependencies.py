from __future__ import annotations

from dataclasses import dataclass

from app.agent.ports import BusinessGateway
from app.rag.use_case import RetrieveSubjectsUseCase


@dataclass(frozen=True)
class AgentDependencies:
    business: BusinessGateway
    retrieval: RetrieveSubjectsUseCase
