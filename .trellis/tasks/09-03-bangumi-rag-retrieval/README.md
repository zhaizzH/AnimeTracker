# bangumi-rag-retrieval 文档索引

更新时间：2026-09-05

## 当前状态

- 任务状态：`in_progress`。
- Phase 1–4 已完成并有验证证据；Phase 5–7 的 profile、outbox、RRF、Evidence 与 fail-closed 基础可复用。
- 用户已同意把检索技术方向调整为 **MySQL 8.4 `ngram` FULLTEXT + Redis 8 Vector Set + Python RRF**。
- 新路线目前只有规划，MySQL lexical/Redis vector 双投影、release 发布、120-case 真实门禁和 24 小时灰度尚未实现。

## 当前权威文档

1. [prd.md](./prd.md)：产品目标、需求边界与验收标准。
2. [design.md](./design.md)：当前有效的技术架构、版本契约与回滚设计。
3. [implement.md](./implement.md)：已完成状态和新路线待实施清单。
4. [task.json](./task.json)：Trellis 任务状态与机器可读元数据。
5. [MySQL FULLTEXT + Redis Vector Set 决策](./research/mysql-fulltext-redis-vectorset-decision.md)：技术路线选择、替代方案与门槛。

## 当前有效证据

| 文档 | 结论 |
|---|---|
| [Phase 2 映射报告](./phase2-mapping-report.md) | Java/Python 实体映射与旧 `subject_credit` 兼容已验证 |
| [Phase 4 回填报告](./phase4-backfill-report.md) | 覆盖率、失败原因和 stale 报告契约已验证 |
| [Phase 6 Business 报告](./phase6-business-report.md) | Evidence 与结构化关系查询契约已验证 |
| [MySQL 迁移报告](./phase8-mysql-migration-report.md) | 实际库迁移、21 张表和幂等性已验证 |
| [Spring Boot 启动报告](./phase8-springboot-startup-report.md) | MyBatis alias 与健康检查已验证 |
| [离线评测报告](./phase8-offline-evidence-report.md) | 离线指标/故障矩阵通过；不能替代真实发布 gate |

## 历史证据

`history/` 保存已被后续实现或新技术路线取代的检查报告。它们只用于追溯，不表示当前状态：

- [初始全量审查](./history/check-report.md)
- [Phase 3 专项审查](./history/check-report-phase3.md)
- [RediSearch 路线最终审查](./history/check-report-final.md)
- [RediSearch Shadow Index 报告](./history/phase5-indexer-report.md)
- [RediSearch 实体名称报告](./history/phase7-entity-name-report.md)
- [RediSearch 环境阻塞报告](./history/phase8-redis-report.md)

## 维护规则

- 当前事实只更新 `prd.md`、`design.md`、`implement.md` 和对应的当前证据报告。
- 被新结论替代的报告移入 `history/` 并保留历史说明，不直接删除审查证据。
- 不把离线 mock 测试、健康检查或旧 RediSearch 报告写成新路线已完成。
