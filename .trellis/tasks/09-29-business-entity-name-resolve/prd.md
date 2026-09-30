# Business 名称解析端点（子 A）

> 子任务，父任务 `09-21-entity-name-resolution-wiring`。跨层缺口的**前置**：Business 当前完全没有按名称解析实体的能力。

## Goal

新增 Business API：按 `entity_name` + `entity_kind` 解析为本地实体 ID，供 Agent 侧名称检索链路使用。

## Background（父任务调研已核实）

- **Business 侧无任何名称解析能力**：`SubjectController` 的 `/search` 走 `SubjectSearchQueryDTO`，SQL 只对 `s.name`/`s.name_cn` 做 `LIKE`（`SubjectMapper.xml:14-15`）——按**作品名**，不按人物/角色/声优名。`client/service/` 无 EntityResolver/PersonService/CharacterService。16 个 mapper 中 `EvidenceMapper.java:72-93` 的四个扩展方法全部以**本地 ID** 为参数；全仓 grep 确认**无任何 SQL 以 name 为条件查询 person/character/alias**。
- **数据层已就绪**（无需 migration）：`docs/database/db-schema.sql` 已有
  - `person.name`（`:357`，索引 `idx_person_name` `:373`）
  - `character.name`（`:387`，索引 `:402`）
  - `person_alias.name`（`:415`，索引 `:423`）
  - `character_alias.name`（`:434`，索引 `:442`）
- **安全边界参照**：`EvidenceMapper.xml:122-171` 的 `/resolve` 硬编码 `spc.source_active=1 AND p.source_active=1 AND s.type=2 AND s.nsfw=0 AND s.import_status=1`。
- **授权现状**：`SecurityConfig.java:71` 把 `POST /api/client/evidence/resolve` 设为 `permitAll()`（与其它 client 端点不同）。
- **目标契约（spec 已定）**：`entity_name` 最多 48 可见字符；`entity_kind ∈ {PERSON, CHARACTER, ACTOR, RELATION_SUBJECT}`；解析失败必须 fail-closed（`agent-guidelines.md:98,101`）；实体 ID 不得拼接进 SQL 字符串（`agent-guidelines.md:108`）。
- spec **未命名**该端点路径——须在本任务内定义并冻结。

## Requirements

- **R1 端点契约**（须冻结后子 B 才能开始）：定义路径、请求字段、响应结构、错误语义、授权。建议形状：
  - `POST /api/client/entities/resolve-by-name`（路径待定，需与既有 `AgentApiPaths`/client 命名一致）
  - 请求：`{entityName: str(1..48), entityKind: enum(四值), limit: int(1..50)}`
  - 响应：本地实体 ID 列表，每项含 `entityKind` + `entityId`
- **R2 数据访问**：新 mapper 方法按 name 查 `person`/`character`（含 `*_alias` 表）；使用参数绑定，**禁止字符串拼接**；复用既有 name 索引。
- **R3 授权**：显式决定并测试；须说明与 `/resolve` 当前 `permitAll()`（`SecurityConfig.java:71`）是否一致及理由。
- **R4 安全边界**：返回结果须满足与 `/resolve` 一致的可见性（`source_active`/`nsfw`/`type`/`import_status`），或明确记录差异及理由。
- **R5 OpenAPI**：`docs/spec/openapi.yaml` 建模新端点，字段与实现一致。
- **R6 测试**：`mvn -B test`（`backend/business`）覆盖正常解析、四值 `entity_kind`、`limit` 上限、无匹配、授权、边界（超长名称/非法 kind）。

## Acceptance Criteria

- [ ] **AC1** 新端点契约已冻结并写入本任务 `design.md`（路径、字段、错误语义、授权决策）。
- [ ] **AC2** `mvn -B test`（`backend/business`）全绿。
- [ ] **AC3** 覆盖上列 R6 六类用例；至少「正常」与「无匹配/非法入参」各有显式断言。
- [ ] **AC4** 授权行为已测试并有明确决策记录（与 `/resolve` 的 `permitAll()` 是否一致 + 理由）。
- [ ] **AC5** SQL 全部参数绑定，无字符串拼接；安全边界与 `/resolve` 一致或差异已登记。
- [ ] **AC6** `docs/spec/openapi.yaml` 已建模该端点且与实现字段一致。
- [ ] **AC7** `entity_name` 48 字符上限与四值 `entity_kind` 在实现层强制（非仅文档）。

## Out of Scope

- Agent 侧接线（子 B）。
- 新增数据库列或 migration（name 列与索引已就绪）。
- 修改 `entity_kind` 四值枚举或 48 字符上限。
- 修改 Business `/resolve` 的既有安全边界或五种 entityType 语义。
- 名称解析缓存层（另开任务）。

## Notes

- **契约冻结是子 B 的前置阻塞点**（父任务已声明顺序约束）。
- 父任务调研全文：`.trellis/tasks/09-21-entity-name-resolution-wiring/research/entity-name-resolution-facts.md`。
- 复杂任务：需 `design.md`（契约、SQL 形状、授权决策）+ `implement.md`，再 `task.py start`。
