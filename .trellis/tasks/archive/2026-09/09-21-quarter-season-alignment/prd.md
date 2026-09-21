# 季度/档期映射跨层对齐

## Goal

修正 Python Agent 侧 season 标签→季度号/月份段映射，使其与权威侧（Business `SeasonUtil` 的动漫季约定 + indexer 存储的 MySQL `QUARTER()` 日历季度）一致，消除"查夏季实际命中春季"的错误结果。无需重建索引。

## Background

- 权威约定（动漫季 == 日历季度号）：`SeasonUtil.java:18-39` winter=1-3月、spring=4-6月、summer=7-9月、autumn=10-12月；indexer `jobs/indexer/repository.py:127` 用 `QUARTER(s.air_date)` 存储，即 1-3月=1 … 10-12月=4。因此正确映射应为 `winter=1, spring=2, summer=3, autumn=4`。
- 当前 Python 侧共 **5 处**错位映射（2026-09-21 逐一核实）：
  1. `app/rag/retrieval.py:17` `_QUARTERS={spring:1,summer:2,autumn:3,winter:4}`（用于 RediSearch 表达式 `:520`、Evidence 过滤 `:797`、`_item_quarter` 字符串分支 `:969-970`）。
  2. `app/adapters/redis/subject_index.py:239` Vector Set FILTER 内联同样的错位映射。
  3. `jobs/indexer/shadow_eval.py:153-158` `quarter_bounds` spring=(1,3)…winter=(10,12)，与权威约定整体错位一季。
  4. `jobs/importer/main.py:55-60` `SEASON_MONTHS` 同样的错位月份段；CLI `--mode season --key 2026-summer`（`main.py:6,699-701`）实际扫描 4-6 月而非 7-9 月，scheduler 的 quarterly_full 走 `--mode full` 不受影响。
  5. `app/rag/query_planner.py:27-32` 文本→标签的 `第一季度/一季度/Q1`→spring 等"第N季度/QN"标记继承了旧错位约定（Q1=日历1-3月=权威 winter）；spec `rag-retrieval-contract.md:29` 已点名 query_planner 需一并修复。
- `app/rag/retrieval.py:964-981` 的 `_item_quarter` 用 `((month-1)//3)+1`（日历季度）是**正确的**，与 indexer 存储一致；错的是标签→数字映射，导致 `_matches_query_filters`（`:795-798`）拿正确 item 季度去比错误标签号。
- wire 契约：Agent→Business `/season`、`/schedule` 传字符串标签（`subject_catalog.py:36,47`），Business DTO 用 `@Pattern(spring|summer|autumn|winter)`；Business 内部按动漫季取月份范围。数字季度只在 Agent 内部（Redis FILTER、Evidence 过滤、indexer 存储）使用。
- 下列既有测试**钉住了错误行为**，修复时必须同步更新：
  - `tests/jobs/indexer/test_shadow_eval.py:30-31`（autumn→(7,9)）与 `:40-43`（四季参数化月份段全错）。
  - `tests/rag/test_query_planner.py:18-23`（"Q4"→winter，权威应为 autumn）。
  - `tests/rag/test_evidence_contract.py:170-224`（airDate=2024-01-01 + quarter="spring" 期望通过；修复后 spring=4-6月，需把用例标签改为 winter 以保持原测试意图）。
- `tests/evals/generate_golden_cases.py:232` 生成 `filter_quarter_tag_*` 用例时把 quarter="autumn" 的证据参数写死为 `QUARTER()=3`（实际 7-9 月=夏季），需改为 4；已入库的 `golden_cases.json` 是 DEFINITION_ONLY 历史快照，本任务不重算（见 Notes）。

## Requirements

1. 定义**唯一**规范映射常量（`winter=1, spring=2, summer=3, autumn=4`），Python 侧所有标签→季度号/月份段处引用它，消除内联重复：`retrieval._QUARTERS`、`subject_index.py:239`、`shadow_eval.quarter_bounds`、`importer.SEASON_MONTHS`。
2. 修正 `app/rag/query_planner.py` 的"第N季度/几季度/QN"文本标记对齐权威约定（Q1/第一季度→winter、Q2→spring、Q3→summer、Q4→autumn），季节词（春番/春季等）保持不变；QN 标记从规范常量派生，不得再手写一份数字映射。
3. `_item_quarter` 的日历算法保持不变（已正确）。
4. 不重建索引、不改 MySQL 存储、不改 Business `SeasonUtil`（其为权威）、不改前端。
5. 修正 `generate_golden_cases.py:232` 的 autumn 证据参数为 4，使下次重放生成的数据集语义正确。
6. 加跨层回归测试：断言 Python 标签→季度号 == Business `SeasonUtil` 标签→月份→`QUARTER()` 对四季全部一致（源码级解析 Java 文件，无需 Java 运行时）；并断言 RediSearch 表达式、Redis Vector FILTER、Evidence 过滤、shadow eval SQL、importer season key、query_planner 文本解析对同一标签落到同一季度/月份段。

## Acceptance Criteria

- [ ] "夏季/summer" 检索命中的是 7-9 月番（quarter=3），不再是 4-6 月；四季均正确。
- [ ] Python 侧只有一处规范映射常量，`retrieval`/`subject_index`/`shadow_eval`/`importer`/`query_planner` 全部引用或对齐它（grep 不再存在第二份手写数字映射）。
- [ ] 跨层回归断言 Python 映射与 Java `SeasonUtil`+MySQL `QUARTER()` 四季一致，纳入 `uv run pytest`。
- [ ] RediSearch 表达式、Redis Vector FILTER、Evidence 结构化过滤、shadow eval SQL、importer `--mode season`、query_planner 六处对同一季度标签结果一致。
- [ ] 未改 Business/DB/前端；无需重建索引；既有 RAG/indexer/importer 测试在更新钉住错误行为的断言后全绿（`uv run pytest -q`）。

## Out of Scope

- 不改 Business `SeasonUtil`、DTO 或 MySQL 存储。
- 不引入新的季度语义（如按首播月自定义档期）。
- 不重算已入库的 `tests/evals/golden_cases.json` 历史快照（见 Notes）。
- 不做 T2（evidence/air-status 严格化）的任何改动。

## Notes

- 复杂任务（跨 retrieval/index/importer/影子评测 + 跨层语义）：`task.py start` 前补 `design.md`（规范常量放置位置、跨层回归如何断言 Java 侧）与 `implement.md`。
- 关键事实来源见 Background 中的 file:line；权威侧为 Java/MySQL 日历季度。
- `golden_cases.json` 当前为 `DEFINITION_ONLY` 快照且不被单测语义断言（`tests/evals/test_runner.py` 只校验结构）；其中 7 条 `filter_quarter_tag_*` 用例的证据参数仍是旧的 quarter=3。下一次对真实库做 live shadow eval 前需重新生成数据集（生成器已在本任务修正），该重放属于运维动作，不在本任务提交内。
