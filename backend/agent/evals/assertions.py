from __future__ import annotations

from .schema import EvalCase


def case_failure(case: EvalCase, ranked: list[int], fallback: str | None, error_type: str | None) -> str | None:
    if case.expectedFallback is not None and fallback != case.expectedFallback:
        return f"{case.id}: expected fallback {case.expectedFallback}"
    if case.expectedErrorType is not None and error_type != case.expectedErrorType:
        return f"{case.id}: expected error {case.expectedErrorType}"
    if case.expectedSubjectIds and not set(case.expectedSubjectIds).intersection(ranked):
        return f"{case.id}: expected subject missing"
    if set(case.forbiddenSubjectIds).intersection(ranked):
        return f"{case.id}: forbidden subject returned"
    return None
