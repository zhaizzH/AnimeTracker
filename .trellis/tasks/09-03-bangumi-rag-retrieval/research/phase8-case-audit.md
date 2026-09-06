# Research: Phase 8 真实库 Golden Case 可追溯性审查

- Query: recent 导入后是否能从真实 MySQL 构造恰好 120 条可追溯 golden cases；需要哪些字段/查询证据；`search_index_release=0` 对真实评测的阻断；哪些 Phase 8 报告可以先生成
- Scope: mixed（本地 MySQL/Redis、评测资产、任务设计与实现代码）
- Date: 2026-09-06

## Findings

### 1. 当前真实运行库快照

本次通过 Agent `.env` 的只读连接检查 `localhost:3306/anime_tracker`，没有写入数据库。当前可作为快照基线的结果为：

| 数据/投影 | 当前数量或状态 | 证据查询 |
|---|---:|---|
| `subject` | 220 | `SELECT COUNT(*) FROM subject` |
| `subject.name` | 220 个非空且唯一 | `SELECT COUNT(*),COUNT(DISTINCT name) ...` |
| `subject.name_cn` | 179 个非空 | `SELECT COUNT(*) ...` |
| active `subject_alias` | 181 行，覆盖 179 个作品 | `SELECT COUNT(*),COUNT(DISTINCT subject_id) ...` |
| active `subject_meta_tag` | 805 行、52 个不同标签 | `GROUP BY name` |
| `subject.summary` | 195 个非空 | `CHAR_LENGTH(TRIM(summary))>0` |
| `person` | 9,275 | `SELECT COUNT(*) FROM person` |
| ``character`` | 2,129 | `SELECT COUNT(*) FROM \\`character\\`` |
| active `subject_person_credit` | 14,434 行，覆盖 102 个作品 | 关系表与 `person` 联查 |
| active `subject_character` | 2,160 行，覆盖 75 个作品 | 关系表与 ``character`` 联查 |
| active `character_actor` | 2,293 行，覆盖 72 个作品 | 关系表与 `person` 联查 |
| `subject_relation` | 6 行，3 种关系、3 对双向边 | `GROUP BY relation` |
| `search_document` | 220 条 `SUBJECT/v1/subject-profile-v1` | `GROUP BY entity_kind,index_version,profile_version` |
| Redis Vector Set | `rag:vectors:SUBJECT:v1` 有 220 个成员，1024 维、Q8 | `VCARD`/`VINFO` |
| `search_index_release` | 0 行，ACTIVE=0 | `SELECT ... FROM search_index_release` |

空气状态由 indexer 按 `air_date`、episode `status='NA'` 推导，而不是 `subject` 的持久列；当前推导分布为 `airing=149`、`finished=52`、`upcoming=15`、`unknown=4`。当前所有 `subject` 都是 `type=2, nsfw=0`。

### 2. 是否可以构造恰好 120 条

结论是“可以从当前真实库构造 120 条**数据可追溯的 case 定义**，但现在不能宣称已经完成 120-case 真实检索门禁”。原因如下：

- 可直接由事实表生成大量确定性 case：220 个标题、179 个中文标题、181 条别名、52 个 meta tag、2026 年/季度字段、评分/评分人数、air status、14,434 条人物职员边、2,160 条角色边、2,293 条声优边。仅标题/别名、结构化过滤、人物/角色/声优和降级/空结果即可超过 120 条候选定义。
- 系列关系不能单独支撑大量 case：当前只有 6 条 `subject_relation`，仅可生成少量真实关系 case；不能沿用旧文件中“进击的巨人/Fate/物语/高达”等假设系列并把本地 ID 当事实。
- 语义 case 不能只由计数生成。若要保留“治愈/悬疑/机甲”等主观语义，必须引用当前 `summary`、可信标签、关系/credit 文本或人工标注，并把标注证据固定到快照；否则只是模型/人工猜测，不是可追溯期望集合。
- 当前 `golden_cases.json` 仍有 53 条，`GoldenCase` 只含 `id/category/description/query/expectation`，没有快照、查询证据、版本或来源字段（`backend/agent/tests/evals/schemas.py:14-80`）。因此即使补到 120 条，现有 schema 也不足以证明“来自哪次 MySQL 快照、哪条 SQL、哪个 index/profile 版本”。
- 当前 53 条的 ID 虽然在 1–220 范围内，但名称和语义描述不能自动视为当前数据事实；现有报告也已记录其未绑定固定 MySQL/Redis 快照（`phase8-offline-evidence-report.md:17-23`）。重新生成时必须以真实查询返回的 `subject.id` 为准，不能按旧 case 的经典作品描述补号。

推荐的 120 条配额可以按“可事实验证优先”规划，而不是硬凑系列关系：标题/别名 30、结构化过滤 35、人物/角色/声优 25、关系 5、否定/边界/空结果 15、语义（有摘要/标签证据并人工复核）10。该配额只是生成计划；每条 case 仍需通过候选集合非空、结果稳定性和检索接口实际回放复核。

### 3. 每条 case 必须增加的追溯证据

现有 runner 接受注入的 `retrieve` 函数并计算 Recall/MRR/nDCG（`backend/agent/tests/evals/runner.py:24-177`），它不会读取 MySQL、Redis、Business 或快照。因此真实 case/报告至少应绑定以下字段：

1. `snapshot`: `capturedAt`（UTC）、数据库名、schema/migration 版本、数据快照摘要（各事实表计数和 hash）、代码 commit。
2. `query`: 与 Agent `RetrievalQuery` 对齐的原始结构化查询；自然语言/语义 query 另存规范化 query，不能只保留描述文本。
3. `expectation`: `expected_subject_ids`、`must_contain_all`、hard filters，以及“期望集合来自事实 SQL 还是人工语义标注”的类型。
4. `evidence`: 唯一 `evidenceId`、SQL 模板 ID、参数、来源表/关系、返回行的稳定 hash；关系 case 还应记录 `subject_relation.id`/`subject_person_credit.id`/`subject_character.id`/`character_actor.id`。
5. `index`: `indexVersion=v1`、`profileVersion=subject-profile-v1`、MySQL `search_document.content_hash` 样本、Redis key 和构建时间；若是故障/降级 case，还要记录预期 `fallbackType`。
6. `replay`: 生成时的 SQL 结果 ID 集合、在线回放结果 ID 集合、Business/Evidence 请求 traceId（禁止保存用户原文、token、向量或私有响应）。

最低事实 SQL 证据应覆盖：标题/别名来自 `subject`+`subject_alias`；过滤来自 `subject`+`subject_meta_tag`/`subject_tag`；人物/角色/声优来自三类新关系表与 `source_active=1`；系列关系来自 `subject_relation` 双向边；期望可展示字段来自 Business Evidence 查询，而不是直接把 `search_document` 当权威事实源。

### 4. `search_index_release=0` 的真实评测阻断

该状态是实际阻断，不是文档问题：

- Business lexical API 设计为必须读取 MySQL active release，并在无 ACTIVE 行时返回 HTTP 503；当前服务无法提供带 `indexVersion` 的真实词法候选。
- Agent 的设计要求先从 Business 取得 `indexVersion`，再查询同版本 Redis Vector Set 并做 RRF（`design.md:128-129`）。直接调用 `VSIM` 虽然可以测组件，但不能替代线上同版本检索链。
- 因此目前不能生成可信的端到端 Recall@20、MRR@10、nDCG@10、Business/Evidence hydrated P95、证据完整率，也不能把“Redis 220 成员”当作真实 Agent 召回通过。
- Gate 明确要求五份报告同版本、`requiredTotal=120`、`requiredPassed=120`、无失败，并要求 Recall/MRR/nDCG、P95 和人工检查达标（`backend/agent/jobs/indexer/gate.py:90-125`）。在 release=0 时若生成评测 JSON，只能是 `blocked`/诊断报告；填入 120 passed 会伪造发布证据。
- 版本激活也不应作为绕过评测的手段。必须先生成五份同一 `v1/subject-profile-v1` 的报告并通过 gate，再由 MySQL release store 激活。

### 5. Phase 8 可以先生成的报告

可以先做、且不需要 active release 的报告：

- **数据质量报告**：MySQL 事实表计数、`source_active`、subject type/NSFW、摘要/别名覆盖、关系外键孤儿检查、`search_document` 内容 hash 样本；需标记 `indexVersion=v1/profileVersion=subject-profile-v1`。
- **双投影容量/一致性报告**：MySQL `search_document` 220 条与 Redis Vector Set 220 成员、向量维度/Q8/VINFO、ID 集合差集、预计内存和直接 VSIM 组件 P95。它可以先生成，但不得写成“Business 端到端延迟”。
- **Golden case 数据集审计/生成报告**：可以从 SQL 生成候选并记录 120 条配额、每条 `evidenceId`、快照 hash 和未覆盖场景；这份报告不等于 eval gate 通过。
- **离线故障矩阵报告**：现有 mock/contract 测试可以继续记录 Redis、Embedding、Business、Evidence 故障的 fail-closed 行为；现有 52 passed 只能证明离线契约，不证明真实服务。

必须等待 active release 和可用 Business/Evidence 链后再生成“通过型”报告：

- **真实 120-case eval**：至少需要 Business lexical HTTP 200、同版本 Vector Set、RRF、Evidence 回查的真实回放；否则只能报告 blocked。
- **端到端 latency 报告**：可提前测直接 MySQL/Redis 组件，但 hydrated P95 必须在真实 Agent→Business→Evidence 链路测量。
- **人工证据报告**：可以先审查 case 的 SQL/摘要证据，但要达到发布 gate 的 20 条人工检查，必须审查实际检索结果和 EvidenceCandidate 来源；当前 Business 503 时不能给严重错误=0 的通过结论。
- **24 小时灰度/回滚报告**：release 未激活前不能开始。

## Files found

- `backend/agent/tests/evals/golden_cases.json` — 当前 53 条评测资产，期望 ID 未绑定运行库快照。
- `backend/agent/tests/evals/schemas.py` — GoldenCase/Expectation 结构，缺少 snapshot/evidence/index 追溯字段。
- `backend/agent/tests/evals/runner.py` — 注入式离线 runner，只消费 query 和 ID 列表。
- `backend/agent/jobs/indexer/gate.py` — 五份报告、120/120、指标和版本一致性门禁。
- `backend/agent/jobs/indexer/repository.py:115-171` — subject profile 的年份、季度、评分、热度、air status、标签、credit、relation 数据来源。
- `.trellis/tasks/09-03-bangumi-rag-retrieval/prd.md` — AC3/AC4/AC6 验收约束。
- `.trellis/tasks/09-03-bangumi-rag-retrieval/design.md` — active release、同版本查询和评测阈值设计。
- `.trellis/tasks/09-03-bangumi-rag-retrieval/implement.md` — Phase 8 未完成清单。
- `.trellis/tasks/09-03-bangumi-rag-retrieval/phase5-7-implementation-report.md` — 当前双投影、recent 导入和 release=0 运行记录。
- `.trellis/tasks/09-03-bangumi-rag-retrieval/phase8-offline-evidence-report.md` — 离线测试通过但真实门禁未满足的现有报告。

## Related specs

- `.trellis/spec/backend/agent-guidelines.md` — recent 导入失败必须 fail-closed，保留 checkpoint；本审查没有修改该规范。
- `.trellis/spec/backend/agent-rag-retrieval.md` — 如存在则应继续核对 EvidenceCandidate、版本一致性和降级约束；当前任务上下文未要求修改 spec。

## Caveats / Not Found

- `search_index_release` 当前查询结果为空；本次没有激活 release，也没有修改任何数据库、Redis、代码或 golden case。
- `rag_index_job` 当前状态为 `INDEXED=118, PENDING=102`，但 `search_document` 和 Vector Set 均为 220；这说明历史任务队列状态与投影快照不一致，质量报告必须同时记录三者并解释，不能只引用旧的“220 indexed”文字。
- 当前 `subject_relation` 只有 6 行，关系 case 覆盖不足；不要用旧 golden case 的虚构系列集合补足。
- 任务现有运行报告记录 DashScope embedding smoke 仍为 `EmbeddingUnavailable`；本次研究未重新发起外部 embedding 请求。因此语义 case 的向量回放和 embedding 故障/恢复证据仍未完成。
- 当前输出未调用外部网络或外部文档；结论基于本地代码、任务文档和只读 MySQL/Redis 查询。
