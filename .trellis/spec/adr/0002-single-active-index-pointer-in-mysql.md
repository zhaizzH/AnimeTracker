# 0002 — 索引激活指针以 MySQL `search_index_release` 为唯一权威，刻意移除 Redis 别名

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：[backend/rag-retrieval-contract.md](../backend/rag-retrieval-contract.md)、[backend/database-guidelines.md](../backend/database-guidelines.md#scenario-rag-词法投影与发布指针)

## 背景

检索由两套投影共同支撑：MySQL 的 ngram 全文索引承担词法召回，Redis 8 的 Vector Set 承担语义召回。两套投影都必须能**按版本重建、按版本切换、按版本回滚**，因此系统需要一个「当前哪个版本是活的」的活动指针。

指针放在哪里，决定了发布与回滚的原子性边界。历史上项目用过 Redis 别名来实现切换。

## 决策

活动指针以 MySQL `search_index_release` 为**唯一权威**：`status='ACTIVE'` 派生的生成列加唯一索引，保证至多一个活动版本。

同时**刻意移除 Redis 别名机制**：配置键 `RAG_INDEX_ALIAS` 已删除，`gate.py` 甚至保留了一个守卫——一旦检测到别名配置就 fail-closed 报错，明确「本门禁刻意不支持 Redis 别名」。文档中「Redis alias 不是发布或回滚事实」是硬约束。

## 备选方案

1. **用 Redis 别名做原子切换。** 未采纳——这是多数向量栈（含 RediSearch/Redis Stack）的惯用做法，也确实更省事，但它把活动指针放进了一个**不是结构事实来源**的存储：发布事实会分散在两处（开关在 Redis、版本记录在 MySQL），回滚时难以原子对齐；Redis 被清空或重建会直接丢失发布状态。而且本项目**刻意不用 RediSearch**（词法召回走 MySQL ngram），引入别名只会带来与其余架构不一致的孤例。
2. **MySQL 单指针（采纳）。** 发布的真值就是一行可 SQL 查询、可审计、可事务切换的记录。

## 后果

**正面**

- 发布与回滚只有一处事实来源，可用一条 SQL 复核当前活动版本。
- 切换可放进事务，与投影写入的一致性边界清晰。
- 不依赖 Redis 是否保有某个键，Redis 独立于发布状态。

**代价**

- 切换释放指针是一次 MySQL 事务写入，而非 Redis 的 O(1) 重命名；发布的关键路径要求 MySQL 可达。
- 发布窗口要求 MySQL 与 Redis **同时**在场（词法在 MySQL、语义在 Redis），任一缺失都不能算发布成功。

**约束**

- 不得恢复 `RAG_INDEX_ALIAS` 或任何以 Redis 键充当活动指针的机制；`gate.py` 会在配置层直接拒绝。
- 无活动 release 时 Business lexical API 返回 503，**不得**伪造候选或静默降级。
