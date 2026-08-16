"""30+ case 数据集契约与离线门禁：所有 required 确定性 case 必须离线 PASS。"""

import pytest

from evals.runner import DEFAULT_CASE_PATHS, run_offline
from evals.schema import load_cases

# 写能力工具：命中即视为写操作 case，必须声明 forbiddenTools 或 businessCalls
_WRITE_TOOLS = {
    "preview_weekly_collection_progress",
    "execute_weekly_collection_progress",
    "cancel_weekly_collection_progress",
    "preview_add_to_wishlist",
    "execute_add_to_wishlist",
    "cancel_add_to_wishlist",
}


def test_required_dataset_is_complete():
    cases = load_cases(DEFAULT_CASE_PATHS)
    assert len(cases) >= 30
    assert all(case.required for case in cases)
    assert {c.category for c in cases} >= {
        "routing", "recommendation", "collection_progress", "wishlist", "safety",
    }


def test_case_ids_are_globally_unique():
    cases = load_cases(DEFAULT_CASE_PATHS)
    assert len({c.id for c in cases}) == len(cases)


def test_write_capability_cases_declare_forbidden_or_business():
    cases = load_cases(DEFAULT_CASE_PATHS)
    for case in cases:
        used_write = set(case.expect.calledTools or []) & _WRITE_TOOLS
        is_write_category = case.category in {"collection_progress", "wishlist"}
        if not (used_write or is_write_category):
            continue
        assert case.expect.forbiddenTools or case.expect.businessCalls is not None, (
            f"case {case.id} 是写能力 case, 必须声明 forbiddenTools 或 businessCalls"
        )


def test_all_required_cases_pass_offline():
    cases = load_cases(DEFAULT_CASE_PATHS)
    report = run_offline(cases)
    assert report.failed == 0, "\n" + report.render()


def test_report_render_does_not_leak_sensitive_content():
    cases = load_cases(DEFAULT_CASE_PATHS)
    report = run_offline(cases)
    rendered = report.render()
    for token in ("Bearer", "eyJ", "eval-key", "tok"):
        assert token not in rendered, f"报告泄露敏感内容: {token}"
