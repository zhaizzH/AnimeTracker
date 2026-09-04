# 最终跨层质量检查报告

日期：2026-09-04
范围：Phase 3 导入、Phase 5 多实体索引/outbox、Phase 6 Business 精确查询、Evidence fail-closed，以及 Phase 7 结构化实体 ID、实体名称与受限查询规划切片。

## 结论

代码级门禁通过；任务仍不能宣称生产 RAG 已启用。当前实现已把 Subject、Episode、Person、Character 的事实写入、索引任务和证据回查接通，但真实 MySQL/Redis/MinIO/Embedding/Bangumi API 与灰度发布尚未执行。

## 已通过

- 导入成功在同一事务写入旧 `rag_index_job` 与通用 `search_index_job`；完整响应保护、幂等键和失败重试已覆盖。
- 多实体 indexer 生产入口支持四类实体、profile hash 漂移、tombstone、Redis shadow HASH 和旧 Subject 队列兼容。
- Business `POST /api/client/evidence/resolve` 支持 SUBJECT/PERSON/CHARACTER/ACTOR，SQL 使用参数绑定并过滤 `type=2`、`nsfw=0`、`import_status=1`、`source_active=1`。
- Evidence API 异常、错误、部分或不安全响应统一 fail-closed；Agent 优先使用 Business 返回的 `sourceId/sourceUrl/sourceFetchedAt`。

## 未通过/未验证

1. AC1/AC9：未在临时空库、带旧数据库、备份恢复链路执行真实 DDL/前向迁移；详情回填和索引仍缺真实 MinIO/数据库运行报告。
2. AC4：结构化 `person_ids`、`character_ids`、`actor_ids`、`relation_subject_ids`、受控 `entity_name/entity_kind` 与明确中文条件规划已接入 Python `RetrievalQuery`、RAG 工具和 Business `/resolve`；名称从版本化实体 shadow index 解析，PERSON/CHARACTER 同名候选按名称约束取并集，ACTOR 保留关系语义，`RELATION_SUBJECT` 名称映射到 SUBJECT shadow 文档后沿 `subject_relation` 双向扩展；规划器仅补全明确的年份/季度/播出状态/评分/评分人数，显式字段优先；Redis Top-50 不足时改走精确权威回查，Redis 与 Business fallback 均执行 allowlist，解析异常 fail-closed。通用自然语言查询规划（含复杂否定和自由关系表达）仍需后续切片。
3. AC6/AC7：已有 53 条 golden cases 和确定性指标 runner，但没有绑定真实快照的 Recall/MRR/nDCG/过滤正确率/证据完整率/P95 基线，也未完成故障演练、shadow alias 灰度和 24 小时观测。
4. AC8：当前没有新增 Neo4j/Elasticsearch/Milvus/RabbitMQ/MongoDB；是否引入仍按评测和容量指标决定。

## 验证证据

- `backend/agent` 受影响范围：**166 passed**（importer/backfill/indexer/rag/adapters）。
- `backend/agent` 全量：**224 passed，1 deselected**；被排除的是依赖 Windows `tmp_path` 的自定义 golden loader 测试，环境临时目录 ACL 返回 WinError 5；同一逻辑使用工作区文件手工验证通过。
- `backend/agent` `compileall -q app jobs`：通过。
- `backend/business` `mvn -B test`：**30 passed，BUILD SUCCESS**。
- `git diff --check`：通过（仅 CRLF 转换提示）。
- Phase 7 结构化实体筛选、名称解析与规划：定向测试 **67 passed**，RAG/适配器范围 **81 passed**；Business HTTP `/resolve` 契约、`RELATION_SUBJECT` 服务、名称转义/类型映射、规划器显式字段优先和 fail-closed 测试已覆盖。

## 建议顺序

先执行真实迁移/索引基础设施门禁，再完善 Phase 7 的复杂否定与自由关系查询规划，最后用固定快照跑评测后决定是否需要额外中间件。

## Phase 7 硬化附录（2026-09-04）

- 修复关系语义：新增 `RELATION_SUBJECT`，Business 通过 `subject_relation` 双向参数化查询；`SUBJECT` 仍保持精确 ID 兼容。
- 修复召回窗口：实体 allowlist 在 Redis Top-50 无命中时走最多 50 个 ID 的精确 Business 回查，并复用年份、季度、评分、热度、标签、状态过滤。
- 修复输入/响应边界：RAG 工具使用严格正整数列表；`/resolve` 根类型、列表字段、`active/type/nsfw` 任一缺失或不安全时 fail-closed。
- 复核结果：上述边界测试、关系服务测试和工具 schema 测试均通过；未引入 Neo4j 等额外中间件。
