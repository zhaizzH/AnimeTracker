# Agent 实体名称解析接线（子 B）

> 子任务，父任务 `09-21-entity-name-resolution-wiring`。**前置**：子 A（`09-29-business-entity-name-resolve`）契约冻结。

## Goal

把 `main.py` 两处 `entity_name_lookup = None` 替换为真实的 Business typed resolver 适配器，使按人物/角色/声优名称的检索在线可用。

## Background（父任务调研已核实）

- **Agent 侧链路已完整实现且有单测**：`retrieval.py:375-421` `_lookup_entity_name`（校验名称长度/kind/ID 合法性）、`:317-318` 并入 `by_kind`、`:347-372` 名称命中复用同一 `resolve_lookup` 做关系扩展，fail-closed 语义齐备。测试见 `tests/rag/test_entity_filters.py:114-131,185-198`。
- **缺的只是组合根注入**：`main.py:132`（rag_enabled 分支，注释「Name resolution is authoritative Business work. The old Redis text-index adapter is intentionally not wired.」）、`main.py:143`（else 分支）均为 `None`（行号以复核时为准）。
- **消费链**：`retrieval.py:110-113` → `:114-118` 有 `entity_name_error` 即在访问 index **之前**返回 `available=False, items=[], reason=entity_name_error`；`:119-123` 有名无匹配 → `available=True, reason="no_results"`。
- **`RedisEntityNameLookup` 是死代码**：`app/adapters/redis/entity_name_lookup.py:23-51`；`:35-36` 无 `resolver` 即抛 `RuntimeError("实体名称解析必须使用 Business typed resolver；Vector Set 不提供全文名称查询")`。全仓生产构造点**零**（grep 只命中测试）。类名带 `redis` 但已无 Redis 调用（`:24` 注释「Compatibility name for the old adapter」）。
- **类型别名仍是 Callable**：`retrieval.py:70` `EntityNameLookup = Callable[..., Any]`，非 Protocol。
- **既有测试测的是死代码契约**：`tests/adapters/test_entity_name_lookup.py:10-30` 三条用例全程用手写 lambda 充当 resolver，不接触生产组合根、不断言 `main.py` 是否注入。
- **失实 docstring**：`rag_tools.py:38` 称「实体名称会先解析为本地 ID」——接线前为假。
- **spec 警告**：`agent-guidelines.md:110` 已明文警告「当前线上装配没有名称适配器，不能把这些单测路径视为已接通」。

## Requirements

- **R1 组合根注入**：`main.py` 两处 `entity_name_lookup = None` 替换为真实 Business 名称解析适配器（或明确保留 `None` 并记录决策——但保留则本任务目标未达成）。
- **R2 适配器契约**：必须走 Business typed resolver（子 A 的端点），**不得从 Vector Set 读名称**（spec `agent-guidelines.md:101`）。适配器须把 Business 响应映射为 `EntityNameMatch(entity_kind, entity_id)` 列表，并保持既有校验（名称长度、kind、ID ≥ 1）。
- **R3 `RedisEntityNameLookup` 去留**：类名误导（不含 Redis 调用）。决定：重命名去掉 `redis` 前缀并迁出 `app/adapters/redis/`，或保留为兼容名并记录理由。同步更新 `app/adapters/redis/__init__.py` 导出与 `tests/adapters/test_entity_name_lookup.py`。
- **R4 修正失实 docstring**：`rag_tools.py:38`。
- **R5 接线后测试**：新增**经真实组合根路径**的测试——区别于既有注入 lambda 的单测（后者不能证明在线可用）。至少断言：注入的适配器被 `RagRetrievalService` 持有；名称检索端到端走到 Business resolver（用替身）。
- **R6 spec 同步**：更新 `rag-retrieval-contract.md:18` 缺口行与 `agent-guidelines.md:109-110`（「不能视为已接通」警告消除或改写）。

## Acceptance Criteria

- [ ] **AC1** `main.py` 两分支均注入真实适配器；无 `entity_name_lookup = None` 残留（除非有显式记录的理由）。
- [ ] **AC2** 端到端（契约级等价替身 Business 端点）：`entity_name` + `entity_kind` 检索返回 Subject 候选，且经 `/resolve` 关系扩展生效。
- [ ] **AC3** fail-closed 全链保持：解析失败 → `available=False` + `entity_resolution_unavailable` 且**不访问 Subject 索引**；无匹配 → `available=True` + `no_results` 且不扩大范围（对齐 `agent-guidelines.md:117-121`）。
- [ ] **AC4** `RedisEntityNameLookup` 命名/位置决策已执行并记录；`__init__.py` 与既有适配器测试同步。
- [ ] **AC5** `rag_tools.py:38` docstring 与接线后行为一致。
- [ ] **AC6** `rag-retrieval-contract.md:18` 与 `agent-guidelines.md:109-110` 缺口已更新为已实现。
- [ ] **AC7** `uv run pytest` 全绿（记录实际数字）。
- [ ] **AC8** 无 Vector Set 名称查询路径（grep 确认）。

## Out of Scope

- Business 侧端点实现（子 A，本任务前置）。
- 重写检索/重排算法。
- 修改 `entity_kind` 四值或 48 字符上限（spec 已定）。
- 名称解析缓存层（另开任务）。

## Notes

- **前置阻塞**：子 A 的契约（路径、请求/响应字段、授权）必须先冻结；本任务 `implement.md` 须写明该前置。
- 父任务调研全文：`.trellis/tasks/09-21-entity-name-resolution-wiring/research/entity-name-resolution-facts.md`。
- 历史：`.trellis/tasks/archive/2026-09/09-03-bangumi-rag-retrieval/history/phase7-entity-name-report.md` 记载 2026-09-04 曾以 RediSearch 实现，后因 Redis 无 RediSearch 能力搁置。
- 复杂任务：需 `design.md`（适配器形状、命名决策、测试策略）+ `implement.md`，再 `task.py start`。
