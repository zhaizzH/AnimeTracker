# Research: 实体名称解析接线（跨层）

- **Query**: 实体名称解析 entity_name_lookup 接线现状 + Business 侧名称解析能力缺口判定
- **Scope**: mixed（Agent 内部源码 + Business Java 源码 + OpenAPI/Schema + spec）
- **Date**: 2026-09-21

---

## 1. `entity_name_lookup` 的全部接线点与消费点

### 定义（类型）

| 位置 | 内容 |
|---|---|
| `backend/agent/app/rag/retrieval.py:70` | `EntityNameLookup = Callable[..., Any]` — 唯一类型别名，非 Protocol |
| `backend/agent/app/rag/retrieval.py:85` | `RagRetrievalService.__init__` 参数 `entity_name_lookup: EntityNameLookup \| None = None` |
| `backend/agent/app/rag/retrieval.py:94` | `self._entity_name_lookup = entity_name_lookup` |
| `backend/agent/app/rag/retrieval.py:107` | `retrieve()` 逐调用覆盖参数 `entity_name_lookup: EntityNameLookup \| None = None` |

注意：这不是 Protocol 端口，而是裸 `Callable[..., Any]`。无 `app/rag/ports.py` 中的端口定义（`app/rag/ports.py` 仅含 index/embedding 相关）。

### 构造（组合根）

| 位置 | 内容 |
|---|---|
| `backend/agent/main.py:127-138` | `if settings.rag_enabled:` 分支：构造 Redis、`RedisSubjectIndex`，然后 **`entity_name_lookup = None`（:132）**，注释「Name resolution is authoritative Business work. The old Redis text-index adapter is intentionally not wired.」 |
| `backend/agent/main.py:139-143` | `else:` 分支：**`entity_name_lookup = None`（:141）** |
| `backend/agent/main.py:144-153` | 传入 `RagRetrievalService(..., entity_name_lookup=entity_name_lookup, ...)`（:151） |

两分支都为 `None` ⇒ **在线组合根从不注入名称解析器**。

### 消费

| 位置 | 行为 |
|---|---|
| `retrieval.py:110-113` | `retrieve()` 首先调用 `_lookup_entity_name(query, lookup=entity_name_lookup or self._entity_name_lookup)` |
| `retrieval.py:114-118` | 有 `entity_name_error` 即 `return self._complete(RetrievalResult(available=False, items=[], reason=entity_name_error), ...)` — 在访问 index 之前返回 |
| `retrieval.py:119-123` | `query.entity_name and not entity_name_matches` ⇒ `available=True, reason="no_results"` |
| `retrieval.py:124-129` | 其余情况把 `name_matches` 交给 `_resolve_entity_subject_ids(...)` |
| `retrieval.py:317-318` | `_resolve_entity_subject_ids` 把 `name_matches` 按 kind 合并进 `by_kind` |
| `retrieval.py:347-372` | 名称命中的 ID 复用**同一个 `resolve_lookup`**（即 Business `/resolve`）做关系扩展；`by_kind` 各 kind 之间取并集，最后与显式 ID 字段取交集 |

### `_lookup_entity_name`（解析器消费细节）

`backend/agent/app/rag/retrieval.py:375-421`：

- `:382-383` 无 `entity_name` ⇒ `return [], None`
- `:384-385` `lookup is None` ⇒ `return [], "entity_resolution_unavailable"` ← **当前生产必走此分支**
- `:386-393` lookup 抛异常 ⇒ `entity_resolution_unavailable`
- `:394-397` 响应非 Mapping/list/tuple ⇒ `entity_resolution_unavailable`
- `:400` `allowed_kinds = {query.entity_kind}` 或全四种
- `:409-410` kind 不在 allowed_kinds 或 `raw_id` 是 bool ⇒ `entity_resolution_unavailable`
- `:411-416` id 非 int 或 `< 1` ⇒ `entity_resolution_unavailable`
- `:417-421` 去重后返回 `list[tuple[str, int]]`
- 接受 Mapping 形态与 dataclass/对象形态两种行（`:402-407`）

### `entity_resolution_unavailable` 产生处（共 12 处）

`retrieval.py:322`（无 resolve_lookup）、`:331,:333,:336`（显式 ID 的 /resolve 失败）、`:356,:358,:361`（名称命中的 /resolve 失败）、`:385`（**无名称解析器**）、`:393,:397,:410,:414,:416`（名称响应非法）。

---

## 2. `RedisEntityNameLookup`

- 文件：`backend/agent/app/adapters/redis/entity_name_lookup.py`（全场 51 行）
- 类：`:23-51`；dataclass `EntityNameMatch(entity_kind, entity_id)` `:17-20`
- 类型别名：`:14` `EntityNameKind = Literal["PERSON","CHARACTER","ACTOR","RELATION_SUBJECT"]`
- 方法签名：`:30`
  ```python
  def lookup(self, entity_name: str, *, entity_kind: EntityNameKind | None = None, limit: int = 50) -> list[EntityNameMatch]
  ```
- `:26` `__init__(self, redis_client=None, *, index_version="", resolver=None, **_kwargs)`
- `:31-34` 名称非空且 ≤48 字符、`limit ≥ 1` 校验
- **`:35-36` 无 `resolver` 即 `raise RuntimeError("实体名称解析必须使用 Business typed resolver；Vector Set 不提供全文名称查询")`**
- `:37` `response = self._resolver(entity_name.strip(), entity_kind=entity_kind, limit=min(limit, 50))`
- `:38-50` 校验响应必须是 list/tuple、行可映射、`entity_id ≥ 1`，否则 RuntimeError

导出：`app/adapters/redis/__init__.py:2,11,12`。

**为何是死代码**：全仓 `RedisEntityNameLookup` 引用点只有（1）自身定义、（2）`__init__.py` 再导出、（3）`tests/adapters/test_entity_name_lookup.py:7,17,24,28`、（4）spec 文本。**没有任何生产构造点**：`main.py` 两处均写 `None`，`grep -rn "RedisEntityNameLookup(" backend` 只命中测试。类名/文件位置带 `redis` 但当前实现已不含任何 Redis 调用（RediSearch 移除后的兼容壳，`:24` 注释 "Compatibility name for the old adapter"）。

---

## 3. 解析失败路径

**服务层返回**（`retrieval.py:115-118`）：

```python
RetrievalResult(available=False, items=[], reason=entity_name_error)
```

即 `available=False`、`items=[]`、`reason="entity_resolution_unavailable"`。`personalization_notice` 保留。

**模型可感知路径**：

| 位置 | 内容 |
|---|---|
| `app/rag/use_case.py:37-42` | 返回 `{"available", "reason", "personalizationNotice", "items"}` |
| `app/agent/client/rag_tools.py:140-148` | `_items()`：`available` 为假时返回 `{"available": False, "reason": <reason>, "items": []}` |
| `resources/prompt/client/recommend_agent_prompt.md:31` | 提示词要求「返回没有找到匹配项、名称解析不可用或校验失败时：如实告知用户，不生成预览、不写入」 |
| `.trellis/spec/backend/agent-guidelines.md:224` | 「RAG `available=false` 或异常 → 返回"名称解析不可用"；不伪装无结果；不预览；不建状态」 |

同文件另一处名称相关用户话术：`app/agent/client/actions/subject_resolution.py:312,314`（`"名称解析暂时不可用，请稍后再试或直接提供番剧ID"`）——属于写操作预览链路，非 RAG 链路。

**语义要点**：解析**故障**（unavailable）与解析**无命中**（`available=True, reason="no_results"`，`retrieval.py:119-123`）被刻意区分，且 spec 明文要求不得混淆（`agent-guidelines.md:117-121`）。

---

## 4. spec 目标：名称 → 本地实体 ID → 关系扩展

### 已明确的目标数据流

`.trellis/spec/backend/agent-guidelines.md:109`（原文要点）：

> 目标边界：名称应先解析为本地实体 ID，再通过 Business `/resolve` 做关系扩展。当前 `main.py` 在开关两种分支都注入 `entity_name_lookup=None`，`_lookup_entity_name` 遇到名称立即返回 `entity_resolution_unavailable`；只有显式实体 ID 的 `/resolve` 链已接线。不得把注释中的 Business 名称解析方案描述为已实现。旧 `RedisEntityNameLookup` 未接入在线组合根。

`.trellis/spec/backend/agent-guidelines.md:152-157`（Correct 示例）：

```python
matches = entity_name_lookup(query.entity_name, entity_kind=query.entity_kind, limit=50)
allowed = resolve_evidence(match.entity_kind, ids, token=token)
```

**结论：spec 已明确目标数据流为「名称 → 本地实体 ID → Business `/resolve` 关系扩展」；spec 只描述目标与当前缺口，未命名提供解析能力的 Business 端点路径。**

### 相关签名与约束

| 位置 | 要点 |
|---|---|
| `agent-guidelines.md:98` | `entity_name` 最多 48 可见字符；`entity_kind ∈ PERSON\|CHARACTER\|ACTOR\|RELATION_SUBJECT`；不可脱离 `entity_name` 单独使用 |
| `agent-guidelines.md:99` | `POST /api/client/evidence/resolve`：`{"entityType": "...", "ids": [1, ...]}`；`RELATION_SUBJECT` 沿 `subject_relation` 双向扩展 |
| `agent-guidelines.md:100` | `BusinessGateway.resolve_evidence(entity_type, entity_ids, *, token) -> dict \| list \| None`（无结果返回 None） |
| `agent-guidelines.md:101` | `RedisEntityNameLookup.lookup(...)`「仅作为 Business typed resolver 的兼容边界，不从 Vector Set 读取名称；名称解析失败必须 fail-closed」 |
| `agent-guidelines.md:108` | 实体 ID 不得拼接进 Vector Set `FILTER` 或 SQL 字符串 |
| `agent-guidelines.md:110` | 注入名称适配器的测试路径中 PERSON/CHARACTER 在名称约束内取并集；**「当前线上装配没有名称适配器，不能把这些单测路径视为已接通」** |
| `agent-guidelines.md:120-121` | 名称索引缺失/格式错误/异常 ⇒ `available=false` + `entity_resolution_unavailable`，**不得访问 Subject 索引**；名称无匹配 ⇒ `available=true` + `no_results`，不得扩大范围 |
| `agent-guidelines.md:133,135` | 测试要求：名称成功、PERSON/CHARACTER 同名并集、无匹配与故障 fail-closed；适配器断言路径/JSON body/Authorization |
| `.trellis/spec/backend/rag-retrieval-contract.md:18` | 「实体名称 \| `entity_name_lookup=None`，有名称即 `entity_resolution_unavailable` \| 名称参数和 Prompt 已存在不等于在线名称解析可用；显式 ID 的 Business `/resolve` 已接线」 |
| `rag-retrieval-contract.md:13` | 源码参照列 `backend/agent/main.py`、`app/rag/retrieval.py`、`app/rag/use_case.py`、`app/agent/client/rag_tools.py` |

### 跨层指南

`.trellis/spec/guides/cross-layer-thinking-guide.md` 中**没有**实体名称解析的专门条款。相关通用约束：

- `:24-30` 事实来源优先级：可执行源码/测试 > OpenAPI/Schema > README；冲突须同变更内修正文档
- `:36-44` JSON API 变更须同步 `docs/spec/openapi.yaml`、Java/Python 实现、shared 类型
- `:94-100` 「按 `JWT role → graph.py 节点 → tools 注册 → Prompt 来源/缓存` 检查，不从单条自然语言回答推断后端能力」

---

## 5. Business 侧现状（关键：跨层缺口判定）

### （a）Business 是否已有「按名称解析实体」的端点/service/mapper？—— **没有**

穷举证据：

1. **Controller**：`backend/business/client/src/main/java/top/zhaizz/client/controller/` 下 8 个控制器。`SubjectController.java` 暴露 `GET /api/client/subjects`（:43-46）、`/search`（:53-56）、`POST /lexical-search`（:64-67）、`/season`、`/schedule`、`POST /batch`（:95-99）、`GET /{id}`、`/years`、`/{id}/episodes`。`searchSubjects` 走 `SubjectSearchQueryDTO`，SQL 只对 `s.name` / `s.name_cn` 做 `LIKE`（`SubjectMapper.xml:14-15`）——**按作品名，不按人物/角色/声优名**。
2. **Service**：`client/service/` 全部为 Auth/Subject/User/Collection/Episode/Evidence/Tag/Verification；`impl/` 同名。**无 EntityResolver / PersonService / CharacterService**。
3. **Mapper**：`backend/business/**/mapper/*.java` 共 16 个。`EvidenceMapper.java:72-93` 的四个扩展方法全部以**本地 ID** 为参数（`selectSubjectIdsByPersonIds` / `...ByCharacterIds` / `...ByActorIds` / `selectRelatedSubjectIds`）。全仓 grep `FROM \`?person\`?|FROM \`?character\`?|person_alias|character_alias` 在 Business 只命中：`EvidenceMapper.xml:162`（`character_actor` JOIN）、`pojo/.../entity/PersonAlias.java:12`、`pojo/.../entity/CharacterAlias.java:12`。**没有任何 SQL 以 name 为条件查询 person/character/alias。**
4. **OpenAPI**：`docs/spec/openapi.yaml` 无 person/character/actor 名称检索路径；仅 `:1443-1484` 的 `/api/client/evidence/resolve`（`:1446` 明示 "ids 使用本地数据库主键"）。`:1446,1459` 是唯一的实体类型枚举定义处。
5. **DB Schema**：`docs/database/db-schema.sql` 已有数据与索引——`person.name`（:357）带 `idx_person_name`（:373）、`character.name`（:387）带 `idx_character_name`（:402）、`person_alias.name`（:415）带 `idx_person_alias_name`（:423）、`character_alias.name`（:434）带 `idx_character_alias_name`（:442）。**数据层与索引齐备，缺的只是 API。**

### （b）Business `/resolve` 现状

| 层 | 位置 | 内容 |
|---|---|---|
| Controller | `client/controller/EvidenceController.java:46-50` | `@PostMapping("/resolve")`，`Result<List<EvidenceCandidateVO>> resolveEvidence(@Valid @RequestBody EvidenceEntityBatchRequestDTO request)` |
| DTO | `pojo/src/main/java/top/zhaizz/pojo/dto/evidence/EvidenceEntityBatchRequestDTO.java:26` | `private EvidenceEntityType entityType;` + `ids` |
| Service | `client/service/impl/EvidenceServiceImpl.java:74-102` | `:79-81` `>50` 抛 `BizException(BAD_REQUEST)`；`:91-97` switch：`SUBJECT→ids`、`RELATION_SUBJECT→selectRelatedSubjectIds`、`PERSON→selectSubjectIdsByPersonIds`、`CHARACTER→selectSubjectIdsByCharacterIds`、`ACTOR→selectSubjectIdsByActorIds`；`:101` 再走 `batchEvidence` |
| 安全边界 | `EvidenceMapper.xml:122-171` | 每个扩展查询硬编码 `spc.source_active=1 AND p.source_active=1 AND s.type=2 AND s.nsfw=0 AND s.import_status=1` —— 满足 spec「只返回 type=2、nsfw=false、active=true」 |
| 鉴权 | `app/config/SecurityConfig.java:71` | `POST /api/client/evidence/resolve` 为 `permitAll()`（注意：与其它 client 端点不同） |
| OpenAPI | `openapi.yaml:1443-1484` | 请求 `{entityType, ids[1..50]}`；200 空数组表示无匹配；400 为类型缺失/ID 非正/超 50 |
| Agent 调用 | `app/adapters/business_http.py:128-141` | `resolve_evidence(entity_type, entity_ids, token=)` → `POST /api/client/evidence/resolve`，body `{"entityType":..., "ids":...}` |
| Agent 端口 | `app/agent/ports.py:54-60` | `BusinessGateway.resolve_evidence(...) -> dict \| list \| None` |
| Agent 接线 | `main.py:150` | `resolve_evidence_lookup=business.resolve_evidence` — **已接线** |
| Agent 消费 | `retrieval.py:329,354` | 显式 ID 与名称命中都调用同一个 `resolve_lookup` |

### （c）明确判定

> **跨层缺口是「Business 完全没有按名称解析实体的能力」，不是「已有能力但 Agent 未接线」。**

- Business 侧：无端点、无 service、无按名称查询的 mapper/SQL，OpenAPI 亦无契约。属**新增跨层 API 能力**。
- Agent 侧：`entity_name_lookup` 消费链路（`retrieval.py` 解析→校验→并入 `by_kind`→`/resolve` 扩展→fail-closed）**已完整实现并通过单测**；缺的只是组合根注入一个真实的 Business 名称解析适配器（`main.py:132/141`）。
- 数据层：名称列与索引已在 `db-schema.sql` 存在，无需 migration 新增列。

**任务体量**：Business 新功能 + Agent 接线，两者都真实存在，且 Business 侧是前置依赖。

---

## 6. typed 工具路径：名称参数形态

| 位置 | 内容 |
|---|---|
| `app/agent/client/rag_tools.py:16` | `EntityName = SafeTerm` |
| `:17` | `EntityKind = Literal["PERSON","CHARACTER","ACTOR","RELATION_SUBJECT"]` |
| `:15` | `StrictEntityIds` — ID 路径是严格正整数数组、max 50 |
| `:34-35 / :48-49` | `rag_search_subjects(entity_name: EntityName \| None = None, entity_kind: EntityKind \| None = None)` → 写入 `RetrievalQuery` |
| `:70-71 / :89-90` | `rag_discover_subjects` 同 |
| `:111-112 / :130-131` | `rag_recommend_subjects` 同 |
| `:38` | docstring：**「实体名称会先解析为本地 ID」** — 与生产行为不符（生产返回 `entity_resolution_unavailable`） |
| `app/rag/schemas.py:68-69` | `entity_name: SafeTerm \| None`、`entity_kind: Literal[...]` |
| `schemas.py:88` | `entity_name` 计入 `has_filter` 意图判定 |
| `schemas.py:93-94` | `entity_kind` 非空而 `entity_name` 为空 ⇒ `ValueError("entity_kind 必须与 entity_name 一起提供")` |

**形态结论：名称参数是字符串（`SafeTerm`），ID 参数是独立的正整数数组字段。三条 RAG 工具都同时暴露两套参数（显式 ID 与名称字符串）。** 即 spec 所称「名称参数和 Prompt 已存在不等于在线名称解析可用」——工具与 Prompt 侧已就绪，运行期不可用。

`SafeTerm` 约束见 `schemas.py`（strip_whitespace、≤48、拒绝控制字符），与 spec `agent-guidelines.md:98` 一致。

---

## 7. 既有测试

### `backend/agent/tests/adapters/test_entity_name_lookup.py`（全文 31 行）

| 用例 | 行 | 断言 |
|---|---|---|
| `test_lookup_delegates_typed_name_without_building_redis_expression` | `:10-19` | 注入 `resolver` lambda（`:13-15`），断言 `RedisEntityNameLookup(index_version="v1", resolver=resolver).lookup("花泽香菜", entity_kind="PERSON") == [EntityNameMatch("PERSON", 7)]`，且调用形态为 `[("花泽香菜","PERSON",50)]` |
| `test_vector_set_name_lookup_fails_closed_without_business_resolver` | `:22-24` | 不传 resolver 时 `pytest.raises(RuntimeError, match="Business typed resolver")` |
| `test_invalid_resolver_response_fails_closed` | `:27-30` | resolver 返回 dict 时 `RuntimeError, match="response invalid"` |

**结论：测的是死代码本身的契约（适配器边界与 fail-closed），不是接线后的行为。** 全程用手写 lambda 充当 resolver，不接触生产组合根，也不断言 `main.py` 是否注入。

### 相关测试（均为注入式单测，不能证明在线可用）

- `tests/rag/test_entity_filters.py:58-66` `_service(..., name_lookup=None)` 工厂：名称解析器**由测试注入**
- `:114-131` `test_entity_name_resolves_to_typed_id_then_business_subjects` — 注入 `name_lookup` 返回 `[{"entity_kind":"PERSON","entity_id":17}]`，断言 `resolver.calls == [("PERSON",[17])]`（即名称 → ID → /resolve 的目标流）
- `:133-...` 同名无 kind 的 PERSON/CHARACTER 并集
- `:185-198` `test_entity_name_lookup_failure_is_fail_closed_before_business_resolve` — lookup 抛异常 ⇒ `available=False`、`reason=entity_resolution_unavailable`、`index.calls == 0`
- `:317,327,338` 其余 `entity_resolution_unavailable` 断言
- `tests/adapters/test_business_http.py` 覆盖 `/resolve` 的 HTTP 形状

**综合判定：Agent 侧「名称→ID→/resolve」逻辑已被单测钉住且通过，但因组合根注入 `None`，这些测试路径与生产路径不一致（spec `agent-guidelines.md:110` 已明文警告）。**

---

## 8. 历史背景（归档，供参考）

`.trellis/tasks/archive/2026-09/09-03-bangumi-rag-retrieval/history/phase7-entity-name-report.md`：2026-09-04 曾以 RediSearch `idx:rag:entity:<version>` 实现名称解析（`:10`），`:12` 记载名称→typed local ID→Business `/resolve` 的链路，`:13` 记载 fail-closed 语义。`:3` 说明该 RediSearch 名称索引**将由 MySQL FULLTEXT 取代**。`phase8-redis-report.md:31` 记载当时 Redis 非 RediSearch/Redis Stack 实例，`FT.*` 不可用。

`.trellis/workspace/zhaizzH/journal-1.md:188`：「F08 实体名称解析等待 Business 权威接口。」——与本次缺口判定一致。

---

## 9. Caveats / Not Found

- **未找到** Business 侧任何名称解析端点、DTO、service 方法或按名称查询的 SQL。此项为「确认不存在」，非「未搜索」。
- **未找到** `docs/spec/openapi.yaml` 中除 `/api/client/evidence/resolve` 外的实体（person/character/actor）相关路径。
- **未找到** 任何断言 `main.py` 注入非 None 解析器的测试。
- `.trellis/spec/guides/cross-layer-thinking-guide.md` 无实体名称解析专门章节（已确认）。
- 未验证运行时数据库是否实际存在 person/character 数据与索引（本任务为源码审计）。
- `SecurityConfig.java:71` 将 `/resolve` 设为 `permitAll()`，与解析链的鉴权期望是否一致未在本任务结论范围内。
- 未查证 Agent 是否有针对名称解析的缓存层（grep 未见相关实现）。
