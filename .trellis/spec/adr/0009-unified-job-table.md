# 0009 — 统一 `job` 表承载三类任务，而非每条队列一张表

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：[backend/database-guidelines.md](../backend/database-guidelines.md)「Python 离线任务」

## 背景

离线侧有三类任务：实体详情补全（`ENTITY_DETAIL`，backfill 消费）、通用双投影索引（`SEARCH_INDEX`，indexer 消费）、旧 Subject 兼容索引（`RAG_INDEX`）。历史上它们是三张独立表。

## 决策

**合并为一张 `job` 表**，靠 `type` 区分；差异元数据（embedding 元组、`source_id`、`checkpoint`、`content_hash`）折叠进 `payload_json`，仅将幂等比对所需的 `content_hash` 提升为列。合并前旧 `entity_detail_job` / `search_index_job` / `rag_index_job` schema 约 90% 雷同（状态、重试次数、下次重试时间、错误信息），差异列均非查询条件。

## 备选方案

1. **维持三张独立队列表。** 未采纳——三份近乎重复的 schema 与三套 lease/重试/幂等实现。
2. **单表 + `payload_json` 承载差异（采纳）。** 复用一套租约、重试与幂等机制。

## 后果

**正面**

- 只有一套任务生命周期机制（认领、重试退避、终态），无三份漂移。
- 新增任务类型只是新增一个 `type` 取值，不需要新表。

**代价与陷阱（重要）**

- 单表意味着**作用域必须显式**：针对 `job` 的每条 SQL 都必须带 `type=` 或 `id=`。仅按 `status`/`next_retry_at` 过滤会跨队列误伤其他类型——这是本表最易犯的错误。
- 三类任务的 claim 谓词**故意不同**，不能互相「统一」：`RAG_INDEX` 与 `SEARCH_INDEX` 的可领分支**不含** `next_retry_at IS NULL`，而 `ENTITY_DETAIL` **必须保留** `IS NULL`（backfill 用 `NULL` 表示「解除暂停、立即可领」）。统一它们会造成「无退避重试到耗尽」或「暂停后永不恢复」。

**约束**

- 禁止再引入独立 job 队列表。新增终态优先用独立状态（`ABANDONED` / `TOMBSTONE`），不复用 `FAILED` + `NULL`。
