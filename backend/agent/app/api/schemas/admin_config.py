from pydantic import BaseModel


class PromptOut(BaseModel):
    promptKey: str
    promptContent: str


class PromptUpdateRequest(BaseModel):
    promptContent: str


class ModelConfig(BaseModel):
    model: str | None = None
    modelRoute: str | None = None
    temperature: float | None = None
    maxTokens: int | None = None
    thinkingBudget: int | None = None
    reasoningEffort: str | None = None
