"""从真实 MySQL 事实库生成可追溯的 120-case 数据集。

该脚本只执行 SELECT，不激活 release、不写入 MySQL/Redis，也不会把
“定义集”误标成真实检索评测通过。生成结果包含数据库快照摘要、SQL
证据模板、结果摘要和统一的 index/profile version，供 Phase 8 gate 在
真实服务可用后重放。

Usage::

    python -m tests.evals.generate_golden_cases \
        --output tests/evals/golden_cases.json
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text


INDEX_VERSION = os.getenv("RAG_INDEX_VERSION", "v1")
PROFILE_VERSION = os.getenv("RAG_PROFILE_VERSION", "subject-profile-v1")


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, tuple):
        return list(value)
    return value


def _safe_term(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= 48 and not any(
        ord(char) < 0x20 for char in value
    )


def _id_list(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(item) for item in value.split(",") if item]


def _hash_ids(ids: Iterable[int]) -> str:
    canonical = ",".join(str(int(value)) for value in ids)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _rank(ids: Iterable[int], subjects: dict[int, dict[str, Any]]) -> list[int]:
    return sorted(
        {int(value) for value in ids},
        key=lambda value: (
            -float(subjects[value].get("score") or 0),
            -int(subjects[value].get("rating_total") or 0),
            value,
        ),
    )


def _connection() -> Engine:
    load_dotenv(Path(__file__).parents[2] / ".env")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_NAME", "anime_tracker")
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    return create_engine(url)


def _subject_query(connection: Any, where: str, params: dict[str, Any]) -> list[int]:
    rows = connection.execute(
        text(
            "SELECT s.id FROM subject s "
            "WHERE s.type=2 AND s.nsfw=0 AND s.import_status=1 AND " + where + " "
            "ORDER BY s.score DESC, s.rating_total DESC, s.id ASC"
        ),
        params,
    ).scalars().all()
    return [int(value) for value in rows]


def _sql_case(
    *,
    case_id: str,
    category: str,
    description: str,
    query: dict[str, Any],
    result_ids: list[int],
    subjects: dict[int, dict[str, Any]],
    snapshot_id: str,
    captured_at: str,
    sql_template: str,
    parameters: dict[str, Any],
    source_tables: list[str],
    hard_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ranked = _rank(result_ids, subjects)
    expected = ranked[:10]
    return {
        "id": case_id,
        "category": category,
        "description": description,
        "query": query,
        "expectation": {
            "expected_subject_ids": expected,
            "must_contain_all": expected[: min(3, len(expected))],
            "hard_filters": hard_filters or {},
        },
        "trace": {
            "snapshot_id": snapshot_id,
            "captured_at": captured_at,
            "evidence_id": f"{snapshot_id}:{case_id}",
            "sql_template": sql_template,
            "parameters": {key: _json_value(value) for key, value in parameters.items()},
            "source_tables": source_tables,
            "result_count": len(result_ids),
            "result_ids_hash": _hash_ids(result_ids),
            "index_version": INDEX_VERSION,
            "profile_version": PROFILE_VERSION,
        },
    }


def _title_cases(
    connection: Any,
    subjects: dict[int, dict[str, Any]],
    aliases: list[dict[str, Any]],
    snapshot_id: str,
    captured_at: str,
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    named = [row for row in subjects.values() if _safe_term(row.get("name"))]
    for index, row in enumerate(named[:20], 1):
        subject_id = int(row["id"])
        term = str(row["name"])
        result_ids = _subject_query(
            connection,
            "(s.name=:term OR s.name_cn=:term)",
            {"term": term},
        )
        if not result_ids:
            continue
        cases.append(
            _sql_case(
                case_id=f"title_name_{index:02d}",
                category="title_alias",
                description="事实快照中的作品原名精确匹配",
                query={"keywords": [term]},
                result_ids=result_ids,
                subjects=subjects,
                snapshot_id=snapshot_id,
                captured_at=captured_at,
                sql_template="subject.title_exact.v1",
                parameters={"subject_id": subject_id, "term": term},
                source_tables=["subject"],
            )
        )
    for index, row in enumerate(aliases[:10], 1):
        subject_id = int(row["subject_id"])
        term = str(row["name"])
        result_ids = _subject_query(
            connection,
            "EXISTS (SELECT 1 FROM subject_alias sa "
            "WHERE sa.subject_id=s.id AND sa.name=:term AND sa.source_active=1)",
            {"term": term},
        )
        if not result_ids:
            continue
        cases.append(
            _sql_case(
                case_id=f"title_alias_{index:02d}",
                category="title_alias",
                description="事实快照中的 active 别名匹配",
                query={"keywords": [term]},
                result_ids=result_ids,
                subjects=subjects,
                snapshot_id=snapshot_id,
                captured_at=captured_at,
                sql_template="subject.alias_exact.v1",
                parameters={"subject_id": subject_id, "term": term},
                source_tables=["subject", "subject_alias"],
            )
        )
    return cases


def _structured_cases(connection: Any, subjects: dict[int, dict[str, Any]], tags: list[dict[str, Any]], snapshot_id: str, captured_at: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    def add(case_id: str, query: dict[str, Any], where: str, params: dict[str, Any], template: str, tables: list[str], description: str) -> None:
        result_ids = _subject_query(connection, where, params)
        if not result_ids:
            return
        cases.append(_sql_case(case_id=case_id, category="structured_filter", description=description, query=query, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template=template, parameters=params, source_tables=tables))

    for index, row in enumerate(tags[:5], 1):
        tag = str(row["name"])
        add(f"filter_tag_{index:02d}", {"meta_tags": [tag]}, "EXISTS (SELECT 1 FROM subject_meta_tag smt WHERE smt.subject_id=s.id AND smt.name=:tag AND smt.source_active=1)", {"tag": tag}, "subject.meta_tag.v1", ["subject", "subject_meta_tag"], "active 元标签过滤")
    for index, row in enumerate(tags[5:10], 6):
        tag = str(row["name"])
        add(f"filter_tag_{index:02d}", {"meta_tags": [tag], "score_min": 0}, "s.score >= :score AND EXISTS (SELECT 1 FROM subject_meta_tag smt WHERE smt.subject_id=s.id AND smt.name=:tag AND smt.source_active=1)", {"tag": tag, "score": 0}, "subject.meta_tag_score.v1", ["subject", "subject_meta_tag"], "元标签与评分下限组合过滤")
    for index, row in enumerate(tags[10:15], 1):
        tag = str(row["name"])
        add(f"filter_tag_year_{index:02d}", {"year_from": 2026, "year_to": 2026, "meta_tags": [tag]}, "YEAR(s.air_date)=:year AND EXISTS (SELECT 1 FROM subject_meta_tag smt WHERE smt.subject_id=s.id AND smt.name=:tag AND smt.source_active=1)", {"year": 2026, "tag": tag}, "subject.year_meta_tag.v1", ["subject", "subject_meta_tag"], "年份与元标签组合过滤")

    score_values = sorted({float(row["score"]) for row in subjects.values() if row.get("score") is not None}, reverse=True)
    score_values = [value for value in score_values if 2 <= len(_subject_query(connection, "s.score >= :value", {"value": value})) <= 40][:5]
    for index, value in enumerate(score_values, 1):
        add(f"filter_score_{index:02d}", {"score_min": value}, "s.score >= :value", {"value": value}, "subject.score_min.v1", ["subject"], "评分下限过滤")

    rating_values = sorted({int(row["rating_total"]) for row in subjects.values() if row.get("rating_total") is not None}, reverse=True)
    rating_values = [value for value in rating_values if 2 <= len(_subject_query(connection, "s.rating_total >= :value", {"value": value})) <= 40][:5]
    for index, value in enumerate(rating_values, 1):
        add(f"filter_rating_{index:02d}", {"rating_total_min": value}, "s.rating_total >= :value", {"value": value}, "subject.rating_total_min.v1", ["subject"], "评分人数下限过滤")

    status_sql = "CASE WHEN s.air_date IS NULL THEN 'UNKNOWN' WHEN s.air_date > CURDATE() THEN 'UPCOMING' WHEN EXISTS (SELECT 1 FROM episode e WHERE e.subject_id=s.id AND e.status='NA') THEN 'AIRING' ELSE 'FINISHED' END = :status"
    for index, status in enumerate(("UPCOMING", "AIRING", "FINISHED"), 1):
        add(f"filter_air_status_{index:02d}", {"air_status": status}, status_sql, {"status": status}, "subject.air_status.v1", ["subject", "episode"], "播出状态过滤")

    for index, row in enumerate(tags[15:22], 1):
        tag = str(row["name"])
        add(f"filter_quarter_tag_{index:02d}", {"year_from": 2026, "year_to": 2026, "quarter": "autumn", "meta_tags": [tag]}, "YEAR(s.air_date)=:year AND QUARTER(s.air_date)=:quarter AND EXISTS (SELECT 1 FROM subject_meta_tag smt WHERE smt.subject_id=s.id AND smt.name=:tag AND smt.source_active=1)", {"year": 2026, "quarter": 3, "tag": tag}, "subject.year_quarter_meta_tag.v1", ["subject", "subject_meta_tag"], "年份季度与元标签组合过滤")

    add("filter_year_01", {"year_from": 2026, "year_to": 2026}, "YEAR(s.air_date)=:year", {"year": 2026}, "subject.year.v1", ["subject"], "年份过滤")

    return cases[:35]


def _semantic_cases(connection: Any, subjects: dict[int, dict[str, Any]], tags: list[dict[str, Any]], snapshot_id: str, captured_at: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for index, row in enumerate(tags[22:32], 1):
        tag = str(row["name"])
        result_ids = _subject_query(connection, "EXISTS (SELECT 1 FROM subject_meta_tag smt WHERE smt.subject_id=s.id AND smt.name=:tag AND smt.source_active=1)", {"tag": tag})
        if not result_ids:
            continue
        cases.append(_sql_case(case_id=f"semantic_tag_{index:02d}", category="subjective_semantic", description="由 active 元标签支持的语义检索定义", query={"semantic_query": tag}, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.semantic_tag_evidence.v1", parameters={"tag": tag}, source_tables=["subject", "subject_meta_tag"]))
    return cases[:10]


def _entity_cases(connection: Any, subjects: dict[int, dict[str, Any]], credits: list[dict[str, Any]], characters: list[dict[str, Any]], actors: list[dict[str, Any]], snapshot_id: str, captured_at: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for index, row in enumerate(credits[:10], 1):
        entity_id, name = int(row["person_id"]), str(row["name"])
        result_ids = _id_list(row["ids"])
        cases.append(_sql_case(case_id=f"person_{index:02d}", category="person_character", description="Person 关系回查", query={"person_ids": [entity_id]}, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.person_credit.v1", parameters={"person_id": entity_id, "name": name}, source_tables=["subject", "person", "subject_person_credit"]))
    for index, row in enumerate(characters[:8], 1):
        entity_id, name = int(row["character_id"]), str(row["name"])
        result_ids = _id_list(row["ids"])
        cases.append(_sql_case(case_id=f"character_{index:02d}", category="person_character", description="Character 关系回查", query={"character_ids": [entity_id]}, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.character.v1", parameters={"character_id": entity_id, "name": name}, source_tables=["subject", "character", "subject_character"]))
    for index, row in enumerate(actors[:7], 1):
        entity_id, name = int(row["person_id"]), str(row["name"])
        result_ids = _id_list(row["ids"])
        cases.append(_sql_case(case_id=f"actor_{index:02d}", category="person_character", description="声优关系回查", query={"actor_ids": [entity_id]}, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.actor.v1", parameters={"person_id": entity_id, "name": name}, source_tables=["subject", "character", "person", "character_actor"]))
    return cases


def _relation_cases(connection: Any, subjects: dict[int, dict[str, Any]], relations: list[dict[str, Any]], snapshot_id: str, captured_at: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for index, row in enumerate(relations[:5], 1):
        input_id = int(row["subject_id"])
        result_ids = [
            int(value)
            for value in connection.execute(
                text(
                    "SELECT DISTINCT CASE WHEN sr.subject_id=:subject_id "
                    "THEN sr.related_subject_id ELSE sr.subject_id END AS subject_id "
                    "FROM subject_relation sr "
                    "JOIN subject s ON s.id=CASE WHEN sr.subject_id=:subject_id "
                    "THEN sr.related_subject_id ELSE sr.subject_id END "
                    "WHERE (sr.subject_id=:subject_id OR sr.related_subject_id=:subject_id) "
                    "AND s.type=2 AND s.nsfw=0 AND s.import_status=1 "
                    "ORDER BY subject_id"
                ),
                {"subject_id": input_id},
            ).scalars().all()
        ]
        cases.append(_sql_case(case_id=f"relation_{index:02d}", category="series_relation", description="作品关系双向扩展回查", query={"relation_subject_ids": [input_id]}, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.relation_bidirectional.v1", parameters={"subject_id": input_id, "relation": row["relation"]}, source_tables=["subject", "subject_relation"]))
    return cases


def _negation_cases(connection: Any, subjects: dict[int, dict[str, Any]], tags: list[dict[str, Any]], snapshot_id: str, captured_at: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for index, row in enumerate(tags[32:38], 1):
        tag = str(row["name"])
        all_ids = _subject_query(connection, "EXISTS (SELECT 1 FROM subject_meta_tag smt WHERE smt.subject_id=s.id AND smt.name=:tag AND smt.source_active=1)", {"tag": tag})
        if len(all_ids) < 2:
            continue
        excluded = int(all_ids[0])
        result_ids = _subject_query(connection, "s.id<>:excluded AND EXISTS (SELECT 1 FROM subject_meta_tag smt WHERE smt.subject_id=s.id AND smt.name=:tag AND smt.source_active=1)", {"tag": tag, "excluded": excluded})
        cases.append(_sql_case(case_id=f"negation_tag_{index:02d}", category="negation", description="元标签结果排除指定作品", query={"meta_tags": [tag], "exclude_subject_ids": [excluded]}, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.meta_tag_exclusion.v1", parameters={"tag": tag, "excluded": excluded}, source_tables=["subject", "subject_meta_tag"]))
    thresholds = sorted({float(row["score"]) for row in subjects.values() if row.get("score") is not None}, reverse=True)
    for index, threshold in enumerate(thresholds[:4], 1):
        all_ids = _subject_query(connection, "s.score>=:score", {"score": threshold})
        if len(all_ids) < 2:
            continue
        excluded = int(all_ids[0])
        result_ids = _subject_query(connection, "s.score>=:score AND s.id<>:excluded", {"score": threshold, "excluded": excluded})
        cases.append(_sql_case(case_id=f"negation_score_{index:02d}", category="negation", description="评分结果排除指定作品", query={"score_min": threshold, "exclude_subject_ids": [excluded]}, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.score_exclusion.v1", parameters={"score": threshold, "excluded": excluded}, source_tables=["subject"]))
    all_ids = _subject_query(connection, "YEAR(s.air_date)=:year", {"year": 2026})
    if len(all_ids) >= 2:
        excluded = int(all_ids[0])
        result_ids = _subject_query(connection, "YEAR(s.air_date)=:year AND s.id<>:excluded", {"year": 2026, "excluded": excluded})
        cases.append(_sql_case(case_id="negation_year_01", category="negation", description="年份结果排除指定作品", query={"year_from": 2026, "year_to": 2026, "exclude_subject_ids": [excluded]}, result_ids=result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.year_exclusion.v1", parameters={"year": 2026, "excluded": excluded}, source_tables=["subject"]))
    return cases[:10]


def _degradation_cases(connection: Any, subjects: dict[int, dict[str, Any]], snapshot_id: str, captured_at: str) -> list[dict[str, Any]]:
    first = next(row for row in subjects.values() if _safe_term(row.get("name")))
    first_term = str(first["name"])
    first_result_ids = _subject_query(
        connection,
        "(s.name=:term OR s.name_cn=:term)",
        {"term": first_term},
    )
    if not first_result_ids:
        raise RuntimeError("无法为降级 case 找到真实标题结果")
    cases: list[dict[str, Any]] = []
    cases.append(_sql_case(case_id="degradation_empty_01", category="degradation", description="不存在标题必须返回空结果", query={"keywords": ["__no_such_anime_2026__"]}, result_ids=[], subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.no_match.v1", parameters={"term": "__no_such_anime_2026__"}, source_tables=["subject"]))
    cases.append(_sql_case(case_id="degradation_empty_02", category="degradation", description="超出数据范围的年份必须返回空结果", query={"year_from": 2200, "year_to": 2200}, result_ids=[], subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.year_no_match.v1", parameters={"year": 2200}, source_tables=["subject"]))
    for index, (semantic, fallback) in enumerate(((False, "business"), (True, "lexical_only")), 1):
        row = first
        query = {"semantic_query": row["name"]} if semantic else {"keywords": [row["name"]]}
        cases.append(_sql_case(case_id=f"degradation_fallback_{index:02d}", category="degradation", description="存储故障时保留既定降级路径", query=query, result_ids=first_result_ids, subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.title_exact.v1", parameters={"subject_id": int(row["id"]), "term": first_term}, source_tables=["subject"], hard_filters={"fallback": fallback}))
    cases.append(_sql_case(case_id="degradation_empty_03", category="degradation", description="严格不存在的标签必须返回空结果", query={"meta_tags": ["__no_such_tag_2026__"]}, result_ids=[], subjects=subjects, snapshot_id=snapshot_id, captured_at=captured_at, sql_template="subject.meta_tag_no_match.v1", parameters={"tag": "__no_such_tag_2026__"}, source_tables=["subject", "subject_meta_tag"]))
    return cases


def generate_dataset(engine: Engine) -> dict[str, Any]:
    with engine.connect() as connection:
        captured = connection.execute(text("SELECT UTC_TIMESTAMP()")).scalar_one()
        captured_at = f"{captured.isoformat()}Z"
        database = str(connection.execute(text("SELECT DATABASE()")).scalar_one())
        columns = connection.execute(text("SELECT table_name,column_name,data_type,is_nullable,column_key FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name IN ('subject','episode','person','character','subject_alias','subject_meta_tag','subject_relation','subject_person_credit','subject_character','character_actor') ORDER BY table_name,ordinal_position")).mappings().all()
        schema_signature = hashlib.sha256(json.dumps([dict(row) for row in columns], sort_keys=True, default=_json_value).encode()).hexdigest()
        snapshot_seed = {"database": database, "captured_at": captured_at, "schema_signature": schema_signature}
        snapshot_id = "mysql-" + hashlib.sha256(json.dumps(snapshot_seed, sort_keys=True).encode()).hexdigest()[:16]

        subject_rows = connection.execute(text("SELECT id,name,name_cn,air_date,score,rating_total FROM subject WHERE type=2 AND nsfw=0 AND import_status=1 ORDER BY id")).mappings().all()
        subjects = {int(row["id"]): dict(row) for row in subject_rows}
        aliases = connection.execute(text("SELECT subject_id,name FROM subject_alias WHERE source_active=1 AND name<>'' AND CHAR_LENGTH(name)<=48 ORDER BY id")).mappings().all()
        tags = connection.execute(text("SELECT smt.name,GROUP_CONCAT(smt.subject_id ORDER BY smt.subject_id) ids,COUNT(*) n FROM subject_meta_tag smt JOIN subject s ON s.id=smt.subject_id WHERE smt.source_active=1 AND s.type=2 AND s.nsfw=0 AND s.import_status=1 AND CHAR_LENGTH(smt.name)<=48 GROUP BY smt.name HAVING COUNT(*)>=2 ORDER BY n DESC,name")).mappings().all()
        credits = connection.execute(text("SELECT spc.person_id,p.name,GROUP_CONCAT(DISTINCT spc.subject_id ORDER BY spc.subject_id) ids,COUNT(DISTINCT spc.subject_id) n FROM subject_person_credit spc JOIN person p ON p.id=spc.person_id JOIN subject s ON s.id=spc.subject_id WHERE spc.source_active=1 AND s.type=2 AND s.nsfw=0 AND s.import_status=1 AND CHAR_LENGTH(p.name)<=48 GROUP BY spc.person_id,p.name HAVING COUNT(DISTINCT spc.subject_id)>=2 ORDER BY n DESC,spc.person_id")).mappings().all()
        characters = connection.execute(text("SELECT sc.character_id,c.name,GROUP_CONCAT(DISTINCT sc.subject_id ORDER BY sc.subject_id) ids,COUNT(DISTINCT sc.subject_id) n FROM subject_character sc JOIN `character` c ON c.id=sc.character_id JOIN subject s ON s.id=sc.subject_id WHERE sc.source_active=1 AND s.type=2 AND s.nsfw=0 AND s.import_status=1 AND CHAR_LENGTH(c.name)<=48 GROUP BY sc.character_id,c.name HAVING COUNT(DISTINCT sc.subject_id)>=2 ORDER BY n DESC,sc.character_id")).mappings().all()
        actors = connection.execute(text("SELECT ca.person_id,p.name,GROUP_CONCAT(DISTINCT ca.subject_id ORDER BY ca.subject_id) ids,COUNT(DISTINCT ca.subject_id) n FROM character_actor ca JOIN person p ON p.id=ca.person_id JOIN subject s ON s.id=ca.subject_id WHERE ca.source_active=1 AND s.type=2 AND s.nsfw=0 AND s.import_status=1 AND CHAR_LENGTH(p.name)<=48 GROUP BY ca.person_id,p.name HAVING COUNT(DISTINCT ca.subject_id)>=2 ORDER BY n DESC,ca.person_id")).mappings().all()
        relations = connection.execute(text("SELECT sr.id,sr.subject_id,sr.related_subject_id,sr.relation FROM subject_relation sr JOIN subject s ON s.id=sr.subject_id JOIN subject r ON r.id=sr.related_subject_id WHERE s.type=2 AND s.nsfw=0 AND s.import_status=1 AND r.type=2 AND r.nsfw=0 AND r.import_status=1 ORDER BY sr.id")).mappings().all()
        active_release = connection.execute(text("SELECT COUNT(*) FROM search_index_release WHERE status='ACTIVE'")).scalar_one()

    with engine.connect() as connection:
        cases = _title_cases(connection, subjects, [dict(row) for row in aliases], snapshot_id, captured_at)
        cases.extend(_structured_cases(connection, subjects, [dict(row) for row in tags], snapshot_id, captured_at))
        cases.extend(_semantic_cases(connection, subjects, [dict(row) for row in tags], snapshot_id, captured_at))
        cases.extend(_entity_cases(connection, subjects, [dict(row) for row in credits], [dict(row) for row in characters], [dict(row) for row in actors], snapshot_id, captured_at))
        cases.extend(_relation_cases(connection, subjects, [dict(row) for row in relations], snapshot_id, captured_at))
        cases.extend(_negation_cases(connection, subjects, [dict(row) for row in tags], snapshot_id, captured_at))
        cases.extend(_degradation_cases(connection, subjects, snapshot_id, captured_at))

    if len(cases) != 120:
        counts = Counter(case["category"] for case in cases)
        raise RuntimeError(f"真实快照只能生成 {len(cases)} 条 case，分类计数={dict(counts)}；拒绝写入不完整数据集")
    metadata = {
        "status": "DEFINITION_ONLY",
        "release_active": bool(active_release),
        "release_status": "ACTIVE" if active_release else "BLOCKED_NO_ACTIVE_RELEASE",
        "snapshot_id": snapshot_id,
        "captured_at": captured_at,
        "database": database,
        "schema_signature": schema_signature,
        "index_version": INDEX_VERSION,
        "profile_version": PROFILE_VERSION,
        "case_count": len(cases),
        "category_counts": dict(Counter(case["category"] for case in cases)),
        "generator": "tests.evals.generate_golden_cases:v1",
        "evaluation_note": "定义集来自真实 MySQL 快照；ACTIVE release 与真实服务回放仍需单独门禁。",
    }
    return {"metadata": metadata, "cases": cases}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("golden_cases.json"))
    args = parser.parse_args()
    dataset = generate_dataset(_connection())
    args.output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dataset["metadata"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
