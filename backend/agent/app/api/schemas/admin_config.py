from enum import Enum

from pydantic import BaseModel, Field


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


class FieldSource(str, Enum):
    """单字段取值的来源：Redis 显式覆盖，或回退 Settings(.env) 默认。"""

    default = "default"
    override = "override"


class ModelConfigSources(BaseModel):
    model: FieldSource
    modelRoute: FieldSource
    temperature: FieldSource
    maxTokens: FieldSource
    thinkingBudget: FieldSource
    reasoningEffort: FieldSource


class ModelConfigView(ModelConfig):
    """GET 响应：生效值 + 逐字段来源。

    请求侧仍用 ``ModelConfig``——来源是只读派生信息，不可设置，故不进入入参。
    ``alias`` 而非 ``serialization_alias``：service 构造时传入的就是 ``_sources``，
    需要输入侧也认同名；FastAPI 默认按 alias 序列化，线上即为 ``_sources``。
    """

    sources: ModelConfigSources = Field(alias="_sources")
