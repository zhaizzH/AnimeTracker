"""Run a read-only retrieval evaluation against an unpublished index version.

The public Business lexical endpoint intentionally reads the MySQL ACTIVE
release and therefore cannot evaluate a shadow projection while no release is
published.  This module is an internal gate adapter: it reads only the
requested ``search_document.index_version`` rows, queries the matching Redis
Vector Set, and still uses Business batch/evidence APIs for the authority
boundary.  It never inserts or updates ``search_index_release``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
import os
from pathlib import Path
from typing import Any, Literal, Mapping

import redis
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import Engine, text

from app.adapters.business_http import HttpBusinessGateway
from app.adapters.llm.embeddings import DashScopeEmbeddingClient
from app.adapters.mysql.import_records import get_engine
from app.adapters.redis.subject_index import RedisSubjectIndex
from app.rag.retrieval import RagRetrievalService
from app.rag.schemas import RetrievalQuery
from tests.evals.runner import EvalConfig, evaluate_case, load_golden_dataset
from tests.evals.schemas import CaseResult, GoldenCase


SHADOW_REPORT_SCHEMA = "rag-shadow-eval-v1"
EvalStatus = Literal["SHADOW_ONLY", "RELEASE_CANDIDATE"]


class ShadowEvalReport(BaseModel):
    """Gate-compatible evaluation report for shadow or release candidates."""

    model_config = ConfigDict(extra="forbid")

    schemaVersion: str = SHADOW_REPORT_SCHEMA
    status: EvalStatus = "SHADOW_ONLY"
    indexVersion: str = Field(min_length=1)
    profileVersion: str = Field(min_length=1)
    releaseProfileVersion: str = Field(min_length=1)
    activeReleaseCount: int = Field(ge=0)
    datasetStatus: str = Field(min_length=1)
    requiredTotal: int = Field(ge=0)
    requiredPassed: int = Field(ge=0)
    requiredFailed: int = Field(ge=0)
    failures: list[str]
    recall20: float = Field(ge=0, le=1)
    mrr10: float = Field(ge=0, le=1)
    ndcg10: float = Field(ge=0, le=1)
    hardFilterAccuracy: float = Field(ge=0, le=1)
    evidenceCompleteness: float = Field(ge=0, le=1)
    caseResults: list[dict[str, Any]]
    embeddingContract: dict[str, Any]

    @model_validator(mode="after")
    def validate_report_contract(self) -> "ShadowEvalReport":
        if self.requiredTotal != 120:
            raise ValueError("shadow eval 必须包含恰好 120 条 case")
        if self.requiredPassed + self.requiredFailed != self.requiredTotal:
            raise ValueError("requiredPassed 与 requiredFailed 不一致")
        if len(self.caseResults) != self.requiredTotal:
            raise ValueError("shadow eval caseResults 必须与 requiredTotal 一致")
        if self.status == "RELEASE_CANDIDATE" and (
            self.requiredPassed != self.requiredTotal
            or self.requiredFailed != 0
            or self.failures
        ):
            raise ValueError("RELEASE_CANDIDATE 必须是 120/120 且没有失败 case")
        if self.profileVersion != self.releaseProfileVersion:
            raise ValueError("projection profile 与 release profile 不一致")
        contract = self.embeddingContract
        for key in ("provider", "model", "dimensions", "profileVersion", "releaseProfileVersion"):
            if key not in contract or contract[key] in (None, ""):
                raise ValueError(f"embedding contract 缺少 {key}")
        if str(contract["profileVersion"]) != self.releaseProfileVersion:
            raise ValueError("embedding contract profile 与 release profile 不一致")
        if str(contract["releaseProfileVersion"]) != self.releaseProfileVersion:
            raise ValueError("embedding contract release profile 与报告不一致")
        return self


@dataclass(frozen=True)
class ShadowLexicalSearch:
    """Read-only MySQL FULLTEXT adapter for one candidate version."""

    engine: Engine
    index_version: str
    limit: int = 50

    def __call__(self, query: RetrievalQuery, *, token: str | None = None) -> dict[str, Any]:
        del token  # The internal SQL path does not accept user credentials.
        sql, params = build_shadow_sql(query, index_version=self.index_version, limit=self.limit)
        with self.engine.connect() as connection:
            rows = connection.execute(text(sql), params).mappings().all()
            profile = _single_subject_profile(connection, self.index_version)
        return {
            "indexVersion": self.index_version,
            "profileVersion": profile,
            "candidates": [
                {
                    "subjectId": int(row["subject_id"]),
                    "name": row.get("name"),
                    "nameCn": row.get("name_cn"),
                    "lexicalScore": float(row.get("lexical_score") or 0.0),
                }
                for row in rows
            ],
        }


def build_shadow_sql(query: RetrievalQuery, *, index_version: str, limit: int = 50) -> tuple[str, dict[str, Any]]:
    """Build parameterized shadow SQL; no query text becomes SQL syntax."""

    _validate_version(index_version)
    if not 1 <= limit <= 50:
        raise ValueError("limit 必须在 1..50")
    terms = list(query.keywords)
    if not terms and query.semantic_query:
        terms = [query.semantic_query]
    params: dict[str, Any] = {"index_version": index_version, "limit": limit}
    where = [
        "d.entity_kind = 'SUBJECT'",
        "d.index_version = :index_version",
        "d.source_active = 1",
        "s.type = 2",
        "s.nsfw = 0",
        "s.import_status = 1",
    ]
    match_expr = "0.0"
    if terms:
        params["query_text"] = " ".join(str(term) for term in terms)
        match_expr = (
            "MATCH(d.title, d.aliases, d.lexical_text) "
            "AGAINST (:query_text IN BOOLEAN MODE)"
        )
        where.append(f"{match_expr} > 0")
    if query.year_from is not None:
        params["year_from"] = query.year_from
        where.append("s.air_date >= CONCAT(:year_from, '-01-01')")
    if query.year_to is not None:
        params["year_to"] = query.year_to
        where.append("s.air_date <= CONCAT(:year_to, '-12-31')")
    if query.quarter:
        quarter_bounds = {
            "spring": (1, 3),
            "summer": (4, 6),
            "autumn": (7, 9),
            "winter": (10, 12),
        }
        month_from, month_to = quarter_bounds[query.quarter]
        params["quarter_month_from"] = month_from
        params["quarter_month_to"] = month_to
        where.append("MONTH(s.air_date) BETWEEN :quarter_month_from AND :quarter_month_to")
    if query.score_min is not None:
        params["score_min"] = query.score_min
        where.append("s.score >= :score_min")
    if query.rating_total_min is not None:
        params["rating_total_min"] = query.rating_total_min
        where.append("s.rating_total >= :rating_total_min")
    if query.air_status:
        today = date.today().isoformat()
        params["today"] = today
        if query.air_status == "UPCOMING":
            where.append("s.air_date > :today")
        elif query.air_status == "FINISHED":
            where.append("s.air_date IS NOT NULL AND s.air_date <= :today")
            where.append(
                "NOT EXISTS (SELECT 1 FROM episode e WHERE e.subject_id=s.id "
                "AND (e.status='NA' OR e.airdate > :today))"
            )
        elif query.air_status == "AIRING":
            where.append("s.air_date IS NOT NULL AND s.air_date <= :today")
            where.append(
                "EXISTS (SELECT 1 FROM episode e WHERE e.subject_id=s.id "
                "AND (e.status='NA' OR e.airdate > :today))"
            )
    for offset, subject_id in enumerate(query.exclude_subject_ids):
        key = f"exclude_{offset}"
        params[key] = int(subject_id)
        where.append(f"s.id <> :{key}")
    for offset, tag in enumerate(query.meta_tags):
        key = f"tag_{offset}"
        params[key] = str(tag)
        where.append(
            "(EXISTS (SELECT 1 FROM subject_tag st WHERE st.subject_id=s.id AND st.name=:{key}) "
            "OR EXISTS (SELECT 1 FROM subject_meta_tag smt WHERE smt.subject_id=s.id "
            "AND smt.name=:{key} AND smt.source_active=1))".format(key=key)
        )
    if terms:
        order_by = "lexical_score DESC, s.score DESC, s.rating_total DESC, s.id ASC"
    else:
        # Keep filter-only cases identical to the golden snapshot generator's
        # deterministic subject ordering.
        order_by = "s.score DESC, s.rating_total DESC, s.id ASC"
    sql = (
        "SELECT d.entity_id AS subject_id, s.name, s.name_cn, "
        f"{match_expr} AS lexical_score "
        "FROM search_document d INNER JOIN subject s ON s.id=d.entity_id "
        "WHERE " + " AND ".join(where) +
        f" ORDER BY {order_by} LIMIT :limit"
    )
    return sql, params


def run_shadow_eval(
    *,
    engine: Engine,
    redis_client: Any,
    business_url: str,
    embedding_client: Any,
    dataset_path: str | Path,
    index_version: str,
    release_profile_version: str,
    token: str | None = None,
    status: EvalStatus = "SHADOW_ONLY",
) -> ShadowEvalReport:
    """Evaluate exactly 120 cases without requiring an ACTIVE release.

    ``RELEASE_CANDIDATE`` is deliberately available only for a clean 120/120
    result.  The caller still has to produce the remaining gate reports before
    activating the MySQL release.
    """

    _validate_version(index_version)
    dataset = load_golden_dataset(dataset_path)
    cases = dataset["cases"]
    metadata = dataset["metadata"]
    if len(cases) != 120:
        raise ValueError(f"shadow gate 要求恰好 120 条 case，当前为 {len(cases)}")
    dataset_version = str(metadata.get("index_version") or "")
    if dataset_version and dataset_version != index_version:
        raise ValueError(f"dataset indexVersion={dataset_version} 与候选版本={index_version} 不一致")

    _validate_version(release_profile_version)
    dataset_profile = str(metadata.get("profile_version") or "")
    if not dataset_profile:
        raise ValueError("dataset 缺少 profile_version")
    with engine.connect() as connection:
        active_count = int(connection.execute(text("SELECT COUNT(*) FROM search_index_release WHERE status='ACTIVE'")).scalar() or 0)
        projection_profile = _single_subject_profile(connection, index_version)
    if projection_profile != dataset_profile:
        raise ValueError(
            f"dataset profile_version={dataset_profile} 与 SUBJECT projection={projection_profile} 不一致"
        )
    if release_profile_version != projection_profile:
        raise ValueError(
            f"release profile_version={release_profile_version} 与 SUBJECT projection={projection_profile} 不一致"
        )
    gateway = HttpBusinessGateway(business_url)
    service = RagRetrievalService(
        RedisSubjectIndex(redis_client),
        embedding_client,
        authority_lookup=gateway.batch_subjects,
        business_search=lambda _query, *, token: {"items": []},
        evidence_lookup=gateway.batch_evidence,
        resolve_evidence_lookup=gateway.resolve_evidence,
        lexical_search=ShadowLexicalSearch(engine, index_version),
    )
    results: list[CaseResult] = []
    failures: list[str] = []
    case_details: list[dict[str, Any]] = []
    total_candidates = 0
    evidence_candidates = 0
    for case in cases:
        query = RetrievalQuery.model_validate(case.query)
        result = service.retrieve(query, token=token)
        retrieved = [item.subject_id for item in result.items]
        candidate_evidence_complete = all(
            isinstance(item.evidence, Mapping) and bool(item.evidence)
            for item in result.items
        )
        total_candidates += len(result.items)
        evidence_candidates += sum(
            1 for item in result.items if isinstance(item.evidence, Mapping) and bool(item.evidence)
        )
        case_result = evaluate_case(case, lambda _query, ids=retrieved: ids, config=EvalConfig(k=20))
        results.append(case_result)
        passed = result.available and candidate_evidence_complete and _required_case_passed(case, retrieved)
        if not passed:
            failures.append(case.id)
        case_details.append({
            **case_result.model_dump(),
            "available": result.available,
            "reason": result.reason,
            "evidenceComplete": candidate_evidence_complete,
            "passed": passed,
        })
    total = len(results)
    report = {
        "schemaVersion": SHADOW_REPORT_SCHEMA,
        "status": status,
        "indexVersion": index_version,
        "profileVersion": projection_profile,
        "releaseProfileVersion": release_profile_version,
        "activeReleaseCount": active_count,
        "datasetStatus": str(metadata.get("status") or "UNKNOWN"),
        "requiredTotal": total,
        "requiredPassed": total - len(failures),
        "requiredFailed": len(failures),
        "failures": failures,
        "recall20": sum(item.recall for item in results) / total,
        "mrr10": sum(item.rr for item in results) / total,
        "ndcg10": sum(item.ndcg for item in results) / total,
        "hardFilterAccuracy": sum(1 for item in results if item.all_must_contain_hit) / total,
        "evidenceCompleteness": evidence_candidates / total_candidates if total_candidates else 1.0,
        "caseResults": case_details,
        "embeddingContract": {
            "provider": "dashscope",
            "model": "text-embedding-v4",
            "dimensions": 1024,
            "profileVersion": projection_profile,
            "releaseProfileVersion": release_profile_version,
        },
    }
    return ShadowEvalReport.model_validate(report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-version", required=True)
    parser.add_argument("--dataset", type=Path, default=Path(__file__).parents[2] / "tests/evals/golden_cases.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release-profile-version", required=True)
    parser.add_argument(
        "--status",
        choices=("SHADOW_ONLY", "RELEASE_CANDIDATE"),
        default="SHADOW_ONLY",
        help="报告状态；RELEASE_CANDIDATE 仅在 120/120 通过时有效",
    )
    parser.add_argument("--business-url", default=os.getenv("BUSINESS_BASE_URL", "http://127.0.0.1:8080"))
    args = parser.parse_args(argv)
    load_dotenv()
    engine = get_engine(
        os.getenv("DB_HOST", "127.0.0.1"), int(os.getenv("DB_PORT", "3306")),
        os.getenv("DB_USER", "root"), os.getenv("DB_PASSWORD", ""), os.getenv("DB_NAME", "anime_tracker"),
    )
    client = redis.Redis.from_url(os.getenv("RAG_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    report = run_shadow_eval(
        engine=engine,
        redis_client=client,
        business_url=args.business_url,
        embedding_client=DashScopeEmbeddingClient(os.getenv("DASHSCOPE_API_KEY", "")),
        dataset_path=args.dataset,
        index_version=args.index_version,
        release_profile_version=args.release_profile_version,
        status=args.status,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.model_dump().items() if key != "caseResults"}, ensure_ascii=False, indent=2))
    return 0 if report.requiredFailed == 0 else 1


def _validate_version(value: str) -> None:
    if not isinstance(value, str) or not value or ":" in value or any(char.isspace() for char in value):
        raise ValueError("index_version 无效")


def _single_subject_profile(connection: Any, index_version: str) -> str:
    rows = connection.execute(
        text(
            "SELECT DISTINCT profile_version FROM search_document "
            "WHERE entity_kind='SUBJECT' AND index_version=:version"
        ),
        {"version": index_version},
    ).scalars().all()
    profiles = {str(value).strip() for value in rows if value is not None and str(value).strip()}
    if not profiles:
        raise ValueError(f"候选版本没有 SUBJECT projection: {index_version}")
    if len(profiles) != 1:
        raise ValueError(f"候选版本包含多个 SUBJECT profile_version: {sorted(profiles)}")
    return next(iter(profiles))


def _required_case_passed(case: GoldenCase, retrieved_ids: list[int]) -> bool:
    """Evaluate the hard requirement without confusing it with ranking gold.

    ``expected_subject_ids`` is ordered relevance data for Recall/MRR/nDCG;
    ``must_contain_all`` is the explicit pass/fail set.  Cases without an
    expected result are strict no-result checks.
    """
    retrieved = set(retrieved_ids)
    required = set(case.expectation.must_contain_all)
    if required:
        return required.issubset(retrieved)
    expected = set(case.expectation.expected_subject_ids)
    return expected.issubset(retrieved) if expected else not retrieved


if __name__ == "__main__":
    raise SystemExit(main())
