# bangumi-rag-retrieval 文档索引

更新时间：2026-09-09

## 当前状态

- 任务状态：`completed`（待 Trellis 归档）。
- Phase 1–4 已完成并有验证证据；Phase 5–7 的 profile、双投影 indexer、RRF、Evidence 与 fail-closed 基础已实现并通过本地测试。
- 用户已同意把检索技术方向调整为 **MySQL 8.4 `ngram` FULLTEXT + Redis 8 Vector Set + Python RRF**。
- MySQL lexical/Redis Vector Set 双投影、Business lexical API、同版本 Agent 查询和 MySQL release store 已实现；真实实体投影、120-case `RELEASE_CANDIDATE` 评测、20 条人工证据检查、v1 激活及 24 小时灰度/回滚确认均已完成。
- recent 导入已补齐当前日历涉及的人物/角色摘要与关系；2026-09-06 直连 DashScope Embedding 成功，search index job 已全部完成，v1 release 已按 gate 结果激活。
- 已修复 Business `/subjects/batch` 缺少 `active` 字段的跨层契约，并同步 Java VO、OpenAPI 与测试；Evidence 现在补充由剧集状态推导的 `airStatus`。
- 2026-09-06 18:28（UTC+8）已重新真实访问 8080/8090 并只读核对 MySQL/Redis：Business/Agent/Evidence 均可用，当前真实库为 23 张表，Redis 实际使用 DB 1，四类双投影数量一致；激活后词法 API 实测返回 200。
- 2026-09-07 真实回放修复了 FULLTEXT 误命中、AIRING Evidence 过滤、纯结构化排序和语义标签加权；v1 五份报告均通过 gate，21:16 已激活 ACTIVE release，lexical API 实测返回 HTTP 200。

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
| [MySQL 迁移报告](./phase8-mysql-migration-report.md) | migration-002 的 21 表历史快照与 migration-003 后当前 23 表状态已区分 |
| [Spring Boot 启动报告](./phase8-springboot-startup-report.md) | MyBatis alias 与最新 8080/8090 健康检查已验证 |
| [离线评测报告](./phase8-offline-evidence-report.md) | 离线指标/故障矩阵通过；不能替代真实发布 gate |
| [Golden Case 定义集报告](./phase8-golden-case-definition-report.md) | 真实 MySQL 快照生成恰好 120 条可追溯定义；v1 已产生 120/120 `RELEASE_CANDIDATE` |
| [Phase 5–7 实现报告](./phase5-7-implementation-report.md) | 双投影、词法 API、版本化 VSIM、全量回填与本地测试已完成；v1 激活与灰度/回滚确认已完成 |
| [真实索引运行报告](./phase8-index-runtime-report.md) | v1 双投影 13,173 条完成，Redis/MySQL 数量一致；发布门禁与 v1 激活均已通过 |
| [本机真实访问审计](./phase8-live-runtime-audit.md) | 记录 8080/8090、MySQL、Redis 的实测命令、时间和结果 |
| [实时质量报告](./research/quality-v1.json) | v1 覆盖率 100%；存在 1 条 EPISODE_SHORTAGE 与 38 条 EPISODE_STATUS_DRIFT |
| [Shadow 评测报告](./research/eval-shadow-v1.json) | v1 真实回放 120/120 通过；保留 `SHADOW_ONLY` 诊断报告 |
| [Release Candidate 评测报告](./research/eval-v1.json) | v1 真实回放 120/120 通过，状态为 `RELEASE_CANDIDATE`；已用于激活 |
| [容量报告](./research/capacity-v1.json) | 预计占用约 41.5 MB，利用率 1.72%，通过容量门槛 |
| [延迟报告](./research/latency-v1.json) | Redis P95 15.363 ms、Evidence hydrated P95 18.679 ms，通过延迟门槛 |
| [人工证据报告](./research/human-v1.json) | 20 条 candidate 结果逐条复核，严重错误 0 |
| [v1 灰度确认](./research/gray-v1-confirmation.md) | 24 小时灰度观察与 release/功能开关回滚确认通过 |
| [Phase 8 case 审查](./research/phase8-case-audit.md) | 真实库可追溯 case 定义与 release/Embedding 阻断边界 |

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
