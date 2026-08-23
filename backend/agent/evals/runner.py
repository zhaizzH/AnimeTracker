from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
import json
from pathlib import Path
import sys

import yaml
from pydantic import ValidationError

from .adapters import FixtureSubject, OfflineAdapter
from .assertions import case_failure
from .metrics import ndcg_at_k, recall_at_k, reciprocal_rank
from .schema import EvalCase, EvalReport


_ROOT = Path(__file__).resolve().parent
DEFAULT_RAG_CASE_PATHS = tuple(_ROOT / "cases" / name for name in (
    "title_alias.yaml", "semantic.yaml", "filters.yaml", "personalization.yaml", "safety_failure.yaml",
))
DEFAULT_SUBJECT_PATH = _ROOT / "fixtures" / "subjects.yaml"


class DatasetError(ValueError):
    pass


def _documents(path: Path) -> list[dict]:
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise DatasetError(f"invalid dataset: {path}") from error
    if isinstance(parsed, dict):
        parsed = parsed.get("cases", parsed.get("subjects"))
    if not isinstance(parsed, list) or not all(isinstance(item, dict) for item in parsed):
        raise DatasetError(f"dataset must be a list: {path}")
    return parsed


def load_cases(paths: Sequence[Path] = DEFAULT_RAG_CASE_PATHS) -> list[EvalCase]:
    try:
        cases = [EvalCase.model_validate(item) for path in paths for item in _documents(path)]
    except ValidationError as error:
        raise DatasetError("invalid eval case") from error
    if len({case.id for case in cases}) != len(cases):
        raise DatasetError("eval case ids must be unique")
    return cases


def load_subjects(path: Path = DEFAULT_SUBJECT_PATH) -> list[FixtureSubject]:
    try:
        return [FixtureSubject(
            subject_id=int(item["subjectId"]), title=str(item["title"]),
            aliases=tuple(str(alias) for alias in item.get("aliases", [])), text=str(item["text"]),
            year=int(item["year"]), quarter=int(item["quarter"]), score=float(item["score"]),
            tags=tuple(str(tag) for tag in item.get("tags", [])),
            preference_states=tuple(str(state) for state in item.get("preferenceStates", [])),
            excluded_states=tuple(str(state) for state in item.get("excludedStates", [])),
            nsfw=bool(item.get("nsfw", False)), subject_type=int(item.get("type", 2)),
        ) for item in _documents(path)]
    except (KeyError, TypeError, ValueError) as error:
        raise DatasetError("invalid subject fixture") from error


def run_offline(paths: Sequence[Path] = DEFAULT_RAG_CASE_PATHS) -> EvalReport:
    cases = load_cases(paths)
    adapter = OfflineAdapter(load_subjects())
    failures: list[str] = []
    ranked_cases: list[tuple[EvalCase, list[int], str | None]] = []
    returned = valid = 0
    valid_ids = {subject.subject_id for subject in load_subjects()}
    for case in cases:
        result = adapter.evaluate(case)
        failure = case_failure(case, result.ranked, result.fallback, result.error_type)
        if failure:
            failures.append(failure)
        ranked_cases.append((case, result.ranked, failure))
        returned += len(result.ranked)
        valid += sum(subject_id in valid_ids for subject_id in result.ranked)
    relevant = [(case, ranked) for case, ranked, _ in ranked_cases if case.expectedSubjectIds]
    denominator = len(relevant) or 1
    return EvalReport(
        required_total=sum(case.required for case in cases),
        required_passed=sum(case.required and failure is None for case, _, failure in ranked_cases),
        mrr_at_10=sum(reciprocal_rank(set(case.expectedSubjectIds), ranked) for case, ranked in relevant) / denominator,
        recall_at_20=sum(recall_at_k(set(case.expectedSubjectIds), ranked) for case, ranked in relevant) / denominator,
        ndcg_at_10=sum(ndcg_at_k(set(case.expectedSubjectIds), ranked) for case, ranked in relevant) / denominator,
        valid_subject_id_ratio=valid / returned if returned else 1.0,
        failures=tuple(failures),
    )


def _passes_gate(report: EvalReport) -> bool:
    return not report.failures and report.required_passed == report.required_total and report.mrr_at_10 >= .90 and report.recall_at_20 >= .85 and report.ndcg_at_10 >= .75


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic offline RAG evaluation")
    parser.add_argument("--mode", choices=("offline",), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--index-version")
    args = parser.parse_args(argv)
    try:
        report = run_offline()
    except DatasetError as error:
        print(str(error), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump()
    if args.index_version:
        payload["indexVersion"] = args.index_version
    payload["embeddingContract"] = {"provider": "dashscope", "model": "text-embedding-v4", "dimensions": 1024, "profileVersion": "subject-profile-v1"}
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    args.output.write_text(content, encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0 if _passes_gate(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
