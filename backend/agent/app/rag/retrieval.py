from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping, Sequence

from app.shared.observability import log_event
from app.rag.air_status import infer_air_status  # noqa: F401  # 测试契约：call site 复用共享推断函数
from app.rag.authority import (
    enrich_evidence,
    index_version,
    is_safe_authority_detail,
    items_of,
    map_evidence,
    matches_query_filters,
)
from app.rag.entity_resolution import (
    EntityNameLookup,
    EntityResolveLookup,
    is_error,
    lookup_entity_name,
    resolve_entity_subject_ids,
)
from app.rag.lexical import expressions, lexical_terms
from app.rag.ports import EmbeddingPort
from app.rag.rerank import (
    as_candidates,
    filter_entity_subjects,
    has_textual_intent,
    reciprocal_rank_fusion,
    rerank,
)
from app.rag.schemas import RetrievalQuery
from app.rag.user_profile import UserPreference

_MAX_RESULTS = 15

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

AuthorityLookup = Callable[..., dict | list]
EvidenceLookup = Callable[..., dict | list]

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
        entity_name_matches, entity_name_error = lookup_entity_name(
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
        entity_subject_ids, entity_resolution_error = resolve_entity_subject_ids(
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
        textual_intent = has_textual_intent(query)
        entity_candidates_exhausted = False
        versioned_semantic = getattr(self._index, "semantic_search_for_version", None)
        try:
            lexical_payload: Any = None
            version: str | None = None
            if callable(versioned_semantic):
                # 业务侧词法契约是发布版本的唯一来源。
                # 缺少版本号的响应必须失败即闭合。
                if effective_lexical is None:
                    raise RuntimeError("MySQL 词法检索适配器不可用")
                lexical_payload = effective_lexical(query, token=token)
                version = index_version(lexical_payload)
                if not version:
                    raise RuntimeError("Business 词法响应缺少 indexVersion")
                lexical = as_candidates(lexical_payload, "lexical", RetrievalCandidate)
            for expression in expressions(query):
                if not callable(versioned_semantic) and (lexical_terms(query) or vector is None):
                    lexical = as_candidates(self._index.lexical_search(expression, limit=50), "lexical", RetrievalCandidate)
                if vector is not None:
                    if callable(versioned_semantic):
                        semantic = as_candidates(
                            versioned_semantic(version, query, vector, limit=50), "semantic", RetrievalCandidate
                        )
                    else:
                        semantic = as_candidates(self._index.semantic_search(expression, vector, limit=50), "semantic", RetrievalCandidate)
                if not lexical and not semantic:
                    continue
                candidates = filter_entity_subjects(
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
                if entity_subject_ids and result.available and (not textual_intent or not result.items):
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
                        merged_items = rerank(list(merged.values()), query, preference)[:_MAX_RESULTS]
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
            not textual_intent or not lexical or not semantic or entity_candidates_exhausted
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
        if has_textual_intent(query):
            items = rerank(items, query, preference)
        return RetrievalResult(available=True, items=items[:_MAX_RESULTS])

    @staticmethod
    def _complete(result: RetrievalResult, personalization_missing: bool, fallback_type: str | None = None) -> RetrievalResult:
        result = RagRetrievalService._with_personalization_notice(result, personalization_missing)
        log_event("rag.retrieval.completed", candidateCount=len(result.items), success=result.available)
        if fallback_type is not None:
            log_event("rag.fallback.used", fallbackType=fallback_type, success=result.available)
        return result

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
        if is_error(response):
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        details_by_id: dict[int, Mapping[str, Any]] = {}
        for item in items_of(response):
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
            and is_safe_authority_detail(details_by_id[candidate.subject_id], query)
        ]
        if safe and evidence_lookup is not None:
            safe, evidence_ok = enrich_evidence(safe, token, evidence_lookup)
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
                and matches_query_filters(candidate.evidence, query)
            ]
        elif safe:
            # 未配置 Evidence 适配器时保留既有的业务侧回退行为；
            # 该模式下没有可用于评估更丰富字段的证据载荷。
            safe = [
                candidate
                for candidate in safe
                if matches_query_filters(candidate.details or {}, query)
            ]
        ranked = safe if not has_textual_intent(query) else rerank(safe, query, preference)
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
        if is_error(response):
            return RetrievalResult(available=False, items=[], reason="business_unavailable")
        allowed = set(allowed_subject_ids) if allowed_subject_ids is not None else None
        candidates: list[RetrievalCandidate] = []
        for item in items_of(response):
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

    # ---- 测试契约委托：既有测试直调这些私有方法，保留薄转发。----
    from app.rag.lexical import build_expression
    _build_expression = staticmethod(build_expression)
    _enrich_evidence = staticmethod(enrich_evidence)
    _map_evidence = staticmethod(map_evidence)
    _matches_query_filters = staticmethod(matches_query_filters)

    @staticmethod
    def _as_candidates(response, reason):
        return as_candidates(response, reason, RetrievalCandidate)

    @staticmethod
    def _with_personalization_notice(result: RetrievalResult, missing: bool) -> RetrievalResult:
        if not missing:
            return result
        return replace(result, personalization_notice="基于你当前的收藏还不多，先给你看热门")
