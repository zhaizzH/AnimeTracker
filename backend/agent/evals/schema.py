"""离线评测数据集 schema：严格 Pydantic 校验，字段白名单。

隐私红线：case 只描述行为断言，不保存用户输入、JWT、API key、完整回答。
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class EvalExpectation(BaseModel):
    """单个 case 的确定性行为断言。字段与 spec 固定列表一致，全部可选。"""

    model_config = ConfigDict(extra="forbid")

    routeTarget: str | None = None
    calledTools: list[str] | None = None
    forbiddenTools: list[str] = Field(default_factory=list)
    toolArguments: dict[str, dict[str, Any]] = Field(default_factory=dict)
    pendingActionType: str | None = None
    pendingActionOperation: Literal["SET", "REPLACE", "CLEAR"] | None = None
    pendingSubjectIds: list[int] | None = None
    # businessCalls 是精确序列断言：(method, path) 按发生顺序
    businessCalls: list[list[str]] | None = None
    answerContainsAny: list[str] = Field(default_factory=list)
    answerExcludes: list[str] = Field(default_factory=list)
    errorCategory: str | None = None


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    category: str = ""
    input: str
    required: bool = True
    state: dict[str, Any] = Field(default_factory=dict)
    fixtures: dict[str, Any] = Field(default_factory=dict)
    expect: EvalExpectation


def load_cases(paths: list[str | Path]) -> list[EvalCase]:
    """读取并校验 YAML 数据集；拒绝重复 id。校验错误带 case id 与文件定位。"""
    seen: set[str] = set()
    cases: list[EvalCase] = []
    for path in paths:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if raw is None:
            continue
        items = raw if isinstance(raw, list) else [raw]
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"{path}: 顶层条目必须是 mapping")
            cid = item.get("id")
            try:
                case = EvalCase.model_validate(item)
            except ValidationError as exc:
                raise ValueError(f"case {cid!r} in {path} 校验失败: {exc}") from exc
            if case.id in seen:
                raise ValueError(f"重复的 case id: {case.id}")
            seen.add(case.id)
            cases.append(case)
    return cases
