from __future__ import annotations

from array import array
from dataclasses import dataclass, replace
from datetime import date
import math
import re
from typing import Any, Callable, Mapping, Sequence

from app.shared.observability import log_event
from app.rag.air_status import infer_air_status
from app.rag.ports import EmbeddingPort
from app.rag.schemas import RetrievalQuery
from app.rag.seasons import SEASON_QUARTERS
from app.rag.user_profile import UserPreference


_REDIS_RESERVED = re.compile(r'([,\.<>\{\}\[\}"\':;!@#$%^&*()\-+=~|\\/])')
_MAX_RESULTS = 15
_REDIS_TAG_RESERVED = re.compile(r'([\.< >\{\}\[\}"\':;!@#$%^&*()\-+=~|\\/])')


def escape_redis_term(value: str, *, preserve_comma: bool = False) -> str:
    """兼容旧索引表达式的唯一转义入口；调用方不能提供查询片段。"""
    return (_REDIS_TAG_RESERVED if preserve_comma else _REDIS_RESERVED).sub(r"\\\1", value)


@dataclass(frozen=True)
class RetrievalCandidate:
    subject_id: int
    retrieval_score: float
    retrieval_reason: str
    title: str = ""
    details: Mapping[str, Any] | None = None
    evidence: Mapping[str, Any] | None = None
    vector: Sequence[float] | None = None


@dataclass(frozen=True)
class RetrievalResult:
    available: bool
    items: list[RetrievalCandidate]
    reason: str = ""
    personalization_notice: str = ""


def reciprocal_rank_fusion(
    lexical: Sequence[RetrievalCandidate], semantic: Sequence[RetrievalCandidate], *, k: int = 60
) -> list[RetrievalCandidate]:
    """按固定 RRF 公式融合，平分时保持最早出现的候选顺序。"""
    scores: dict[int, float] = {}
    reasons: dict[int, set[str]] = {}
    originals: dict[int, RetrievalCandidate] = {}
    order: dict[int, int] = {}
    for source, label in ((lexical, "lexical"), (semantic, "semantic")):
        for rank, candidate in enumerate(source, start=1):
            sid = candidate.subject_id
            order.setdefault(sid, len(order))
            originals.setdefault(sid, candidate)
            scores[sid] = scores.get(sid, 0.0) + 1.0 / (k + rank)
            reasons.setdefault(sid, set()).add(label)
    return [
        replace(originals[sid], retrieval_score=scores[sid], retrieval_reason="+".join(sorted(reasons[sid])))
        for sid in sorted(scores, key=lambda value: (-scores[value], order[value]))
    ]


AuthorityLookup = Callable[..., dict | list]
EvidenceLookup = Callable[..., dict | list]
EntityResolveLookup = Callable[..., dict | list]
EntityNameLookup = Callable[..., Any]


class RagRetrievalService:
    """混合召回只产生经过 Business 权威回查的安全候选。"""

    def __init__(
        self,
        index: Any,
        embeddings: EmbeddingPort,
        *,
        authority_lookup: AuthorityLookup,
        business_search: AuthorityLookup,
        evidence_lookup: EvidenceLookup | None = None,
        resolve_evidence_lookup: EntityResolveLookup | None = None,
        entity_name_lookup: EntityNameLookup | None = None,
        lexical_search: AuthorityLookup | None = None,
    ) -> None:
        self._index = index
        self._embeddings = embeddings
        self._authority_lookup = authority_lookup
        self._business_search = business_search
        self._evidence_lookup = evidence_lookup
        self._resolve_evidence_lookup = resolve_evidence_lookup
        self._entity_name_lookup = entity_name_lookup
        self._lexical_search = lexical_search

    def retrieve(
        self,
        query: RetrievalQuery,
        *,
        token: str | None = None,
        preference: Mapping[int | str, float] | UserPreference | None = None,
        personalization_missing: bool = False,
        business_search: AuthorityLookup | None = None,
        evidence_lookup: EvidenceLookup | None = None,
        resolve_evidence_lookup: EntityResolveLookup | None = None,
        entity_name_lookup: EntityNameLookup | None = None,
        lexical_search: AuthorityLookup | None = None,
    ) -> RetrievalResult:
        entity_name_matches, entity_name_error = self._lookup_entity_name(
            query,
            lookup=entity_name_lookup or self._entity_name_lookup,
        )
        if entity_name_error:
            return self._complete(
                RetrievalResult(available=False, items=[], reason=entity_name_error),
                personalization_missing,
            )
        if query.entity_name and not entity_name_matches:
            return self._complete(
                RetrievalResult(available=True, items=[], reason="no_results"),
                personalization_missing,
            )
        entity_subject_ids, entity_resolution_error = self._resolve_entity_subject_ids(
            query,
            token=token,
            resolve_lookup=resolve_evidence_lookup or self._resolve_evidence_lookup,
            name_matches=entity_name_matches,
        )
        if entity_resolution_error:
            return self._complete(
                RetrievalResult(available=False, items=[], reason=entity_resolution_error),
                personalization_missing,
            )
        if entity_subject_ids is not None and not entity_subject_ids:
            return self._complete(
                RetrievalResult(available=True, items=[], reason="no_results"),
                personalization_missing,
            )

        lexical: list[RetrievalCandidate] = []
        semantic: list[RetrievalCandidate] = []
        redis_failed = False
        vector: list[float] | None = None
        if query.semantic_query:
            try:
                vector = self._embeddings.embed_documents([query.semantic_query])[0]
            except Exception:
                vector = None
        effective_evidence = evidence_lookup or self._evidence_lookup
        effective_lexical = lexical_search or self._lexical_search
        # 实体关系是权威白名单。存在文本意图时，只要词法/向量结果
        # 有候选就保留；仅当该结果为空时，才用完整白名单
        # 作为有界索引的兜底。
        has_textual_intent = bool(query.semantic_query or query.keywords)
        entity_candidates_exhausted = False
        versioned_semantic = getattr(self._index, "semantic_search_for_version", None)
        try:
            lexical_payload: Any = None
            index_version: str | None = None
            if callable(versioned_semantic):
                # 业务侧词法契约是发布版本的唯一来源。
                # 缺少版本号的响应必须失败即闭合。
                if effective_lexical is None:
                    raise RuntimeError("MySQL 词法检索适配器不可用")
                lexical_payload = effective_lexical(query, token=token)
                index_version = _index_version(lexical_payload)
                if not index_version:
                    raise RuntimeError("Business 词法响应缺少 indexVersion")
                lexical = self._as_candidates(lexical_payload, "lexical")
            for expression in self._expressions(query):
                if not callable(versioned_semantic) and (self._lexical_terms(query) or vector is None):
                    lexical = self._as_candidates(self._index.lexical_search(expression, limit=50), "lexical")
                if vector is not None:
                    if callable(versioned_semantic):
                        semantic = self._as_candidates(
                            versioned_semantic(index_version, query, vector, limit=50), "semantic"
                        )
                    else:
                        semantic = self._as_candidates(self._index.semantic_search(expression, vector, limit=50), "semantic")
                if not lexical and not semantic:
                    continue
                candidates = self._filter_entity_subjects(
                    reciprocal_rank_fusion(lexical, semantic), entity_subject_ids,
                )
                excluded = set(query.exclude_subject_ids)
                if excluded:
                    candidates = [candidate for candidate in candidates if candidate.subject_id not in excluded]
                if not candidates:
                    # 实体过滤可能清空有界索引窗口中的全部条目。
                    # 不要用空批次调用业务侧：部分适配器会拒绝，
                    # 且下方白名单兜底需要机会去查询已解析的 ID。
                    entity_candidates_exhausted = entity_subject_ids is not None
                    continue
                result = self._authoritative_result(
                    candidates, query, token, preference, effective_evidence,
                )
                if entity_subject_ids and result.available and (not has_textual_intent or not result.items):
                    # 词法/向量存储刻意只返回有界的 top-N 窗口。
                    # 实体关系展开是权威白名单，因此该窗口之外的候选
                    # 仍须在有界的业务批次中校验后，
                    # 才能判定结果完整。
                    allowlist_result = self._authoritative_allowlist_result(
                        entity_subject_ids,
                        query,
                        token,
                        preference,
                        effective_evidence,
                    )
                    if not allowlist_result.available:
                        return self._complete(allowlist_result, personalization_missing)
                    if allowlist_result.items:
                        merged: dict[int, RetrievalCandidate] = {
                            item.subject_id: item for item in allowlist_result.items
                        }
                        for item in result.items:
                            merged[item.subject_id] = item
                        merged_items = self._rerank(list(merged.values()), query, preference)[:_MAX_RESULTS]
                        result = RetrievalResult(available=True, items=merged_items)
                if not result.available or result.items:
                    return self._complete(result, personalization_missing)
        except Exception:
            redis_failed = True
            lexical, semantic = [], []

        # 向量/文本索引只返回其 top-N 窗口。白名单中的实体可能
        # 合理地排在该窗口之外，因此在判定无结果前要
        # 做一次精确的权威批量查询；这能避免实体过滤
        # 变成意外的召回上限。
        if entity_subject_ids and not redis_failed and (
            not has_textual_intent or not lexical or not semantic or entity_candidates_exhausted
        ):
            entity_result = self._authoritative_allowlist_result(
                entity_subject_ids, query, token, preference, effective_evidence
            )
            if not entity_result.available or entity_result.items:
                return self._complete(entity_result, personalization_missing)

        if redis_failed:
            return self._complete(
                self._business_fallback(
                    query,
                    token,
                    preference,
                    business_search or self._business_search,
                    effective_evidence,
                    entity_subject_ids,
                ),
                personalization_missing,
                "business",
            )
        return self._complete(RetrievalResult(available=True, items=[], reason="no_results"), personalization_missing)

    def _authoritative_allowlist_result(
        self,
        subject_ids: Sequence[int],
        query: RetrievalQuery,
        token: str | None,
        preference: Mapping[int | str, float] | UserPreference | None,
        evidence_lookup: EvidenceLookup | None,
    ) -> RetrievalResult:
        """回查完整实体 allowlist，避免索引 top-N 截断关系结果。"""
        safe_items: dict[int, RetrievalCandidate] = {}
        for offset in range(0, len(subject_ids), 50):
            batch = subject_ids[offset : offset + 50]
            candidates = [
                RetrievalCandidate(subject_id, 0.0, "entity_allowlist")
                for subject_id in batch
                if subject_id not in query.exclude_subject_ids
            ]
            if not candidates:
                continue
            result = self._authoritative_result(
                candidates,
                query,
                token,
                preference,
                evidence_lookup,
                result_limit=len(candidates),
            )
            if not result.available:
                return result
            for item in result.items:
                safe_items[item.subject_id] = item
        if not safe_items:
            return RetrievalResult(available=True, items=[], reason="no_results")
        items = list(safe_items.values())
        if _has_textual_intent(query):
            items = self._rerank(items, query, preference)
        return RetrievalResult(available=True, items=items[:_MAX_RESULTS])

    def _resolve_entity_subject_ids(
        self,
        query: RetrievalQuery,
        *,
        token: str | None,
        resolve_lookup: EntityResolveLookup | None,
        name_matches: list[tuple[str, int]] | None = None,
    ) -> tuple[list[int] | None, str | None]:
        """在触碰索引前先通过业务侧解析类型化实体 ID。

        解析响应只保留安全的 Subject ID。在本服务中，实体 ID
        绝不会变成 Redis 表达式或 SQL 片段。
        多个实体过滤条件是取交集，并保留业务侧对第一个过滤器的确定性顺序。
        """
        requested = [
            ("PERSON", query.person_ids),
            ("CHARACTER", query.character_ids),
            ("ACTOR", query.actor_ids),
            ("RELATION_SUBJECT", query.relation_subject_ids),
        ]
        by_kind: dict[str, list[int]] = {"PERSON": [], "CHARACTER": [], "ACTOR": [], "RELATION_SUBJECT": []}
        for entity_type, entity_id in name_matches or []:
            by_kind[entity_type].append(entity_id)
        if not any(ids for _, ids in requested) and not any(by_kind.values()):
            return None, None
        if resolve_lookup is None:
            return [], "entity_resolution_unavailable"

        allowed: list[int] | None = None
        for entity_type, entity_ids in requested:
            if not entity_ids:
                continue
            try:
                response = resolve_lookup(entity_type, list(entity_ids), token=token)
            except Exception:
                return [], "entity_resolution_unavailable"
            if _is_error(response):
                return [], "entity_resolution_unavailable"
            resolved, valid = self._safe_resolved_subject_ids(response)
            if not valid:
                return [], "entity_resolution_unavailable"
            if allowed is None:
                allowed = resolved
            else:
                resolved_set = set(resolved)
                allowed = [subject_id for subject_id in allowed if subject_id in resolved_set]
            if not allowed:
                return [], None
        # 未指定类型的名称可能同时匹配人物和角色。
        # 这些候选在名称约束内是 OR 关系；下方只对不同查询字段做 AND。
        if any(by_kind.values()):
            name_allowed: list[int] = []
            name_seen: set[int] = set()
            for entity_type, entity_ids in by_kind.items():
                if not entity_ids:
                    continue
                try:
                    response = resolve_lookup(entity_type, list(entity_ids), token=token)
                except Exception:
                    return [], "entity_resolution_unavailable"
                if _is_error(response):
                    return [], "entity_resolution_unavailable"
                resolved, valid = self._safe_resolved_subject_ids(response)
                if not valid:
                    return [], "entity_resolution_unavailable"
                for subject_id in resolved:
                    if subject_id not in name_seen:
                        name_seen.add(subject_id)
                        name_allowed.append(subject_id)
            if allowed is None:
                allowed = name_allowed
            else:
                name_allowed_set = set(name_allowed)
                allowed = [subject_id for subject_id in allowed if subject_id in name_allowed_set]
            if not allowed:
                return [], None
        return allowed or [], None

    @staticmethod
    def _lookup_entity_name(
        query: RetrievalQuery,
        *,
        lookup: EntityNameLookup | None,
    ) -> tuple[list[tuple[str, int]], str | None]:
        """通过影子索引把面向用户的名称解析为类型化本地 ID。"""
        if not query.entity_name:
            return [], None
        if lookup is None:
            return [], "entity_resolution_unavailable"
        try:
            response = lookup(
                query.entity_name,
                entity_kind=query.entity_kind,
                limit=50,
            )
        except Exception:
            return [], "entity_resolution_unavailable"
        if isinstance(response, Mapping):
            response = response.get("items", response.get("matches", response.get("data")))
        if not isinstance(response, (list, tuple)):
            return [], "entity_resolution_unavailable"
        matches: list[tuple[str, int]] = []
        seen: set[tuple[str, int]] = set()
        allowed_kinds = {query.entity_kind} if query.entity_kind else {"PERSON", "CHARACTER", "ACTOR", "RELATION_SUBJECT"}
        for row in response:
            if isinstance(row, Mapping):
                raw_kind = row.get("entity_kind", row.get("entityType"))
                raw_id = row.get("entity_id", row.get("entityId"))
            else:
                raw_kind = getattr(row, "entity_kind", None)
                raw_id = getattr(row, "entity_id", None)
            kind = str(raw_kind or "").upper()
            if kind not in allowed_kinds or isinstance(raw_id, bool):
                return [], "entity_resolution_unavailable"
            try:
                entity_id = int(raw_id)
            except (TypeError, ValueError):
                return [], "entity_resolution_unavailable"
            if entity_id < 1:
                return [], "entity_resolution_unavailable"
            identity = (kind, entity_id)
            if identity not in seen:
                seen.add(identity)
                matches.append(identity)
        return matches, None

    @staticmethod
    def _safe_resolved_subject_ids(response: Any) -> tuple[list[int], bool]:
        """仅从 /resolve 提取活动的、非 NSFW 的动画 Subject。"""
        if isinstance(response, list):
            # 直接列表是 HttpBusinessGateway 归一化后的成功响应。
            # Redis 协议数组在此无效。
            if response and isinstance(response[0], int):
                return [], False
            rows = response
        elif isinstance(response, Mapping):
            rows = response.get("items")
            if rows is None:
                rows = response.get("content")
            if rows is None:
                rows = response.get("data")
            if not isinstance(rows, list):
                return [], False
        else:
            return [], False
        subject_ids: list[int] = []
        seen: set[int] = set()
        for row in rows:
            if not isinstance(row, Mapping):
                return [], False
            raw_id = row.get("subjectId", row.get("subject_id", row.get("id")))
            if isinstance(raw_id, bool):
                return [], False
            try:
                subject_id = int(raw_id)
            except (TypeError, ValueError):
                return [], False
            if subject_id <= 0 or not RagRetrievalService._is_safe_subject_response(row):
                return [], False
            if subject_id not in seen:
                seen.add(subject_id)
                subject_ids.append(subject_id)
        return subject_ids, True

    @staticmethod
    def _is_safe_subject_response(item: Mapping[str, Any]) -> bool:
        try:
            if int(item.get("type") or 0) != 2 or item.get("nsfw") is not False:
                return False
            # 业务侧把 import_status 暴露为派生字段 `active`；
            # 缺失时失败即闭合，因为实体过滤绝不能因权威响应不完整
            # 而扩大候选集。
            if item.get("active") is not True:
                return False
            if "importStatus" in item and int(item.get("importStatus") or 0) != 1:
                return False
            if "import_status" in item and int(item.get("import_status") or 0) != 1:
                return False
        except (TypeError, ValueError):
            return False
        return True

    @staticmethod
    def _filter_entity_subjects(
        candidates: Sequence[RetrievalCandidate],
        allowed_subject_ids: list[int] | None,
    ) -> list[RetrievalCandidate]:
        if allowed_subject_ids is None:
            return list(candidates)
        allowed = set(allowed_subject_ids)
        return [
            replace(candidate, retrieval_reason=f"{candidate.retrieval_reason}+entity")
            for candidate in candidates
            if candidate.subject_id in allowed
        ]

    @staticmethod
    def _complete(result: RetrievalResult, personalization_missing: bool, fallback_type: str | None = None) -> RetrievalResult:
        result = RagRetrievalService._with_personalization_notice(result, personalization_missing)
        log_event("rag.retrieval.completed", candidateCount=len(result.items), success=result.available)
        if fallback_type is not None:
            log_event("rag.fallback.used", fallbackType=fallback_type, success=result.available)
        return result

    def _expressions(self, query: RetrievalQuery) -> list[str]:
        attempts = [query]
        if query.score_min is not None or query.rating_total_min is not None:
            attempts.append(query.model_copy(update={"score_min": None, "rating_total_min": None}))
        if query.year_from is not None or query.year_to is not None:
            attempts.append(attempts[-1].model_copy(update={"year_from": None, "year_to": None}))
        if query.meta_tags:
            attempts.append(attempts[-1].model_copy(update={"meta_tags": []}))
        return [self._build_expression(attempt) for attempt in attempts[:4]]

    def _build_expression(self, query: RetrievalQuery) -> str:
        parts: list[str] = []
        terms = self._lexical_terms(query)
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

    @staticmethod
    def _lexical_terms(query: RetrievalQuery) -> list[str]:
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

    def _authoritative_result(
        self,
        candidates: Sequence[RetrievalCandidate],
        query: RetrievalQuery,
        token: str | None,
        preference: Mapping[int | str, float] | UserPreference | None,
        evidence_lookup: EvidenceLookup | None = None,
        result_limit: int = _MAX_RESULTS,
    ) -> RetrievalResult:
        try:
            response = self._authority_lookup([item.subject_id for item in candidates[:50]], token=token, exclude_collected=True)
        except Exception:
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        if _is_error(response):
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        details_by_id: dict[int, Mapping[str, Any]] = {}
        for item in _items(response):
            if not isinstance(item, Mapping) or item.get("id") is None or isinstance(item.get("id"), bool):
                continue
            try:
                subject_id = int(item["id"])
            except (TypeError, ValueError, OverflowError):
                continue
            if subject_id > 0:
                details_by_id[subject_id] = item
        # 批量 Subject 接口刻意只返回基础权威字段。
        # 在 Evidence 之前校验该边界，但此处不要应用结构化过滤：
        # metaTags 等字段只有 Evidence 响应才提供。
        safe = [
            replace(candidate, details=details_by_id[candidate.subject_id])
            for candidate in candidates
            if candidate.subject_id in details_by_id
            and self._is_safe_authority_detail(details_by_id[candidate.subject_id], query)
        ]
        if safe and evidence_lookup is not None:
            safe, evidence_ok = self._enrich_evidence(safe, token, evidence_lookup)
            if not evidence_ok:
                # Evidence 是数据进入 Agent 上下文前的最终权威边界。
                # 部分失败或整体失败的响应绝不能静默回退到
                # Redis/Subject 详情。
                return RetrievalResult(available=False, items=[], reason="evidence_unavailable")
            # 只有在 Evidence 提供了完整字段（metaTags、score、ratingTotal、airDate 等）
            # 之后才应用结构化过滤。
            safe = [
                candidate
                for candidate in safe
                if candidate.evidence is not None
                and self._matches_query_filters(candidate.evidence, query)
            ]
        elif safe:
            # 未配置 Evidence 适配器时保留既有的业务侧回退行为；
            # 该模式下没有可用于评估更丰富字段的证据载荷。
            safe = [
                candidate
                for candidate in safe
                if self._matches_query_filters(candidate.details or {}, query)
            ]
        ranked = safe if not _has_textual_intent(query) else self._rerank(safe, query, preference)
        return RetrievalResult(available=True, items=ranked[:max(0, result_limit)])

    def _business_fallback(
        self,
        query: RetrievalQuery,
        token: str | None,
        preference: Mapping[int | str, float] | UserPreference | None,
        business_search: AuthorityLookup,
        evidence_lookup: EvidenceLookup | None = None,
        allowed_subject_ids: list[int] | None = None,
    ) -> RetrievalResult:
        try:
            response = business_search(query, token=token)
        except Exception:
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        if _is_error(response):
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        allowed = set(allowed_subject_ids) if allowed_subject_ids is not None else None
        candidates: list[RetrievalCandidate] = []
        for item in _items(response):
            if not isinstance(item, Mapping) or item.get("id") is None:
                continue
            raw_id = item.get("id")
            if isinstance(raw_id, bool):
                continue
            try:
                subject_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if subject_id <= 0 or subject_id in query.exclude_subject_ids:
                continue
            if allowed is not None and subject_id not in allowed:
                continue
            candidates.append(
                RetrievalCandidate(
                    subject_id,
                    0.0,
                    "business_fallback",
                    str(item.get("nameCn") or item.get("name") or ""),
                )
            )
        if not candidates:
            return RetrievalResult(available=True, items=[])
        return self._authoritative_result(candidates, query, token, preference, evidence_lookup)

    @staticmethod
    def _enrich_evidence(
        candidates: list[RetrievalCandidate],
        token: str | None,
        evidence_lookup: EvidenceLookup,
    ) -> tuple[list[RetrievalCandidate], bool]:
        """批量回查 Evidence API；失败或部分结果时 fail-closed。"""
        try:
            response = evidence_lookup([c.subject_id for c in candidates], token=token)
        except Exception:
            log_event("rag.evidence.enriched", success=False, errorType="exception")
            return [], False
        if _is_error(response):
            log_event("rag.evidence.enriched", success=False, errorType="business_error")
            return [], False
        rows = response if isinstance(response, list) else []
        by_id: dict[int, Mapping[str, Any]] = {}
        for row in rows:
            if not isinstance(row, Mapping) or row.get("subjectId") is None or isinstance(row.get("subjectId"), bool):
                return [], False
            try:
                subject_id = int(row["subjectId"])
            except (TypeError, ValueError, OverflowError):
                return [], False
            if subject_id <= 0:
                return [], False
            if subject_id in by_id:
                # 合法 ID 重复意味着业务侧对同一 Subject 返回了两行
                # 自相矛盾的数据。字典会静默保留最后一行，而下方的
                # 键集合校验仍会通过，因此在此拒绝整个批次。
                log_event(
                    "rag.evidence.enriched",
                    success=False,
                    errorType="duplicate_subject_id",
                    duplicateSubjectId=subject_id,
                )
                return [], False
            by_id[subject_id] = row
        expected_ids = {candidate.subject_id for candidate in candidates}
        if by_id.keys() != expected_ids:
            log_event(
                "rag.evidence.enriched",
                success=False,
                errorType="partial_response",
                expectedCount=len(expected_ids),
                actualCount=len(by_id),
            )
            return [], False
        enriched = []
        for candidate in candidates:
            ev = by_id.get(candidate.subject_id)
            if ev is None or not RagRetrievalService._is_safe_evidence(ev, candidate.subject_id):
                log_event("rag.evidence.enriched", success=False, errorType="unsafe_response")
                return [], False
            candidate = replace(candidate, evidence=RagRetrievalService._map_evidence(ev))
            enriched.append(candidate)
        log_event("rag.evidence.enriched", success=True, candidateCount=len(enriched))
        return enriched, True

    @staticmethod
    def _is_safe_evidence(item: Mapping[str, Any], subject_id: int) -> bool:
        """验证 EvidenceCandidateVO 的安全边界，避免错误数据进入上下文。"""
        try:
            return (
                int(item.get("subjectId")) == subject_id
                and int(item.get("type") or 0) == 2
                and item.get("nsfw") is False
                and item.get("active") is True
            )
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _map_evidence(ev: Mapping[str, Any]) -> dict[str, Any]:
        """将 EvidenceCandidateVO 映射为 Agent 内部证据字典。"""
        summary = str(ev.get("summary") or "")
        return {
            "aliases": [str(a) for a in (ev.get("aliases") or [])],
            "metaTags": [str(t) for t in (ev.get("metaTags") or [])],
            "credits": [
                f"{str(c.get('personName', ''))}({str(c.get('relation', ''))})"
                for c in (ev.get("credits") or [])
                if isinstance(c, Mapping)
            ],
            "characters": [
                f"{str(c.get('characterName', ''))}({str(c.get('relation', ''))})"
                for c in (ev.get("characters") or [])
                if isinstance(c, Mapping)
            ],
            "relations": [
                f"{str(r.get('relatedSubjectNameCn') or r.get('relatedSubjectName', ''))}({str(r.get('relation', ''))})"
                for r in (ev.get("relations") or [])
                if isinstance(r, Mapping)
            ],
            "summaryExcerpt": summary[:200] if summary else "",
            "summarySource": "bangumi_official",
            "ratingTotal": ev.get("ratingTotal"),
            "collectionTotal": ev.get("collectionTotal"),
            "score": ev.get("score"),
            "airDate": ev.get("airDate"),
            "airStatus": ev.get("airStatus") or ev.get("air_status"),
            "sourceTime": ev.get("sourceTime"),
            "sourceFetchedAt": ev.get("sourceFetchedAt") or ev.get("sourceTime"),
            "active": ev.get("active"),
            "sourceId": ev.get("sourceId"),
            "sourceUrl": ev.get("sourceUrl"),
            "nameCn": ev.get("nameCn"),
            "name": ev.get("name"),
            "type": ev.get("type"),
            "nsfw": ev.get("nsfw"),
            "rank": ev.get("rank"),
        }

    @staticmethod
    def _is_safe_authority_detail(item: Mapping[str, Any], query: RetrievalQuery) -> bool:
        """只校验业务侧批量权威接口提供的字段。

        此阶段不得运行结构化过滤，因为批量接口
        不包含 ``metaTags`` 等 Evidence 字段。
        """
        try:
            if (
                int(item.get("type") or 0) != 2
                or item.get("nsfw") is not False
                or item.get("active") is not True
            ):
                return False
            if int(item.get("id") or -1) in query.exclude_subject_ids:
                return False
        except (TypeError, ValueError):
            return False
        return True

    @staticmethod
    def _matches_query_filters(item: Mapping[str, Any], query: RetrievalQuery) -> bool:
        """对实体兜底使用的精确业务行应用查询过滤。"""
        if query.score_min is not None:
            try:
                if float(item.get("score")) < query.score_min:
                    return False
            except (TypeError, ValueError):
                return False
        if query.rating_total_min is not None:
            try:
                if int(item.get("ratingTotal")) < query.rating_total_min:
                    return False
            except (TypeError, ValueError):
                return False

        year = _item_year(item)
        if query.year_from is not None and (year is None or year < query.year_from):
            return False
        if query.year_to is not None and (year is None or year > query.year_to):
            return False
        if query.quarter is not None:
            quarter = _item_quarter(item)
            if quarter != SEASON_QUARTERS[query.quarter]:
                return False

        if query.air_status is not None:
            status = str(item.get("airStatus") or item.get("air_status") or "").upper()
            if status not in {"UPCOMING", "AIRING", "FINISHED"}:
                # 只允许保守推断来填补缺失或非权威状态；
                # 显式的 ``UNKNOWN`` 不得被当作权威值。
                status = infer_air_status(item.get("airDate") or item.get("air_date"))
            if status != query.air_status:
                return False

        if query.meta_tags:
            raw_tags = item.get("metaTags") or item.get("meta_tags") or item.get("tags")
            tags: set[str] = set()
            if isinstance(raw_tags, (list, tuple, set)):
                for raw_tag in raw_tags:
                    if isinstance(raw_tag, Mapping):
                        raw_tag = raw_tag.get("name") or raw_tag.get("title")
                    if raw_tag is not None:
                        tags.add(str(raw_tag).casefold())
            if any(tag.casefold() not in tags for tag in query.meta_tags):
                return False
        return True

    @staticmethod
    def _as_candidates(response: Any, reason: str) -> list[RetrievalCandidate]:
        rows = _items(response)
        candidates: list[RetrievalCandidate] = []
        for item in rows:
            if not isinstance(item, Mapping):
                continue
            # 业务侧词法候选用公开字段 ``subjectId``，
            # 而 Redis/旧适配器使用 ``subject_id`` 或 ``id``。
            # 在此边界统一三者，避免有效的 FULLTEXT 响应
            # 在 RRF 前被静默丢弃。
            raw_id = item.get("subject_id", item.get("subjectId", item.get("id")))
            if isinstance(raw_id, bool):
                continue
            try:
                subject_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if subject_id <= 0:
                continue
            vector = item.get("vector")
            raw_score = item.get(
                "score",
                item.get("lexicalScore", item.get("vector_score", item.get("similarity", 0.0))),
            )
            try:
                retrieval_score = float(raw_score)
            except (TypeError, ValueError):
                retrieval_score = 0.0
            candidates.append(
                RetrievalCandidate(
                    subject_id,
                    retrieval_score,
                    reason,
                    str(item.get("title") or item.get("nameCn") or item.get("name") or ""),
                    vector=vector if isinstance(vector, Sequence) and not isinstance(vector, (str, bytes)) else None,
                )
            )
        return candidates

    @staticmethod
    def _rerank(
        candidates: Sequence[RetrievalCandidate],
        query: RetrievalQuery,
        preference: Mapping[int | str, float] | UserPreference | None,
    ) -> list[RetrievalCandidate]:
        maximum = max((candidate.retrieval_score for candidate in candidates), default=1.0) or 1.0
        today = date.today()

        def score(candidate: RetrievalCandidate) -> float:
            details = candidate.details or {}
            rating = min(max(float(details.get("ratingTotal") or 0) / 1000.0, 0.0), 1.0)
            popularity = min(max(float(details.get("collectionTotal") or 0) / 10000.0, 0.0), 1.0)
            freshness = _freshness(details.get("airDate"), today)
            preferred = _preference_score(candidate, preference)
            result = 0.55 * (candidate.retrieval_score / maximum) + 0.15 * rating + 0.10 * popularity + 0.10 * freshness + 0.10 * preferred
            title = str(details.get("nameCn") or details.get("name") or candidate.title)
            exact_terms = [query.semantic_query, *query.keywords]
            if any(term and title.casefold() == term.casefold() for term in exact_terms):
                result += 0.30
            evidence = candidate.evidence or {}
            raw_tags = evidence.get("metaTags") or evidence.get("meta_tags") or evidence.get("tags")
            if query.semantic_query and isinstance(raw_tags, (list, tuple, set)):
                semantic_text = query.semantic_query.strip().casefold()
                if any(str(tag).strip().casefold() == semantic_text for tag in raw_tags):
                    # 元标签是语义标签用例的权威证据；
                    # 在有界结果集中保留精确标签匹配。
                    result += 0.35
            return min(result, 1.0)

        return sorted(candidates, key=lambda item: (-score(item), item.subject_id))

    @staticmethod
    def _with_personalization_notice(result: RetrievalResult, missing: bool) -> RetrievalResult:
        if not missing:
            return result
        return replace(result, personalization_notice="基于你当前的收藏还不多，先给你看热门")

def _items(response: Any) -> list[Any]:
    if isinstance(response, Mapping):
        if isinstance(response.get("items"), list):
            return response["items"]
        if isinstance(response.get("candidates"), list):
            return response["candidates"]
        if isinstance(response.get("content"), list):
            return response["content"]
        return []
    if isinstance(response, list):
        if response and isinstance(response[0], int):
            rows: list[dict[str, Any]] = []
            for offset in range(1, len(response), 2):
                if offset + 1 >= len(response) or not isinstance(response[offset + 1], (list, tuple)):
                    continue
                fields = response[offset + 1]
                row = {
                    _text(fields[i]): _decode_subject_vector(fields[i + 1]) if _text(fields[i]) == "vector" else _text(fields[i + 1])
                    for i in range(0, len(fields) - 1, 2)
                }
                row.setdefault("subject_id", _text(response[offset]).rsplit(":", 1)[-1])
                rows.append(row)
            return rows
        return response
    return []


def _index_version(response: Any) -> str | None:
    """从词法响应中提取业务侧发布指针。"""
    if not isinstance(response, Mapping):
        return None
    value = response.get("indexVersion", response.get("index_version"))
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if ":" in value or any(char.isspace() for char in value):
        return None
    return value


def _is_error(response: Any) -> bool:
    return isinstance(response, Mapping) and bool(response.get("error"))


def _freshness(value: Any, today: date) -> float:
    try:
        year = date.fromisoformat(str(value)).year
    except (TypeError, ValueError):
        return 0.0
    return min(max(1.0 - (today.year - year) / 10.0, 0.0), 1.0)


def _item_year(item: Mapping[str, Any]) -> int | None:
    raw_year = item.get("year")
    if raw_year is not None:
        try:
            return int(raw_year)
        except (TypeError, ValueError):
            return None
    raw_date = item.get("airDate") or item.get("air_date")
    try:
        return int(str(raw_date)[:4])
    except (TypeError, ValueError):
        return None


def _item_quarter(item: Mapping[str, Any]) -> int | None:
    raw_quarter = item.get("quarter")
    if raw_quarter is not None:
        if isinstance(raw_quarter, str):
            normalized = raw_quarter.casefold()
            if normalized in SEASON_QUARTERS:
                return SEASON_QUARTERS[normalized]
        try:
            quarter = int(raw_quarter)
            return quarter if quarter in {1, 2, 3, 4} else None
        except (TypeError, ValueError):
            return None
    raw_date = item.get("airDate") or item.get("air_date")
    try:
        month = int(str(raw_date)[5:7])
    except (TypeError, ValueError):
        return None
    return ((month - 1) // 3) + 1 if 1 <= month <= 12 else None


def _has_textual_intent(query: RetrievalQuery) -> bool:
    """是否允许排序对结构化结果集重新排序。"""
    return bool(query.semantic_query or query.keywords)


def _preference_score(candidate: RetrievalCandidate, preference: Mapping[int | str, float] | UserPreference | None) -> float:
    if preference is None:
        return 0.0
    if isinstance(preference, Mapping):
        return min(
            max(float(preference.get(candidate.subject_id, preference.get(str(candidate.subject_id), 0.0))), 0.0),
            1.0,
        )
    profile_vector = getattr(preference, "vector", None)
    candidate_vector = candidate.vector
    if not isinstance(profile_vector, Sequence) or not isinstance(candidate_vector, Sequence):
        return 0.0
    if len(profile_vector) != len(candidate_vector) or not profile_vector:
        return 0.0
    try:
        dot = sum(float(left) * float(right) for left, right in zip(profile_vector, candidate_vector))
        profile_size = math.sqrt(sum(float(value) ** 2 for value in profile_vector))
        candidate_size = math.sqrt(sum(float(value) ** 2 for value in candidate_vector))
    except (TypeError, ValueError, OverflowError):
        return 0.0
    if not all(math.isfinite(value) for value in (dot, profile_size, candidate_size)) or not profile_size or not candidate_size:
        return 0.0
    return min(max((dot / (profile_size * candidate_size) + 1.0) / 2.0, 0.0), 1.0)


def _decode_subject_vector(value: Any) -> list[float] | None:
    if not isinstance(value, bytes) or len(value) != 1024 * 4:
        return None
    decoded = array("f")
    decoded.frombytes(value)
    return list(decoded) if all(math.isfinite(number) for number in decoded) else None


def _text(value: Any) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)
