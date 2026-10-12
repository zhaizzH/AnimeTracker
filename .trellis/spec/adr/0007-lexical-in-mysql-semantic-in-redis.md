# 0007 — 词法召回走 MySQL ngram 全文索引，语义召回走 Redis Vector Set

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：[backend/database-guidelines.md](../backend/database-guidelines.md#scenario-rag-词法投影与发布指针)、`app/adapters/redis/vector_set.py`

## 背景

检索需要两路召回：**词法**（精确关键词、别名、中文分词）与**语义**（向量近邻）。可选的技术栈有多种，从「全部放进一个向量数据库」到「每路各用最合适的存储」。

## 决策

两条召回**分属不同存储，各用其长**：

- **词法**：MySQL 8.4 的 `ngram` FULLTEXT 索引（`search_document` 表），由 business 侧承载。
- **语义**：Redis 8 的 **Vector Set**（`VADD`/`VSIM`/`VREM`），按 key 做版本隔离。

并**刻意排除**两类依赖：Redis 侧不用 RediSearch / Redis Stack，MySQL 侧不再实现第二套词法。词法投影刻意「不实现词法检索」以外的东西，`vector_set.py` 明确「刻意不含任何 RediSearch 命令」。两路结果在 Python 侧用 RRF 融合。

## 备选方案

1. **RediSearch 单栈承载词法 + 语义。** 未采纳——引入 Redis Stack 这一重量级依赖，并放弃 MySQL ngram 对中文分词的现成支持；也把检索耦合到单一组件。
2. **MySQL ngram（词法）+ Redis 8 Vector Set（语义）（采纳）。** 复用已有的两种存储能力，避免引入 RediSearch。

## 后果

**正面**

- 各存储只做它原生擅长的事；中文分词的成熟方案（ngram）直接可用。
- 不引入 Redis Stack；Redis 侧只需 Redis 8 原生 Vector Set 能力。
- 词法投影可随 `index_version` 在 MySQL 内整体重建。

**代价**

- 检索的正确性横跨 MySQL 与 Redis：**发布/回滚要求两者同时在场且同一版本**，任一缺失都不算发布成功。
- 融合逻辑（RRF）由应用层承担，无法交给单一数据库。

**约束**

- 不得引入 RediSearch / Redis Stack 命令；不得在 MySQL 侧再塞一套向量检索，或在 Redis 侧再塞一套词法检索。
