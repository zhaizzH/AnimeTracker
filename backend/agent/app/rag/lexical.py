"""词法表达式构造：RediSearch 表达式与词条切分（从 retrieval.py 拆出，move-only）。"""
from __future__ import annotations

import re

from app.rag.schemas import RetrievalQuery
from app.rag.seasons import SEASON_QUARTERS

_REDIS_RESERVED = re.compile(r'([,\.<>\{\}\[\}"\':;!@#$%^&*()\-+=~|\\/])')
_REDIS_TAG_RESERVED = re.compile(r'([\.< >\{\}\[\}"\':;!@#$%^&*()\-+=~|\\/])')

def escape_redis_term(value: str, *, preserve_comma: bool = False) -> str:
    """兼容旧索引表达式的唯一转义入口；调用方不能提供查询片段。"""
    return (_REDIS_TAG_RESERVED if preserve_comma else _REDIS_RESERVED).sub(r"\\\1", value)

def expressions(query: RetrievalQuery) -> list[str]:
    attempts = [query]
    if query.score_min is not None or query.rating_total_min is not None:
        attempts.append(query.model_copy(update={"score_min": None, "rating_total_min": None}))
    if query.year_from is not None or query.year_to is not None:
        attempts.append(attempts[-1].model_copy(update={"year_from": None, "year_to": None}))
    if query.meta_tags:
        attempts.append(attempts[-1].model_copy(update={"meta_tags": []}))
    return [build_expression(attempt) for attempt in attempts[:4]]

def build_expression(query: RetrievalQuery) -> str:
    parts: list[str] = []
    terms = lexical_terms(query)
    if terms:
        words = " ".join(escape_redis_term(word) for word in terms)
        parts.append(f"(@title:({words})|@aliases:({words})|@summary:({words}))")
    if query.year_from is not None or query.year_to is not None:
        parts.append(f"@year:[{query.year_from if query.year_from is not None else '-inf'} {query.year_to if query.year_to is not None else '+inf'}]")
    if query.quarter:
        value = SEASON_QUARTERS[query.quarter]
        parts.append(f"@quarter:[{value} {value}]")
    if query.score_min is not None:
        parts.append(f"@score:[{query.score_min} +inf]")
    if query.rating_total_min is not None:
        parts.append(f"@rating_total:[{query.rating_total_min} +inf]")
    for tag in query.meta_tags:
        parts.append(f"@meta_tags:{{{escape_redis_term(tag, preserve_comma=True)}}}")
    if query.air_status:
        parts.append(f"@air_status:{{{escape_redis_term(query.air_status.lower())}}}")
    for subject_id in query.exclude_subject_ids:
        parts.append(f"-@subject_id:[{int(subject_id)} {int(subject_id)}]")
    return " ".join(parts) or "*"

def lexical_terms(query: RetrievalQuery) -> list[str]:
    if query.keywords:
        return list(query.keywords)
    if not query.semantic_query:
        return []
    terms: list[str] = []
    for token in query.semantic_query.split():
        terms.extend(token[offset : offset + 48] for offset in range(0, len(token), 48))
        if len(terms) >= 8:
            break
    return terms[:8]
