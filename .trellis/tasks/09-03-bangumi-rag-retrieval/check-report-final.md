# 最终跨层质量检查报告

日期：2026-09-05
范围：Phase 3 导入、Phase 5 多实体索引/outbox、Phase 6 Business 精确查询、Evidence fail-closed，以及 Phase 7 结构化实体 ID、实体名称与受限查询规划切片。

## 结论

代码级门禁通过；任务仍不能宣称生产 RAG 已启用。当前实现已把 Subject、Episode、Person、Character 的事实写入、索引任务和证据回查接通，并修复 Spring Boot 的 `Character` 类型别名启动冲突；真实 MySQL 已完成临时库验证，但当前 Redis 没有 RediSearch 模块，MinIO/Embedding/Bangumi API 与灰度发布尚未执行。

## 已通过

- 导入成功在同一事务写入旧 `rag_index_job` 与通用 `search_index_job`；完整响应保护、幂等键和失败重试已覆盖。
- 多实体 indexer 生产入口支持四类实体、profile hash 漂移、tombstone、Redis shadow HASH 和旧 Subject 队列兼容。
- Business `POST /api/client/evidence/resolve` 支持 SUBJECT/PERSON/CHARACTER/ACTOR，SQL 使用参数绑定并过滤 `type=2`、`nsfw=0`、`import_status=1`、`source_active=1`。
- Evidence API 异常、错误、部分或不安全响应统一 fail-closed；Agent 优先使用 Business 返回的 `sourceId/sourceUrl/sourceFetchedAt`。

## 未通过/未验证

1. AC1/AC9：MySQL 8.4.9 已完成临时空库初始化、旧表模拟前向迁移和二次幂等迁移；真实存量数据备份/恢复、详情回填和索引仍缺真实 MinIO/数据库运行报告。
2. AC4：结构化 `person_ids`、`character_ids`、`actor_ids`、`relation_subject_ids`、受控 `entity_name/entity_kind` 与明确中文条件规划已接入 Python `RetrievalQuery`、RAG 工具和 Business `/resolve`；名称从版本化实体 shadow index 解析，PERSON/CHARACTER 同名候选按名称约束取并集，ACTOR 保留关系语义，`RELATION_SUBJECT` 名称映射到 SUBJECT shadow 文档后沿 `subject_relation` 双向扩展；规划器仅补全明确的年份/季度/播出状态/评分/评分人数，显式字段优先；Redis Top-50 不足时改走精确权威回查，Redis 与 Business fallback 均执行 allowlist，解析异常 fail-closed。通用自然语言查询规划（含复杂否定和自由关系表达）仍需后续切片。
3. AC6/AC7：已有 53 条 golden cases 和确定性指标 runner，但没有绑定真实快照的 Recall/MRR/nDCG/过滤正确率/证据完整率/P95 基线，也未完成故障演练、shadow alias 灰度和 24 小时观测。
4. AC8：当前没有新增 Neo4j/Elasticsearch/Milvus/RabbitMQ/MongoDB；是否引入仍按评测和容量指标决定。
5. RAG 基础设施门禁：应用配置的 Redis 可连接，但服务端仅加载 `vectorset`，`FT.CREATE`、`FT.SEARCH`、`FT._LIST` 均为 unknown command；现有 indexer/名称解析依赖 RediSearch，故 RAG 索引构建与 alias 发布暂不可验证。详见 `phase8-redis-report.md`。
6. HTTP 端到端门禁：本次复核中 `127.0.0.1:8080/actuator/health` 仍连接被拒；Agent 实际健康路由是 `/api/client/agent/health`（不是根路径 `/health`），已返回 HTTP 200。Business/Evidence 真实链路仍未验证。
7. Spring Boot 启动门禁：已修复 `Character` 与 `java.lang.Character` 的 MyBatis alias 冲突，新增回归测试并通过完整 Maven 构建；详见 `phase8-springboot-startup-report.md`。

## 验证证据

- `backend/agent` 受影响范围：**167 passed**（importer/backfill/indexer/rag/adapters）。
- `backend/agent` 全量：**226 passed**。
- `backend/agent` `compileall -q app jobs`：通过。
- `backend/business` `mvn -B clean test`：**31 passed，BUILD SUCCESS**；包含 MyBatis alias 回归测试。
- MySQL 8.4.9 临时库：初始化、旧表前向迁移、重复迁移和 9 张新表/3 个兼容列断言通过；验证库已删除。
- Redis 8.8.0：连接与 PING 通过；模块列表仅有 `vectorset`，RediSearch 命令探针失败。
- Business `8080/actuator/health`：连接被拒；Agent `8090/api/client/agent/health`：HTTP 200，返回 `status=ok`、`llm_configured=true`。本次探测未触发写操作。
- `git diff --check`：通过（仅 CRLF 转换提示）。
- Phase 7 结构化实体筛选、名称解析与规划：定向测试 **68 passed**，RAG/适配器范围 **82 passed**；Business HTTP `/resolve` 契约、`RELATION_SUBJECT` 服务、名称转义/类型映射、规划器显式字段优先和 fail-closed 测试已覆盖。
- Spring Boot 启动回归：`Character` 注册为 `BangumiCharacter`，内置 `Character` 保持 `java.lang.Character`，测试通过。

## 建议顺序

先提供启用 RediSearch 的 Redis Stack/Redis Enterprise 实例并完成索引基础设施门禁，再完善 Phase 7 的复杂否定与自由关系查询规划，最后用固定快照跑评测后决定是否需要额外中间件。

## Phase 7 硬化附录（2026-09-04）

- 修复关系语义：新增 `RELATION_SUBJECT`，Business 通过 `subject_relation` 双向参数化查询；`SUBJECT` 仍保持精确 ID 兼容。
- 修复召回窗口：实体 allowlist 在 Redis Top-50 无命中时走最多 50 个 ID 的精确 Business 回查，并复用年份、季度、评分、热度、标签、状态过滤。
- 修复输入/响应边界：RAG 工具使用严格正整数列表；`/resolve` 根类型、列表字段、`active/type/nsfw` 任一缺失或不安全时 fail-closed。
- 复核结果：上述边界测试、关系服务测试和工具 schema 测试均通过；未引入 Neo4j 等额外中间件。
