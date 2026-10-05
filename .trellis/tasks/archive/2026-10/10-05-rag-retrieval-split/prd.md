# rag retrieval.py 按管线阶段拆分

> 来源：grill 会话收敛。目标可维护性，手法 move-only 重构 + 顺手清明显死码。

## Goal

`backend/agent/app/rag/retrieval.py`（1030 行，`RagRetrievalService` 23 方法）按管线阶段拆 4 文件，`retrieval.py` 只留 dataclass + service 编排。行为零变化。

## Facts（已核实）

- 服务方法分布（ast 行号）：
  - 实体解析：`_resolve_entity_subject_ids` 293-369、`_lookup_entity_name` 372-417、`_safe_resolved_subject_ids` 420-455、`_is_safe_subject_response` 458-473、`_filter_entity_subjects` 476-487
  - 词法/表达式：`escape_redis_term` 23-25、`_expressions` 497-505、`_build_expression` 507-528、`_lexical_terms` 531-541
  - 权威回查/证据：`_authoritative_allowlist_result` 255-291、`_authoritative_result` 543-601、`_business_fallback` 603-644、`_enrich_evidence` 647-703、`_is_safe_evidence` 706-716、`_map_evidence` 719-757、`_is_safe_authority_detail` 760-777、`_matches_query_filters` 780-825
  - 候选/rerank：`_as_candidates` 828-865、`_rerank` 868-897、`reciprocal_rank_fusion` 47-65、尾部纯函数 905-1030（`_preference_score`/`_item_year`/`_item_quarter`/`_freshness` 等）
  - 编排留驻：`retrieve` 98-253、`_complete` 490-495、`_with_personalization_notice` 900-903
- 测试网够：tests/rag 9 文件（`test_lexical_contract`、`test_evidence_contract`、`test_fault_matrix` 等），8810 行测试。
- `_REDIS_RESERVED` 与 `_REDIS_TAG_RESERVED` 语义不同（后者保逗号），**不合**。
- 私有方法改为模块级函数，service 通过 self 委托或直接调用。

## Requirements

- **R1** 拆 `entity_resolution.py` / `lexical.py` / `authority_enrich.py` / `rerank.py`，`retrieval.py` 留 `RetrievalCandidate`/`RetrievalResult`/`RagRetrievalService` 编排（`retrieve`）。
- **R2** move-only：不改任何逻辑、参数、fail-closed 语义；`_` 方法转模块级函数。
- **R3** 顺手清明显死码（未引用函数/导入），其余不动。
- **R4** `uv run pytest` 全绿，数字与拆前一致。

## Acceptance Criteria

- [ ] AC1 retrieval.py ≤ ~400 行，4 个阶段文件存在且 import 无环
- [ ] AC2 pytest 全绿（记录拆前/拆后数字）
- [ ] AC3 grep 确认无私有方法名残留在 retrieval.py（除留驻三个）
- [ ] AC4 死码清理逐条列在 implement 记录

## Out of Scope

- jobs/ 巨型 main（importer 862 行 / indexer 785 行）拆分 — 排后续独立 task。
- 两套转义表合并。
- 任何算法/行为改动。
