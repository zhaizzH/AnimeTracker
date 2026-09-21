# 季度/档期映射跨层对齐

## Goal

修正 Python Agent 侧 season 标签→季度号映射，使其与权威侧（Business `SeasonUtil` 的动漫季约定 + indexer 存储的 MySQL `QUARTER()` 日历季度）一致，消除"查夏季实际命中春季"的错误结果。无需重建索引。

## Background

- 权威约定（动漫季 == 日历季度号）：`SeasonUtil.java:18-39` winter=1-3月、spring=4-6月、summer=7-9月、autumn=10-12月；indexer `jobs/indexer/repository.py:127` 用 `QUARTER(s.air_date)` 存储，即 1-3月=1 … 10-12月=4。因此正确映射应为 `winter=1, spring=2, summer=3, autumn=4`。
- 当前 Python 侧错位：`app/rag/retrieval.py:17` `_QUARTERS={spring:1,summer:2,autumn:3,winter:4}`；`app/adapters/redis/subject_index.py:239` 内联同样的错位映射；`jobs/indexer/shadow_eval.py:153-158` 用 `spring:(1,3),summer:(4,6),autumn:(7,9),winter:(10,12)`（spring=Jan-Mar，与权威 winter=Jan-Mar 冲突）。
- `app/rag/retrieval.py:964-981` 的 `_item_quarter` 用 `((month-1)//3)+1`（日历季度）是**正确的**，与 indexer 存储一致；错的是标签→数字映射，导致 `_matches_query_filters`（`:795-798`）拿正确 item 季度去比错误标签号。
- wire 契约：Agent→Business `/season`、`/schedule` 传字符串标签（`subject_catalog.py:36,47`），Business DTO 用 `@Pattern(spring|summer|autumn|winter)`；Business 内部按动漫季取月份范围。数字季度只在 Agent 内部（Redis FILTER、Evidence 过滤、indexer 存储）使用。

## Requirements

1. 定义**唯一**规范映射常量（`winter=1, spring=2, summer=3, autumn=4`），Python 侧所有标签→季度号处引用它，消除内联重复：`retrieval._QUARTERS`、`subject_index.py:239`。
2. 修正 `jobs/indexer/shadow_eval.py` 的季度月份段为权威约定（winter=1-3、spring=4-6、summer=7-9、autumn=10-12）。
3. `_item_quarter` 的日历算法保持不变（已正确）。
4. 不重建索引、不改 MySQL 存储、不改 Business `SeasonUtil`（其为权威）。
5. 加跨层回归测试：断言 Python 标签→季度号 == Business `SeasonUtil` 标签→月份→`QUARTER()` 对四季全部一致；并断言 Redis FILTER 与 Evidence 过滤对同一标签选到同一季度。

## Acceptance Criteria

- [ ] "夏季/summer" 检索命中的是 7-9 月番（quarter=3），不再是 4-6 月；四季均正确。
- [ ] Python 侧只有一处规范映射常量，`retrieval`/`subject_index`/`shadow_eval` 全部引用或对齐它。
- [ ] 跨层回归断言 Python 映射与 Java `SeasonUtil`+MySQL `QUARTER()` 四季一致，纳入 `uv run pytest`。
- [ ] Redis Vector FILTER、Evidence 结构化过滤、shadow eval 三处对同一季度标签结果一致。
- [ ] 未改 Business/DB/前端；无需重建索引；既有 RAG/indexer 测试不回归。

## Out of Scope

- 不改 Business `SeasonUtil`、DTO 或 MySQL 存储。
- 不引入新的季度语义（如按首播月自定义档期）。

## Notes

- 复杂任务（跨 retrieval/index/影子评测 + 跨层语义）：`task.py start` 前补 `design.md`（规范常量放置位置、跨层回归如何断言 Java 侧）与 `implement.md`。
- 关键事实来源见 Background 中的 file:line；权威侧为 Java/MySQL 日历季度。
