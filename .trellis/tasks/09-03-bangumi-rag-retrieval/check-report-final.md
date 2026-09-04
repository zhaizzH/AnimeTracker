# 最终跨层质量检查报告

日期：2026-09-04
范围：Phase 3 导入、Phase 5 多实体索引/outbox、Phase 6 Business 精确查询、Evidence fail-closed。

## 结论

代码级门禁通过；任务仍不能宣称生产 RAG 已启用。当前实现已把 Subject、Episode、Person、Character 的事实写入、索引任务和证据回查接通，但真实 MySQL/Redis/MinIO/Embedding/Bangumi API 与灰度发布尚未执行。

## 已通过

- 导入成功在同一事务写入旧 `rag_index_job` 与通用 `search_index_job`；完整响应保护、幂等键和失败重试已覆盖。
- 多实体 indexer 生产入口支持四类实体、profile hash 漂移、tombstone、Redis shadow HASH 和旧 Subject 队列兼容。
- Business `POST /api/client/evidence/resolve` 支持 SUBJECT/PERSON/CHARACTER/ACTOR，SQL 使用参数绑定并过滤 `type=2`、`nsfw=0`、`import_status=1`、`source_active=1`。
- Evidence API 异常、错误、部分或不安全响应统一 fail-closed；Agent 优先使用 Business 返回的 `sourceId/sourceUrl/sourceFetchedAt`。

## 未通过/未验证

1. AC1/AC9：未在临时空库、带旧数据库、备份恢复链路执行真实 DDL/前向迁移；详情回填和索引仍缺真实 MinIO/数据库运行报告。
2. AC4：Business 关系解析接口已就绪，但 Python `RetrievalQuery` 尚无 person/character/relation 受限字段，/resolve 尚未接入自然语言查询规划；“找某声优参与作品”仍需 Phase 7。
3. AC6/AC7：已有 53 条 golden cases 和确定性指标 runner，但没有绑定真实快照的 Recall/MRR/nDCG/过滤正确率/证据完整率/P95 基线，也未完成故障演练、shadow alias 灰度和 24 小时观测。
4. AC8：当前没有新增 Neo4j/Elasticsearch/Milvus/RabbitMQ/MongoDB；是否引入仍按评测和容量指标决定。

## 验证证据

- `backend/agent` 受影响范围：**131 passed**（importer/backfill/indexer/rag/adapters）。
- `backend/agent` 全量：**189 passed，1 deselected**；被排除的是依赖 Windows `tmp_path` 的自定义 golden loader 测试，环境临时目录 ACL 返回 WinError 5；同一逻辑使用工作区文件手工验证通过。
- `backend/agent` `compileall -q app jobs`：通过。
- `backend/business` `mvn -B test`：**29 passed，BUILD SUCCESS**。
- `git diff --check`：通过（仅 CRLF 转换提示）。

## 建议顺序

先执行真实迁移/索引基础设施门禁，再实现 Phase 7 的受限实体查询规划，最后用固定快照跑评测后决定是否需要额外中间件。
