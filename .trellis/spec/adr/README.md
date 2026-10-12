# 架构决策记录（ADR）

本目录收录满足**全部三条**的决策：难以反转、无上下文会令人困惑、是真实权衡的结果。领域词汇见 [`../GLOSSARY.md`](../GLOSSARY.md)。

| 编号 | 决策 |
|---|---|
| [0001](./0001-agent-write-two-phase-preview-confirm.md) | Agent 写操作采用「预览 → 确认 → 执行」两阶段协议 |
| [0002](./0002-single-active-index-pointer-in-mysql.md) | 索引激活指针以 MySQL `search_index_release` 为唯一权威，刻意移除 Redis 别名 |
| [0003](./0003-separate-public-and-private-minio-buckets.md) | MinIO 公开封面桶与私有原始快照桶必须是两个不同的桶，且启动期强校验 |
| [0004](./0004-no-versioned-migrations-destructive-full-ddl.md) | 不做版本化迁移：一份破坏式全量 DDL 作为唯一结构事实来源 |
| [0005](./0005-java-business-as-sole-agent-proxy-and-auth-boundary.md) | Java business 是 Python Agent 之前唯一的代理与认证边界 |
| [0006](./0006-fail-closed-index-release-gate.md) | 索引发布门禁 fail-closed，且把评估报告当作不可信输入 |
| [0007](./0007-lexical-in-mysql-semantic-in-redis.md) | 词法召回走 MySQL ngram 全文索引，语义召回走 Redis Vector Set |
| [0008](./0008-java-and-python-share-jwt-secret.md) | Java 与 Python 共享 `JWT_SECRET`，各自本地验签 |
| [0009](./0009-unified-job-table.md) | 统一 `job` 表承载三类任务，而非每条队列一张表 |
| [0010](./0010-subject-person-credit-single-table-dedup-key.md) | 主创关系单表 + 生成列 `dedup_key`，允许未解析占位行 |
| [0011](./0011-evidence-fail-closed-authority-boundary.md) | Evidence 是最终权威边界，部分失败也整批 fail-closed |
| [0012](./0012-public-health-endpoint-always-returns-200.md) | 公共健康检查始终返回 HTTP 200，降级在响应体表达 |
| [0013](./0013-single-instance-import-via-redis-lock.md) | 导入单实例由 Redis 锁 + 本地 PID 文件协调，代价是不可水平扩展 |
| [0014](./0014-agent-config-forbid-and-passthrough-env-keys.md) | Agent 配置 `extra="forbid"`，却把 jobs 专用 env 键声明为 `str` 直通 |
| [0015](./0015-air-status-conservative-single-implementation.md) | 播出状态推断收敛为单一保守实现，绝不从日期直接判「已完结」 |
| [0016](./0016-structural-relations-excluded-under-textual-intent.md) | 有文本意图时排除结构性关系展开，实体关系按权威白名单有界展开 |
| [0017](./0017-frontend-stack-react-over-vue-sunk-cost.md) | 前端技术栈中途从 Vue 3 迁移到 React，接受已写代码作废 |
| [0018](./0018-admin-on-separate-port-not-subpath.md) | 管理端用独立端口部署，前端 `baseURL` 固定 `/api` |
| [0019](./0019-email-via-resend-with-lockout-and-ratelimit.md) | 邮箱验证走 Resend，并同时配登录锁定与限流 |
| [0020](./0020-raw-subject-snapshots-not-redistributed.md) | 数据来源限 Bangumi v0 官方 API，原始快照留存但不分发 |

## 关于取舍

以上 20 条中，少数（0004、0013、0017、0019）的「难以反转」程度或「意外性」弱于其余，收录时已注明其历史性或操作性；若将来判定它们够不上三条准入，可移回对应层规范。
