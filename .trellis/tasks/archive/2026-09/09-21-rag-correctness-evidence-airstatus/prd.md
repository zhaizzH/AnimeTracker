# RAG 正确性：Evidence 重复ID 与播出状态

## Goal

修补两处 RAG 正确性缺陷：Evidence 重复合法 ID 的静默覆盖（绕过 fail-closed 完整性边界），以及 air-status 推断在两个函数间的自相矛盾（违反"单个首播日期不臆断完结"）。顺带评估两处相关健壮性项。

## Background

- Evidence 重复 ID：`app/rag/retrieval.py:668-688` `_enrich_evidence` 用 `by_id[subject_id]=row` 赋值，重复合法 ID 后者静默覆盖；完整性门禁只比对 key 集合（`expected_ids` vs `by_id.keys()`），重复在比对前已坍缩，无法发现。若 Business `/evidence/batch` 对同一合法 ID 返回两行（事实不同），错误行会被当权威证据送入模型上下文。当前无测试覆盖（`tests/rag` 无 dup/重复 用例）。spec `agent-guidelines.md:43`、`rag-retrieval-contract.md:22,85` 已标注"重复合法 ID 尚未拒绝"。
- air-status 分叉：`app/rag/retrieval.py:989-994` `_infer_air_status_name` 对过去日期直接 `FINISHED`；`app/rag/use_case.py:81-92` `_infer_air_status` 对过去日期且无权威状态返回 `UNKNOWN`。前者用于 `air_status` 过滤（`retrieval.py:800-805`），会把无权威状态的过期番当 FINISHED 纳入，违反保守原则。
- 事实（已核）：Business `/evidence/batch` 用 SQL 计算权威 `airStatus`（`EvidenceMapper.xml:22-32`，剧集感知、几乎不为 null），Python 推断只是极少走到的兜底；因此改严格几乎不损失召回。
- 相关健壮性：`HttpBusinessGateway.batch_subjects/batch_evidence/resolve_evidence/save_collection`（`business_http.py:70-141`）不校验外发 ID/类型（依赖上游 typed 工具）；多处 `except Exception`（`retrieval.py:225-227,146-149`、`main.py:176-177`）把不同根因坍缩为单一降级，错误分类偏粗。

## Requirements

1. Evidence 重复合法 ID：在 `_enrich_evidence` 增加行数/唯一性校验——`len(rows) != len(by_id)` 或出现重复合法 subjectId 时 fail-closed（`available=False, reason=evidence_unavailable, items=[]`），与既有"缺项/多项/非法 ID 即拒绝"一致；绝不静默后者胜。
2. air-status 统一：抽一个共享推断函数，`retrieval._infer_air_status_name` 与 `use_case._infer_air_status` 复用之，规则统一为——优先用权威 `airStatus`；无权威状态时，未来首播日期→UPCOMING，过去日期→UNKNOWN（不臆断 FINISHED/AIRING）。
3. 保持 `air_status` 过滤在 Evidence 权威值存在时按权威值判定；仅兜底路径受统一函数影响。
4. 评估（不一定本轮实现，design 决定）：适配器出参 ID/类型的纵深校验；静默 except 的错误分类细化（区分 version-missing / redis-down / embedding-error）。

## Acceptance Criteria

- [ ] Evidence 返回重复合法 ID → `available=False, reason=evidence_unavailable`，不把任何行送入模型上下文；补重复 ID 测试。
- [ ] 过去日期且无权威 airStatus 的条目在 `air_status=FINISHED` 过滤中被排除（判为 UNKNOWN）；有权威 airStatus 时按权威值；两处推断行为一致，抽自同一函数。
- [ ] 既有 RAG 故障矩阵、Evidence 完整性、检索过滤测试不回归；`uv run pytest` 全绿。
- [ ] design 明确记录 12e/12f 两项是本轮实现还是转入 backlog。

## Out of Scope

- 不改 Business `/evidence/batch` 或 `EvidenceMapper` 的 airStatus 计算（其为权威）。
- 不重写检索/重排算法。

## Notes

- 复杂任务：`task.py start` 前补 `design.md`（fail-closed 判定点、共享 air-status 函数放置、12e/12f 取舍）与 `implement.md`。
- 与 T4（测试补齐）协同：Evidence 重复 ID 测试可在本任务内补，孤儿区测试归 T4。
