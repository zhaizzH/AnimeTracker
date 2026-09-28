# 实体名称解析接线（跨层）

> **父任务**。本任务承载跨层目标与集成验收，不做单体实现；实现落在两个子任务（见「子任务拆分」）。

## Goal

按 spec 目标数据流「名称 → 本地实体 ID → Business `/resolve` 关系扩展」打通按人物/角色/声优名称的检索。当前 `entity_name_lookup=None`，任何带名称的检索立即返回 `entity_resolution_unavailable`。

## Background（本会话已核实）

### 缺口判定（本任务的关键结论）

> **跨层缺口是「Business 完全没有按名称解析实体的能力」，不是「已有能力但 Agent 未接线」。**

- **Business 侧无任何名称解析能力**：`backend/business/client/.../controller/` 8 个控制器中，`SubjectController` 的 `/search` 走 `SubjectSearchQueryDTO`，SQL 只对 `s.name`/`s.name_cn` 做 `LIKE`（`SubjectMapper.xml:14-15`）——按**作品名**，不按人物/角色/声优名。`client/service/` 无 EntityResolver/PersonService/CharacterService。16 个 mapper 中 `EvidenceMapper.java:72-93` 的四个扩展方法全部以**本地 ID** 为参数；全仓 grep 确认**没有任何 SQL 以 name 为条件查询 person/character/alias**。`docs/spec/openapi.yaml` 亦无相应路径。
- **数据层已就绪**：`docs/database/db-schema.sql` 已有 `person.name`（`:357`，索引 `idx_person_name` `:373`）、`character.name`（`:387`，索引 `:402`）、`person_alias.name`（`:415`，索引 `:423`）、`character_alias.name`（`:434`，索引 `:442`）。**缺的只是 API，无需新增列或 migration。**
- **Agent 侧链路已完整实现且有单测**：`retrieval.py:375-421` `_lookup_entity_name`（校验名称长度/kind/ID 合法性）、`:317-318` 并入 `by_kind`、`:347-372` 名称命中复用同一 `resolve_lookup` 做关系扩展、fail-closed 语义齐备。测试见 `tests/rag/test_entity_filters.py:114-131,185-198`。**缺的只是组合根注入真实适配器**（`main.py:132,141` 两处 `None`）。

### 现状证据

| 项 | 证据 |
|---|---|
| 类型别名（非 Protocol 端口） | `retrieval.py:70` `EntityNameLookup = Callable[..., Any]`；`:85,:94,:107` 注入与逐调用覆盖 |
| 组合根两分支均注入 `None` | `main.py:132`（rag_enabled 分支，注释「Name resolution is authoritative Business work. The old Redis text-index adapter is intentionally not wired.」）、`main.py:141`（else 分支） |
| 消费链 | `retrieval.py:110-113` → `:114-118` 有 `entity_name_error` 即在访问 index **之前**返回 `available=False, items=[], reason=entity_name_error`；`:119-123` 有名无匹配 → `available=True, reason="no_results"` |
| `RedisEntityNameLookup` 是死代码 | `app/adapters/redis/entity_name_lookup.py:23-51`；`:35-36` 无 `resolver` 即抛 `RuntimeError("实体名称解析必须使用 Business typed resolver；Vector Set 不提供全文名称查询")`。全仓生产构造点**零**（`grep "RedisEntityNameLookup(" backend` 只命中测试）。类名带 `redis` 但已无 Redis 调用（`:24` 注释「Compatibility name for the old adapter」） |
| 既有测试测的是死代码契约 | `tests/adapters/test_entity_name_lookup.py:10-30` 三条用例全程用手写 lambda 充当 resolver，不接触生产组合根、不断言 `main.py` 是否注入 |
| 解析故障 vs 无命中刻意区分 | `agent-guidelines.md:117-121`：故障 → `available=false` + `entity_resolution_unavailable`，**不得访问 Subject 索引**；无匹配 → `available=true` + `no_results`，不得扩大范围 |
| Business `/resolve` 已接线 | Controller `EvidenceController.java:46-50`；Service `EvidenceServiceImpl.java:74-102`（`:79-81` `>50` 抛 `BizException(BAD_REQUEST)`，`:91-97` switch 五种 entityType）；安全边界 `EvidenceMapper.xml:122-171` 硬编码 `spc.source_active=1 AND p.source_active=1 AND s.type=2 AND s.nsfw=0 AND s.import_status=1`。Agent 侧 `business_http.py:128-141` → `main.py:150` 已接线 |
| 工具与 Prompt 已就绪、运行期不可用 | `rag_tools.py:34-35,48-49/70-71/89-90/111-112/130-131` 三条工具均暴露 `entity_name` + `entity_kind`；`:38` docstring 称「实体名称会先解析为本地 ID」——**与生产行为不符**。spec `agent-guidelines.md:110` 已明文警告「当前线上装配没有名称适配器，不能把这些单测路径视为已接通」 |
| spec 目标数据流 | `agent-guidelines.md:109`（目标边界 + 不得把注释方案描述为已实现）、`:152-157`（Correct 示例 `matches = entity_name_lookup(...)` → `allowed = resolve_evidence(match.entity_kind, ids, token=token)`）；`rag-retrieval-contract.md:18` 缺口行 |
| `/resolve` 鉴权差异 | `SecurityConfig.java:71` 把 `POST /api/client/evidence/resolve` 设为 `permitAll()`（与其它 client 端点不同）——新增名称解析端点时需明确其授权是否与之一致 |

### 目标契约（spec 已定部分）

- `entity_name` 最多 48 可见字符；`entity_kind ∈ {PERSON, CHARACTER, ACTOR, RELATION_SUBJECT}`；不可脱离 `entity_name` 单独使用（`agent-guidelines.md:98`）。
- 名称解析失败必须 **fail-closed**（`agent-guidelines.md:101`）。
- 实体 ID 不得拼接进 Vector Set `FILTER` 或 SQL 字符串（`agent-guidelines.md:108`）。
- `RELATION_SUBJECT` 沿 `subject_relation` 双向扩展（`agent-guidelines.md:99`）。
- spec **未命名**提供解析能力的 Business 端点路径——新端点契约需在本任务内定义。

## 子任务拆分（本会话确认）

父任务承载跨层目标、任务映射与集成验收；两个子任务各自可独立规划、实现、检查、归档。**依赖关系写入子任务 artifact，不靠树形位置隐含。**

| 子任务 | 内容 | 验收 | 依赖 |
|---|---|---|---|
| **子 A：Business 名称解析端点** | 新增按名称解析实体的 API：DTO / service / mapper / SQL（复用 `db-schema.sql` 既有 name 列与索引）/ OpenAPI 契约 / 授权决策与测试。限定 `entity_kind` 四值、`limit` 上限、返回本地实体 ID | `mvn -B test`（`backend/business`） | 无（前置） |
| **子 B：Agent 接线** | 组合根注入真实 Business 名称解析适配器（替换 `main.py:132,141` 的 `None`）；适配器走 Business typed resolver；`RedisEntityNameLookup` 去留与命名处理；补接线后的端到端测试 | `uv run pytest`（`backend/agent`） | **依赖子 A 的契约冻结**（路径、请求/响应字段、授权） |

创建命令（子任务）：
```bash
python ./.trellis/scripts/task.py create "<title>" --slug <name> --parent 09-21-entity-name-resolution-wiring
```

顺序约束：子 A 的契约必须先冻结（至少路径与字段结构），子 B 才能开始；子 B 的 `implement.md` 须写明该前置。

## Requirements

### R1 跨层目标（父任务）

名称检索必须端到端可用：模型给出 `entity_name` + `entity_kind` → 解析为本地实体 ID → 经 Business `/resolve` 做关系扩展 → 返回 Subject 候选。任何环节不可用时 fail-closed，不得伪造结果。

### R2 契约定义与冻结

- 子 A 必须产出并冻结新端点的契约（路径、请求字段、响应结构、错误语义、授权），并同步 `docs/spec/openapi.yaml`。
- 契约须满足既有安全边界：只返回 `type=2`、`nsfw=0`、`active`（`source_active=1`）的实体，与 `EvidenceMapper.xml:122-171` 的 `/resolve` 边界一致。
- 授权须显式决定并测试；须说明与 `/resolve` 当前 `permitAll()`（`SecurityConfig.java:71`）是否一致及理由。

### R3 Agent 接线

- `main.py` 两处 `entity_name_lookup = None` 替换为真实适配器（或明确保留 `None` 并记录决策——但保留则本任务目标未达成）。
- 适配器必须使用 Business typed resolver，不得从 Vector Set 读名称（spec `agent-guidelines.md:101`）。
- 修正 `rag_tools.py:38` 的失实 docstring（现称「会先解析为本地 ID」，接线前为假）。

### R4 测试与文档

- Agent 侧补**接线后**的测试（注入真实适配器路径），区别于既有注入式单测——后者不能证明在线可用（`agent-guidelines.md:110`）。
- 修正 spec 缺口行：`rag-retrieval-contract.md:18`、`agent-guidelines.md:109-110`。

## Acceptance Criteria（父任务集成验收）

- [ ] **AC1** 子 A 与子 B 均已完成并归档；各自验收标准已满足。
- [ ] **AC2** 端到端：以真实（或契约级等价替身）Business 端点，`entity_name` + `entity_kind` 检索返回 Subject 候选，且经 `/resolve` 关系扩展生效。
- [ ] **AC3** fail-closed 全链保持：解析失败 → `available=False` + `entity_resolution_unavailable` 且**不访问 Subject 索引**；无匹配 → `available=True` + `no_results` 且不扩大范围（对齐 `agent-guidelines.md:117-121`）。
- [ ] **AC4** `rag-retrieval-contract.md:18` 与 `agent-guidelines.md:109-110` 的缺口描述已更新为已实现；`agent-guidelines.md:110` 的「不能视为已接通」警告已消除或改写。
- [ ] **AC5** `mvn -B test`（`backend/business`）与 `uv run pytest`（`backend/agent`）均全绿。
- [ ] **AC6** 新增端点已在 `docs/spec/openapi.yaml` 中建模，且与实现字段一致。

## Out of Scope

- 重写检索/重排算法。
- 改 Business `/resolve` 的既有安全边界（`EvidenceMapper.xml:122-171`）或五种 entityType 语义。
- 新增数据库列或 migration（`db-schema.sql` 的 name 列与索引已就绪）。
- 修改 `entity_kind` 的四值枚举或 48 字符上限（spec 已定）。
- 名称解析的缓存层（本次调研未见既有实现；如需缓存应另开任务）。

## Notes

- 调研报告：`.trellis/tasks/09-21-entity-name-resolution-wiring/research/entity-name-resolution-facts.md`（含全部 file:line 证据）。
- 历史背景：`.trellis/tasks/archive/2026-09/09-03-bangumi-rag-retrieval/history/phase7-entity-name-report.md` 记载 2026-09-04 曾以 RediSearch 实现名称解析，后因 Redis 无 RediSearch 能力而搁置；`.trellis/workspace/zhaizzH/journal-1.md:188`「F08 实体名称解析等待 Business 权威接口」——与本任务缺口判定一致。
- 本任务体量跨 Java + Python 两技术栈，故拆父子；父任务不设 `design.md`/`implement.md`（无直接实现），由子任务各自具备。
