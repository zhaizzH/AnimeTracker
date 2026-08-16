"""确定性行为断言：evaluate(case, actual) -> list[str]，空列表 = 通过。

纯函数，不触碰网络/IO。失败消息只含工具名/路由目标/挂起动作类型/pending 操作/
Business 调用 (method, path)/错误类别，绝不输出工具参数、用户输入或完整回答。
"""

from dataclasses import dataclass, field
from typing import Any

from evals.schema import EvalCase


@dataclass
class BehaviorSnapshot:
    """一次运行的捕获行为快照。"""

    routeTarget: str | None = None
    calledTools: list[str] = field(default_factory=list)
    toolArguments: dict[str, dict[str, Any]] = field(default_factory=dict)
    pendingAction: Any = None  # PendingActionEvent | None
    businessCalls: list[tuple[str, str]] = field(default_factory=list)
    answer: str = ""
    errorCategory: str | None = None


def _subject_ids(event: Any) -> list[int]:
    action = getattr(event, "action", None)
    if action is None:
        return []
    return [item.subject_id for item in action.items]


def evaluate(case: EvalCase, actual: BehaviorSnapshot) -> list[str]:
    failures: list[str] = []
    exp = case.expect

    if exp.routeTarget is not None and actual.routeTarget != exp.routeTarget:
        # 错误路径下路由未产生，routeTarget 让位给已匹配的 errorCategory
        if not (exp.errorCategory is not None and actual.errorCategory == exp.errorCategory):
            failures.append(f"routeTarget 期望 {exp.routeTarget!r}, 实际 {actual.routeTarget!r}")

    if exp.calledTools is not None and actual.calledTools != list(exp.calledTools):
        failures.append(f"calledTools 期望 {list(exp.calledTools)}, 实际 {actual.calledTools}")

    for name in exp.forbiddenTools:
        if name in actual.calledTools:
            failures.append(f"forbiddenTools: 工具 {name} 被调用")

    for name in exp.toolArguments or {}:
        if actual.toolArguments.get(name) != (exp.toolArguments or {}).get(name):
            failures.append(f"toolArguments[{name}] 不匹配")

    if exp.pendingActionType is not None:
        action = getattr(actual.pendingAction, "action", None)
        got = getattr(action, "type", None) if action is not None else None
        if got != exp.pendingActionType:
            failures.append(f"pendingActionType 期望 {exp.pendingActionType!r}, 实际 {got!r}")

    if exp.pendingActionOperation is not None:
        got = getattr(actual.pendingAction, "operation", None)
        if got != exp.pendingActionOperation:
            failures.append(f"pendingActionOperation 期望 {exp.pendingActionOperation!r}, 实际 {got!r}")

    if exp.pendingSubjectIds is not None:
        got = _subject_ids(actual.pendingAction)
        if got != list(exp.pendingSubjectIds):
            failures.append(f"pendingSubjectIds 期望 {list(exp.pendingSubjectIds)}, 实际 {got}")

    if exp.businessCalls is not None:
        expected = [tuple(c) for c in exp.businessCalls]
        if actual.businessCalls != expected:
            failures.append(f"businessCalls 期望 {expected}, 实际 {actual.businessCalls}")

    if exp.answerContainsAny:
        answer = actual.answer or ""
        if not any(s in answer for s in exp.answerContainsAny):
            failures.append(f"answer 未包含期望子串之一: {exp.answerContainsAny}")

    for s in exp.answerExcludes:
        if s in (actual.answer or ""):
            failures.append(f"answer 包含禁止子串: {s!r}")

    if exp.errorCategory is not None and actual.errorCategory != exp.errorCategory:
        failures.append(f"errorCategory 期望 {exp.errorCategory!r}, 实际 {actual.errorCategory!r}")

    return failures
