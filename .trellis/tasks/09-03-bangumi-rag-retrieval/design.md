# 全量 Bangumi 数据与 RAG 检索闭环设计

## 1. 设计目标

在不新增数据库或消息中间件的前提下，把当前“条目级候选召回”升级为可运营的自然语言找番与可解释推荐系统：MySQL 保存权威事实，Redis/RediSearch 保存可重建索引，Agent 只基于权威回查后的证据回答。

## 2. 边界与不变量

- MySQL 是唯一权威事实库；Redis 索引、MinIO 快照和未来图投影都可从 MySQL/原始快照重建。
- 用户查询不能直接拼接 RediSearch 或 SQL 表达式；必须先转换为受限强类型查询对象。
- 结构化事实走 SQL/Business 工具，主观语义走全文与向量召回；LLM 不得用参数记忆填补数据库事实。
- 共享索引不包含用户私有收藏、评论、JWT、聊天正文或其他个人数据。
- 新 schema 必须同时提供空库初始化定义和存量库前向迁移方案；绝不对非空库执行 `db-schema.sql`。
- 索引只通过 shadow version + gate + alias 切换发布，旧版本保留到回滚窗口结束。

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
Indexer ── deterministic profiles + embedding ─► Redis shadow index
                                                     │
Typed query planner                                   │
  ├─ SQL exact filters / entity resolution            │
  └─ BM25 + KNN + RRF ────────────────────────────────┘
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
3. 结构化条件产生受限过滤器；不允许模型输出原始 Redis 查询语法。
4. Subject profile 分别进行 BM25 与 KNN，各自取候选后用 RRF 融合。
5. 合并关系扩展候选，保留每条来源与匹配原因。
6. Business 批量回查类型、NSFW、有效状态和展示证据；回查失败的候选被丢弃。
7. 可选 reranker 只处理已验证候选；失败时回退确定性 RRF/规则排序。

Redis 当前手写 BM25 + KNN + RRF 可继续使用；是否迁移原生 `FT.HYBRID` 作为独立兼容性优化，不是首版前置条件。

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
- 冷门条目、无结果、Redis/Embedding/Business 失败降级。

指标：Recall@20、MRR@10、nDCG@10、硬过滤正确率、证据完整率、无依据陈述率、Redis P95、Business 回查后 P95。具体阈值先以当前 120-case 计划中的目标作为候选，由基线结果校准并在启用前锁定。

结构化事件只记录 traceId、indexVersion、候选/过滤数量、fallbackType、延迟和错误码；禁止记录用户原文、完整回答、向量、API Key、JWT 或私有收藏。

## 9. 技术栈决策

- Adopt：MySQL、Redis/RediSearch、MinIO、FastAPI/LangGraph、现有 Embedding provider 抽象、可失败降级的 reranker。
- Later：Neo4j（稳定三跳以上查询/图算法 + SQL 基准失败）、Elasticsearch（中文/拼音 golden cases 失败）、Milvus（Redis 容量/P95 失败）、RabbitMQ（需要跨机器 worker 与背压）、MongoDB（现有 Trace/聊天存储不够）。
- 参考项目只复用职责分离、rewrite/retrieve/rerank/format、来源元数据和 Trace 思路，不复制其全部中间件。

## 10. 迁移、兼容与回滚

### MySQL

1. 备份并记录目标库状态。
2. 执行只新增的前向 DDL，保留旧 `subject_credit` 和旧字段。
3. 发布兼容读取/写入代码并完成回填校验。
4. 切换到新关系表；旧表删除另建后续任务。

任一步失败时停止后续步骤；应用回退到旧读取路径，新表保留用于排查，不执行破坏性逆迁移。

### Redis

- 新 profile/index version 建 shadow index。
- gate 未通过不切 alias；切换后指标异常立即将 alias 指回旧 index。
- 回滚窗口结束前不删除旧 index。

### 应用

- 通过功能开关分别控制新 importer relation path、entity backfill、entity indexing、evidence retrieval 和 RAG enablement。
- 每个开关关闭时保留当前 Business 搜索回退；失败必须可观测，不能伪装空结果。

## 11. 主要风险

- API 无可靠全局增量流，完整性依赖周期复核和数据质量报告。
- Person/Character 全详情形成大量 N+1 请求，必须渐进回填并尊重限速。
- 中文分词、拼音和别名召回可能成为 Redis 短板，必须用 golden cases 决策，而不是提前引入 Elasticsearch。
- 跨层变更范围大；按数据契约、导入、索引、检索、评测顺序交付，禁止一次性打开全部开关。
