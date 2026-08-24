from __future__ import annotations

from dataclasses import dataclass

from app.admin.import_service import ImportService
from app.admin.ports import PromptRepository
from app.agent.ports import AgentLlmFactoryPort, BusinessGateway
from app.rag.use_case import RetrieveSubjectsUseCase


@dataclass(frozen=True)
class AgentDependencies:
    business: BusinessGateway
    retrieval: RetrieveSubjectsUseCase
    llm_factory: AgentLlmFactoryPort
    prompt_repository: PromptRepository
    import_service: ImportService
