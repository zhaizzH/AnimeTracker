# 全量 Bangumi 数据与 RAG 检索闭环设计

## 1. 设计目标

在不新增数据库或消息中间件的前提下，把当前“条目级候选召回”升级为可运营的自然语言找番与可解释推荐系统：MySQL 保存权威事实、版本化词法投影与发布指针，现有 Redis 8 Vector Set 保存可重建向量，Agent 只基于权威回查后的证据回答。

## 2. 边界与不变量

- MySQL 是唯一权威事实库和 release 指针来源；MySQL FULLTEXT 投影、Redis 向量、MinIO 快照和未来图投影都可从 MySQL/原始快照重建。
- 用户查询不能直接拼接 `MATCH ... AGAINST`、Vector Set `FILTER` 或其他存储表达式；必须先转换为受限强类型查询对象。
- 结构化事实走 SQL/Business 工具，主观语义走全文与向量召回；LLM 不得用参数记忆填补数据库事实。
- 共享索引不包含用户私有收藏、评论、JWT、聊天正文或其他个人数据。
- 新 schema 必须同时提供空库初始化定义和存量库前向迁移方案；绝不对非空库执行 `db-schema.sql`。
- 索引只通过 shadow version + gate + MySQL active release 切换发布；词法结果返回 `indexVersion`，Agent 必须查询同版本 Vector Set。旧版本保留到回滚窗口结束。

## 3. 目标架构

```text
Bangumi v0 API
  ├─ raw JSON / image ─────────────────────────► MinIO
  └─ normalize + replace-set / upsert
                    │
                    ▼
MySQL authoritative catalog
  ├─ subject / episode / tag / relation
  ├─ person / character / credits / actors
  ├─ import + detail-backfill checkpoints
  └─ search_index_job outbox
                    │
                    ▼
Indexer ── deterministic profiles ───────► MySQL FULLTEXT shadow projection
       └── embedding ────────────────────► Redis Vector Set shadow key
                                                     │
Typed query planner                                   │
  ├─ SQL exact filters / entity resolution            │
  └─ MATCH...AGAINST + VSIM + RRF ───────────────────┘
                    │
                    ▼
Business evidence batch lookup → optional rerank → compact evidence blocks
                    │
                    ▼
LangGraph search / discover / recommend → SSE answer
```

## 4. 数据模型

### 4.1 新实体

`person`

- 内部 `id` 与唯一 `bangumi_person_id`。
- `person_type` 保留上游 person/company/group 类型；不可用字符串 `MAIN` 代替。
- `name`、`summary`、`career_json`、`infobox_json`、图片源与存储状态。
- `detail_status`（SUMMARY_ONLY/PENDING/COMPLETE/FAILED）、`source_hash`、`source_fetched_at`、`last_seen_import_id`、`source_active`。

`character`

- 内部 `id` 与唯一 `bangumi_character_id`。
- `character_type` 保留角色/作品内组织类型，与现实制作组织分离。
- `name`、`summary`、`infobox_json`、图片与同样的详情/来源状态字段。

别名采用 `person_alias`、`character_alias` 独立表，保留外键和唯一约束；不使用无法建立真实外键的通用多态 alias 表。

### 4.2 新关系

- `subject_person_credit(subject_id, person_id, role, relation, sort_order, source_active)`。
- `subject_character(subject_id, character_id, relation, sort_order, source_active)`。
- `character_actor(subject_id, character_id, person_id, actor_relation, sort_order, source_active)`；保留 `subject_id`，避免把仅适用于某一动画版本的声优关系错误推广为全局事实。

关系表按完整成功响应执行事务性 replace-set：先在同一 subject/entity 范围标记旧集合，再 upsert 新集合，最后失效未出现项。分页或网络请求未完整成功时不得清空旧集合。

### 4.3 任务与版本

- `entity_detail_job(entity_kind, entity_id, source_id, status, attempts, next_retry_at, last_error_code, checkpoint, source_hash)`：渐进回填 Person/Character 详情。
- 将当前仅指向 subject 的 `rag_index_job` 演进为通用 `search_index_job(entity_kind, entity_id, index_version, profile_version, content_hash, status, attempts, next_retry_at, indexed_at)`。
- 通用任务表不承担事实外键；写任务前校验实体存在，消费者再次校验 `source_active`。实体删除会产生 delete/tombstone 工作。
- job 中的 `content_hash` 必须来自同一份规范化 profile；消费者发现实时 profile hash 与 job 不同，应废弃旧 job 并产生新版本，不能把新文本写到旧 hash 下。

新增两个可重建控制面对象：

- `search_document(entity_kind, entity_id, index_version, profile_version, title, aliases, lexical_text, content_hash, source_active, source_fetched_at)`：InnoDB 投影表，按 `(entity_kind, entity_id, index_version)` 唯一，`FULLTEXT(title, aliases, lexical_text) WITH PARSER ngram`。它不是事实源，允许按版本整体重建。
- `search_index_release(index_version, profile_version, status, activated_at, retired_at, active_slot)`：MySQL 中唯一的发布状态。`active_slot` 仅在 `ACTIVE` 时生成固定非空值并建立唯一约束，使数据库保证同一时刻只有一个 active release；Redis 不再保存具有发布决定权的 alias。

Vector Set 使用受控版本键：`rag:vectors:{entity_kind}:{index_version}`。元素 ID 只保存实体类型与数据库 ID，属性只保存过滤所需的非私有元数据；删除通过 `VREM`，查询通过 `VSIM`。

## 5. 导入与渐进回填

### 5.1 首轮可用导入

每个 Subject 完成：

1. 获取并保存完整 raw snapshot。
2. 修复 subject `eps/volumes/platform/total_episodes` 等映射，保存评分与收藏聚合。
3. 分页完整获取 episodes、persons、characters、subject relations。
4. 从 subject 端点响应保存 Person/Character 摘要和所有关系边。
5. 事务提交事实变更与对应 `search_index_job`；对象存储失败采用明确回退状态，不伪装完整。

### 5.2 后台详情回填

- 首轮为摘要实体创建 `entity_detail_job`，不阻塞 Subject 可检索状态。
- worker 按 checkpoint、限速、指数退避和最大尝试次数获取 Person/Character 详情。
- 回填可暂停、恢复和重复运行；详情失败只影响该实体的丰富字段，不删除已有摘要与关系。
- 没有全局 updated_at 时，周期性低速复核活跃/高价值实体；`last_modified` 不被误当作可靠实体更新时间。

### 5.3 全量与增量

- full/season/recent/since 继续发现 Subject；详情与关系由统一 subject pipeline 处理。
- 无上游全局变更流，因此增量只保证“已发现 Subject 的重新抓取”，不能声称绝对实时同步。
- 清理继续采用计划 → 摘要确认 → 执行；上游临时 404、认证隐藏或分页失败不能直接解释为删除。

## 6. 检索文档与索引

### 6.1 文档类型

- SUBJECT：标题、别名、简介、官方/可信标签、主要 credits、系列关系摘要。
- EPISODE：所属作品、集数、标题、简介、播出日期。
- PERSON：姓名、别名、类型、职业、简介、代表性参与关系。
- CHARACTER：姓名、别名、简介、所属作品、声优关系。

评分、排名、收藏人数、播出日期、NSFW、类型、状态等只作为 TAG/NUMERIC/SORTABLE 字段和 rerank 特征，不写入 embedding 正文。

### 6.2 面向“找番”的召回策略

最终候选始终是 Subject：

1. 精确名称解析：标题/别名/人物/角色名先走词法解析。
2. 人物或角色命中后，通过 MySQL 关系表扩展为 subject IDs。
3. Business 候选接口在 MySQL active release 上执行参数化 `MATCH ... AGAINST` 与结构化过滤，并始终返回候选和 `indexVersion`；纯向量查询也必须先取得该版本。
4. Agent 使用同一 `indexVersion` 查询 `rag:vectors:SUBJECT:{indexVersion}` 的 `VSIM`，再用现有 RRF 融合词法与语义候选。
5. 合并关系扩展候选，保留每条来源与匹配原因。
6. Business 批量回查类型、NSFW、有效状态和展示证据；回查失败的候选被丢弃。
7. 可选 reranker 只处理已验证候选；失败时回退确定性 RRF/规则排序。

当前 Redis 8.8 已确认支持 `VADD`、`VSIM`、`VREM`、`VSETATTR`、`VGETATTR`，但不支持 `FT.*`。首版直接使用 Vector Set，不安装 Redis Stack。向量默认采用 Vector Set 的 Q8 量化并由真实 Recall/容量门禁验证；若召回不足，先对比 `NOQUANT`，再决定是否更换组件。若 MySQL `ngram` 的中文/拼音词法指标或整体 P95 未达标，再以独立决策评估 OpenSearch/Elasticsearch；若向量容量或延迟仍未达标，再评估 Qdrant。

## 7. Agent 与证据契约

引入强类型 `EvidenceCandidate`：

- `subject_id`、标题、别名。
- `summary_excerpt`，带来源字段而非任意生成摘要。
- `matched_tags`、`matched_credits`、`matched_characters`、`matched_relations`。
- 评分、评分人数、收藏热度、播出状态和数据时间。
- `retrieval_reason` 与 `source_refs`；不暴露 embedding、内部 Redis score 细节或原始私有响应。

search/discover/recommend 三个工具共用同一 retrieval use case，只改变查询默认值和个性化策略。领域 Prompt 明确要求引用证据；若证据不足，返回可执行的放宽建议而不是模型补写。

SSE 事件类型不扩展时无需改前端状态机；若要展示结构化引用卡片，应另行设计向后兼容事件并同步 OpenAPI/shared types。

## 8. 评测、观测与发布

首版至少 50 条确定性 golden cases：

- 中文名、日文名、英文名、别名与近似标题。
- 年份/季度/播出状态/评分/热度/标签组合过滤。
- 主观语义与否定条件。
- 人物、角色、声优、制作公司及系列关系。
- 冷门条目、无结果、MySQL FULLTEXT/Redis Vector Set/Embedding/Business 失败降级。

指标：Recall@20、MRR@10、nDCG@10、硬过滤正确率、证据完整率、无依据陈述率、MySQL lexical P95、Redis VSIM P95、Business 回查后 P95。继续使用现有 gate 候选阈值：覆盖率 ≥99.5%、Recall@20 ≥0.85、MRR@10 ≥0.90、nDCG@10 ≥0.75、向量召回 P95 <250ms、权威回查后 P95 <500ms、Redis 预计内存占用 ≤60%，并要求 120/120 必选评测通过及至少 20 条人工证据检查无严重错误。

五份报告必须绑定同一 `indexVersion/profileVersion`。激活时只在 MySQL 事务中切换 `search_index_release`；Agent 从 Business 词法响应取得该版本并查询对应 Vector Set，因此不会出现 MySQL 新版本配 Redis 旧版本的静默混用。回滚同样只切回上一条已通过 gate 的 release。

结构化事件只记录 traceId、indexVersion、候选/过滤数量、fallbackType、延迟和错误码；禁止记录用户原文、完整回答、向量、API Key、JWT 或私有收藏。

## 9. 技术栈决策

- Adopt：MySQL 8.4 `ngram` FULLTEXT、Redis 8 Vector Set、MinIO、FastAPI/LangGraph、现有 Embedding provider 抽象、Python RRF 与可失败降级的 reranker。
- Do not adopt：Redis Stack/RediSearch。原因是当前 Redis 已具备向量能力，词法和结构化过滤可由现有 MySQL 承担，新增运行时不能解决尚未出现的指标失败。
- Later：OpenSearch/Elasticsearch（中文/拼音或全文 P95 golden gate 失败）、Qdrant（Redis Vector Set 容量/召回/P95 失败）、Neo4j（稳定三跳以上查询/图算法 + SQL 基准失败）、Milvus（Qdrant/Vector Set 均不足）、RabbitMQ（需要跨机器 worker 与背压）、MongoDB（现有 Trace/聊天存储不够）。
- 参考项目只复用职责分离、rewrite/retrieve/rerank/format、来源元数据和 Trace 思路，不复制其全部中间件。

## 10. 迁移、兼容与回滚

### MySQL

1. 备份并记录目标库状态。
2. 执行只新增的前向 DDL，保留旧 `subject_credit` 和旧字段。
3. 发布兼容读取/写入代码并完成回填校验。
4. 切换到新关系表；旧表删除另建后续任务。

任一步失败时停止后续步骤；应用回退到旧读取路径，新表保留用于排查，不执行破坏性逆迁移。

### MySQL FULLTEXT 与 Redis Vector Set

- 新 `profileVersion/indexVersion` 同时建立 MySQL `search_document` shadow 行和版本化 Vector Set key。
- gate 未通过不把 `search_index_release` 置为 `ACTIVE`；发布后异常时在 MySQL 事务中切回上一版本。
- Business 词法 API 返回其实际查询的 `indexVersion`；Agent 只查询同名 Vector Set。任一版本缺失或不一致均 fail-closed 到现有 Business 精确搜索，不允许跨版本融合。
- 回滚窗口结束前不删除旧 `search_document` 版本或旧 Vector Set；清理属于独立确认操作。

### 应用

- 通过功能开关分别控制新 importer relation path、entity backfill、entity indexing、evidence retrieval 和 RAG enablement。
- 每个开关关闭时保留当前 Business 搜索回退；失败必须可观测，不能伪装空结果。

## 11. 主要风险

- API 无可靠全局增量流，完整性依赖周期复核和数据质量报告。
- Person/Character 全详情形成大量 N+1 请求，必须渐进回填并尊重限速。
- MySQL `ngram` 对中文标题有效，但拼音、同义词和长简介相关性可能不足；必须用 golden cases 决定是否引入 OpenSearch/Elasticsearch，而不是凭感觉升级。
- Vector Set 与 MySQL release 分属两个存储，不能做分布式事务；通过“先构建两份 shadow → 同版本 gate → MySQL 单点激活 → 查询携带版本”消除静默错配。
- 跨层变更范围大；按数据契约、导入、索引、检索、评测顺序交付，禁止一次性打开全部开关。
