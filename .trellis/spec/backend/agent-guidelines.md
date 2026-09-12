# Agent 编排与流式协议

## 组合与路由

- `backend/agent/main.py` 是组合根，创建 store、配置仓库、Business Gateway、RAG 用例和 LangGraph。
- 领域节点只依赖 `AgentDependencies` 或端口，不读取环境变量、不创建基础设施客户端。
- `app/agent/graph.py` 先按角色分流；普通用户只允许 `search_agent / discover_agent / recommend_agent`。
- `ADMIN` 直接进入 `admin_agent`，其当前工具集不含 RAG；角色工具、Prompt 缓存、语言与日期的完整现状见 [Agent 运行与提示词契约](./agent-runtime-contract.md)。
- 每个节点只注册完成职责所需的工具；新增工具先确定最小可见节点。
- RAG 关闭时使用显式不可用适配器与 Business fallback，不能把检索失败静默伪装为空结果。
- RAG 索引运行前必须验证 Redis 提供 Vector Set 命令（至少 `VADD`、`VSIM`、`VREM`）；MySQL 8.4 `ngram` FULLTEXT 负责词法召回，Redis 8 Vector Set 只负责语义向量召回。没有 Vector Set 时保持 `RAG_ENABLED=false` 或走 Business fallback，不得宣称已发布 RAG。
- 2026-09-09 历史记录确认 v1 `subject-profile-v1` release 激活及 24 小时灰度/回滚，但本次源码审计不证明当前运行数据库状态；`RAG_ENABLED` 代码默认仍为 `false`。完整发布、灰度和回滚契约见 [RAG 检索与版本发布契约](./rag-retrieval-contract.md)。
- 通过权威回查的候选必须经 Evidence API 补充证据字段（`_enrich_evidence`）；Evidence 失败、错误、部分或不安全响应时必须 fail-closed（`available=false`、空候选），并记录 `rag.evidence.enriched` 事件。
- `RetrievalQuery` 的 `person_ids`、`character_ids`、`actor_ids`、`relation_subject_ids` 只能通过 Business `/api/client/evidence/resolve` 解析为活跃、非 NSFW 动画 Subject allowlist；解析失败不得访问 Redis 或返回未过滤候选。
- Agent 提示词禁止陈述工具返回中不存在的证据；`app/rag/use_case.py::_compact` 当前输出 20 个键，包含 `airDate`、播出状态、来源、匹配事实和检索解释。字段清单以该函数与 `tests/rag/test_evidence_contract.py` 核对，缺项按字段使用空列表、空字符串或 None；不能用旧字段数量代替契约检查。
- 故障矩阵必须在测试中覆盖：Redis/Embedding/Business/Evidence 每层独立故障与组合故障，证明 fail-closed 或既定降级行为。
- 词法响应中的 `indexVersion` 是在线语义查询的唯一版本来源；不得使用配置默认版本或 Redis alias 猜测 active 版本。灰度异常时先关闭功能开关，再通过 MySQL release store 切回已验证 release，旧投影在回滚窗口结束前保留。

### Scenario: Subject batch 权威边界与 Evidence 过滤顺序

#### 1. Scope / Trigger

- 触发：修改 Agent `RagRetrievalService`、Business `/api/client/subjects/batch` 或 Evidence DTO/VO；尤其是新增 `active`、标签、评分、年份、季度和播出状态过滤。
- 目的：防止把不完整的 batch 响应当成 Evidence 事实，或在 Evidence 补全前错误丢弃候选。

#### 2. Signatures

- `POST /api/client/subjects/batch` 请求：`{ "subjectIds": [1, ...], "excludeCollected": boolean }`。
- batch item 至少包含：`id`, `type`, `nsfw`, `active`；其中 `active` 必须由 `subject.import_status = 1` 派生。
- `POST /api/client/evidence/batch` 返回 `EvidenceCandidateVO[]`，每项必须包含 `subjectId`, `type`, `nsfw`, `active`，以及可选的 `metaTags`, `score`, `ratingTotal`, `airDate` 等事实字段。
- `RagRetrievalService._authoritative_result(...) -> RetrievalResult`：先校验 batch 安全边界，再批量 Evidence 回查，最后执行结构化过滤和重排。

#### 3. Contracts

- batch 阶段只校验 `type=2`、`nsfw=false`、`active=true` 和排除 ID；不得在该阶段读取不存在的 `metaTags`/`airStatus` 字段。
- Evidence 响应必须覆盖候选 ID 的全集；当前实现拒绝缺项、额外 ID、非法 ID、错误类型、NSFW 或 inactive。重复的合法 ID 当前被 `by_id` 覆盖，尚未显式拒绝；唯一性应作为待补校验，不能宣称已经受保护。
- `meta_tags`、评分、评分人数、年份、季度和播出状态过滤只能使用 Evidence 字段；Evidence 缺少需要的字段时必须排除候选，不得用 Redis 详情伪造事实。
- 所有外部 `id/subjectId` 必须拒绝布尔值、非数字、非正数和溢出转换；坏行不能抛出未处理异常进入 fallback。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| batch item 缺少 `active` 或 `active != true` | 丢弃该候选；不进入 Evidence/模型上下文 |
| Evidence 超时、错误、部分结果或字段不安全 | `available=false`、`reason=evidence_unavailable` |
| Evidence 过滤后为空 | `available=true`、`reason=no_results`，不扩大查询范围 |
| ID 为布尔值、非正数或不可转换 | 丢弃该行并继续安全处理；不得 500 |
| 无 ACTIVE release 或 Business lexical 缺 `indexVersion` | 词法/混合链 fail-closed，允许既定 Business fallback |

#### 5. Good/Base/Bad Cases

- Good：batch 返回 `active=true`，Evidence 返回完整 `metaTags`，Agent 再执行标签/年份过滤并附证据。
- Base：batch 有候选但 Evidence 缺一项，整个批次不可用，不把其余候选静默送入模型。
- Bad：因为 batch 没有 `metaTags` 就提前过滤，或使用 Redis 的 `air_status` 覆盖 Evidence；把 `subjectId=true` 转成 `1` 更是禁止行为。

#### 6. Tests Required

- Java：batch VO 序列化 `active`；Service 从 `import_status` 映射 active；OpenAPI 与 Controller 测试同步。
- Python：batch `active` 安全边界、Evidence 完整性、Evidence 后结构化过滤、非法 ID fail-closed/不抛异常。
- 运行 `pytest tests/rag tests/jobs/indexer`、`mvn -B clean test`，并对真实 shadow 报告断言 `evidenceCompleteness=1.0`。

#### 7. Wrong vs Correct

#### Wrong

```python
if not detail.get("metaTags"):
    continue  # batch 没有该字段，错误地把合法候选过滤掉
subject_id = int(row.get("subjectId"))  # True 会被转换成 1
```

#### Correct

```python
if detail.get("active") is not True:
    continue
safe, ok = self._enrich_evidence(candidates, token, evidence_lookup)
if not ok:
    return RetrievalResult(available=False, items=[], reason="evidence_unavailable")
safe = [item for item in safe if self._matches_query_filters(item.evidence or {}, query)]
```

## RAG 结构化实体筛选契约

### 1. Scope / Trigger

- Trigger：RAG 工具新增人物、角色、声优和关联条目 ID 过滤，并跨 Agent → Business → MySQL 传递实体关系。

### 2. Signatures

- `RetrievalQuery`: `person_ids`, `character_ids`, `actor_ids`, `relation_subject_ids` 均为最多 50 个正整数；`entity_name` 为最多 48 个可见字符，`entity_kind` 可选值为 `PERSON|CHARACTER|ACTOR|RELATION_SUBJECT`，且不能脱离 `entity_name` 单独使用。
- `POST /api/client/evidence/resolve`: `{ "entityType": "PERSON|CHARACTER|ACTOR|SUBJECT|RELATION_SUBJECT", "ids": [1, ...] }`；`RELATION_SUBJECT` 沿 `subject_relation` 双向扩展。
- `BusinessGateway.resolve_evidence(entity_type, entity_ids, *, token) -> dict | list`。
- `RedisEntityNameLookup.lookup(entity_name, *, entity_kind, limit) -> list[EntityNameMatch]`；仅作为 Business typed resolver 的兼容边界，不从 Vector Set 读取名称；名称解析失败必须 fail-closed。
- `plan_retrieval_query(query) -> RetrievalQuery` 只补全带明确标记的中文年份、季度、播出状态、评分和评分人数；显式结构化字段优先。

### 3. Contracts

- Business 只返回 `type=2`、`nsfw=false`、`active=true` 的证据候选；Agent 仅提取 `subjectId`。
- 多种实体过滤取交集；allowlist 同时约束 Redis 召回和 Business fallback，再执行 Subject 权威回查与 Evidence 回查。
- 实体 ID 不得拼接进 Vector Set `FILTER` 或 SQL 字符串。
- 目标边界：名称应先解析为本地实体 ID，再通过 Business `/resolve` 做关系扩展。当前 `main.py` 在开关两种分支都注入 `entity_name_lookup=None`，`_lookup_entity_name` 遇到名称立即返回 `entity_resolution_unavailable`；只有显式实体 ID 的 `/resolve` 链已接线。不得把注释中的 Business 名称解析方案描述为已实现。旧 `RedisEntityNameLookup` 未接入在线组合根。
- 注入名称适配器的测试路径中，PERSON 与 CHARACTER 的名称候选可在名称约束内取并集；与显式 ID/关系字段仍取交集。查询声优关系时必须保留 ACTOR 语义。当前线上装配没有名称适配器，不能把这些单测路径视为已接通。

### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| ID 非正整数、超过 50 个 | Pydantic 校验失败，工具返回空结果 |
| `/resolve` 超时、错误、异常或返回缺失/不安全字段 | `available=false`、`reason=entity_resolution_unavailable` |
| `/resolve` 返回空集合 | `available=true`、`reason=no_results`，不得扩大查询范围 |
| Redis 故障 | Business fallback 仍应用同一 allowlist |
| 名称索引缺失、返回格式错误或解析异常 | `available=false`、`reason=entity_resolution_unavailable`，不得访问 Subject 索引 |
| 名称无匹配 | `available=true`、`reason=no_results`，不得扩大查询范围 |

### 5. Good/Base/Bad Cases

- Good：`person_ids=[7]` 解析出 Subject 42，Redis 返回 41/42 时只回查 42。
- Base：没有实体过滤时保持旧检索路径和 Business fallback。
- Bad：把 `person_ids` 作为 `@person_id:{7}` 拼入 Subject 索引，或解析失败后继续返回 Redis 候选。

### 6. Tests Required

- Schema：严格拒绝字符串、布尔值、非正数和第 51 个 ID。
- Retrieval：实体解析调用顺序、交集、空集合、异常 fail-closed、Redis 故障 fallback allowlist。
- Retrieval：名称成功、PERSON/CHARACTER 同名并集、名称无匹配与名称解析故障 fail-closed。
- Planner：明确条件提取、显式字段优先，以及不明确/越界提示保留在原始语义查询。
- Adapter：断言 `/api/client/evidence/resolve` 方法、路径、JSON body 和 Authorization；名称查询的转义、类型映射和 malformed response。

### 7. Wrong vs Correct

#### Wrong

```python
expression = f"@subject_id:{{{query.person_ids[0]}}}"
```

#### Correct

```python
allowed = resolve_evidence("PERSON", query.person_ids, token=token)
candidates = [item for item in candidates if item.subject_id in allowed_subject_ids]
```

名称查询必须经过同一条权威链：

```python
matches = entity_name_lookup(query.entity_name, entity_kind=query.entity_kind, limit=50)
allowed = resolve_evidence(match.entity_kind, ids, token=token)
```

## SSE 契约

- 运行时只产生 `AgentEvent`，事件类型为 `answer / thinking / function_call / status / end`。
- `app/api/sse.py` 是序列化单一入口；结束事件必须设置 `is_end=true`。
- 保持 `text/event-stream`、`Cache-Control: no-cache`、`X-Accel-Buffering: no`。
- 改事件字段时同步 `schemas/sse.py`、前端 `useAgentChat.ts` 与 `docs/spec/openapi.yaml`。
- 浏览器只请求 Spring 代理路径，不配置或直连 Agent 的 `:8090`。

## 安全写操作

1. 预览工具查询权威 Business 数据并生成强类型 `PendingAction`。
2. `ChatService` 按用户与会话把动作写入 Redis；成功写入后才允许把动作视为可确认。
3. 用户明确确认后，执行工具只读取 `InjectedState` 中的 action 或 preview ID。
4. 基础设施错误导致结果不确定时保留动作；`PREVIEW_CHANGED` 必须重新确认。
5. 取消只清理待确认状态，不修改业务数据。

参考：`app/agent/client/actions/wishlist.py`、`collection_progress.py`、`app/chat/pending_action.py`。

### 待确认动作持久化失败矩阵

`streaming.py` 会记录并报告 `on_pending_action` 异常，然后继续发送结束事件；调用方必须依据 `status` 错误事件执行重试提示，不能把动作宣告为已持久化。任何新增或修改必须满足以下契约：

| 条件 | 必须行为 |
|---|---|
| 新建/替换动作写 Redis 成功 | 返回可确认状态，并绑定 `user_id`、`session_id`、`preview_id`/nonce 与 TTL |
| 新建/替换动作写 Redis 失败 | 不宣告动作可确认；不得继续执行不可见动作；向调用方返回可重试的失败语义 |
| 已有旧动作且替换失败 | 不能让下一次确认误执行旧动作；清除旧动作或使其版本失效，并记录可关联 trace |
| 用户取消 | 仅删除同一用户/会话的待确认动作，不能修改 Business 数据 |
| 确认时 preview 已变化/过期 | 返回 `PREVIEW_CHANGED`/过期错误，必须重新预览确认 |

最低回归场景：预存旧动作 → `REPLACE` 失败 → 再次确认；断言旧动作不会被执行。

## 认证与配置

- Agent 使用共享 `JWT_SECRET` 本地 HS256 验签，避免回调 Spring 形成代理环路。
- 管理路由必须使用 `require_admin`，不能只靠提示词限制。
- `Settings` 使用 `extra="forbid"`；新增环境变量同步 `app/config.py` 与 `.env.example`。
- `LLM_PROVIDER` 支持 `deepseek|dashscope`；显式设置时缺少对应 Key 必须失败。未设置时当前实现会按 DeepSeek→DashScope Key 存在性回退并记录 warning，不得把“显式选择”写成必需事实。
- LLM 模型/温度等运行时配置优先读取 Redis `agent:config:model`；本地缓存约 5 秒，Redis 不可用时回退环境配置。
- 托管 Prompt 在启动时从 Redis 建立快照；单项读取失败回退仓库内本地 Prompt，不因 Prompt Redis 不可用阻止启动。
- 共享 `.env` 中由 importer 使用的字段也必须声明在 `Settings` 中，否则 `extra="forbid"` 会导致启动失败；业务读取仍需说明真实来源。
- 日志只记录供应商和模型名，绝不记录 Key、JWT、用户输入或完整回答。

### 健康检查语义

- Agent `/api/client/agent/health` 当前始终返回 HTTP 200，并只反映 LLM 配置是否可解析；不代表 Redis、Business、RAG 或 MinIO 可用。
- Business 的 liveness/readiness 配置见 `backend/business/app/src/main/resources/application.yml`；readiness 检查 MySQL 与 Redis，Security 只匿名放行 `/actuator/health` 与 `/actuator/health/**`，其他未显式允许的 URL 仍拒绝；修改健康探针时必须补授权测试。
- 变更健康检查时必须明确：检查项、HTTP 状态、依赖不可用时的响应、公开字段和是否允许匿名访问。

## 离线任务

- importer、indexer、scheduler 使用 `python -m jobs.<name>...` 运行并返回明确退出码。
- indexer 只有显式 `--activate` 且全部报告通过时才激活 MySQL `search_index_release`。
- scheduler 使用 Asia/Shanghai 规则；仓库没有常驻宿主配置，不得假设已有 cron/systemd/容器部署。

### Scenario: Person/Character 回填报告

#### 1. Scope / Trigger

- 触发：运行 `jobs.backfill.main --report` 或定时采集回填状态。

#### 2. Signatures

- 文本：`python -m jobs.backfill.main --report`。
- JSON：`python -m jobs.backfill.main --report-json`。
- `EntityDetailJobRepository.generate_report() -> BackfillReport`。

#### 3. Contracts

- 报告字段包含 `totalJobs/completed/pending/failed/abandoned/coveragePct/failureReasons`。
- stale 字段为 `staleEntities/staleByKind`，统计 active Person/Character 且 `detail_status <> COMPLETE` 的实体。
- 报告只读，不认领、暂停、恢复或修改任务；错误正文不得输出到 JSON。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 无任务 | 覆盖率为 0，报告仍成功生成 |
| 任务失败/放弃 | 按 `last_error_code` 聚合，不输出错误正文 |
| active 实体未完成详情 | 计入 `staleEntities` 与 `staleByKind` |
| 数据库查询失败 | CLI 返回非零退出码，不伪造空报告 |

#### 5. Good/Base/Bad Cases

- Good：调度器采集 `--report-json`，按同一时间窗口记录覆盖率和 stale 数量。
- Base：人工使用 `--report` 查看摘要。
- Bad：报告命令顺便认领任务，或把 API 错误正文写入报告。

#### 6. Tests Required

- Backfill repository 单测断言覆盖率、失败原因、stale 按实体类型聚合及 JSON 字段。
- CLI/编译检查断言 `--report-json` 可导入并返回稳定字段。

#### 7. Wrong vs Correct

```text
Wrong: 只统计 COMPLETED/TOTAL，忽略 active 实体仍处于 SUMMARY_ONLY 的 stale 状态。
Correct: 同时统计任务状态和 person/character 的 detail_status，并通过 --report-json 输出。
```

### 离线任务最低契约

- importer CLI 的 `--mode` 为 `full|season|recent|since|sample`；`--dry-run` 只扫描，不打开数据库或写对象存储，当前仅支持 full 扫描语义。
- importer 并发 worker 上限为 10；断点由扫描 ID 的 SHA-256、offset 和最后条目共同校验，扫描结果变化时拒绝复用旧断点。
- importer 使用 MySQL `GET_LOCK` 做跨进程互斥；每个 worker 独立 Session，失败必须 rollback、关闭连接并返回非零结果。
- indexer 报告缺失、版本不一致、契约/指标不达标时必须 fail closed；只有显式 `--activate` 且所有报告通过时才更新 MySQL `search_index_release`，旧版本投影不得先删除。
- scheduler 使用 Asia/Shanghai 的固定时刻（每日 recent、每周 since、季度 full），同一分钟同模式去重；仓库不提供常驻宿主、重叠任务终止或重启托管。
- 运行环境仅提供普通 Redis 而未加载 Vector Set 时，不能执行 `jobs.indexer`；Redis Vector Set 与 MySQL `search_document` 必须使用同一 `indexVersion`，发布指针只在 MySQL 更新。
- 以上契约的参数、退出码、报告字段或阈值发生变化时，必须同时更新本文件和 `quality-guidelines.md` 的验证清单，并补失败路径测试。

### Scenario: recent 导入日历源失败

#### 1. Scope / Trigger

- 触发：修改 `jobs.importer.main` 的 `recent` 扫描、代理配置或导入断点/状态处理。
- 目的：避免 Bangumi 日历请求失败时把“未扫描到条目”误记为成功，导致断点无法恢复。

#### 2. Signatures

- 命令：`python -m jobs.importer.main --mode recent [--resume]`。
- 扫描源：`BangumiClient.get_calendar() -> list[dict]`。
- 代理环境变量：`HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`；只由进程环境注入，不写入日志或任务记录。

#### 3. Contracts

- `recent` 必须先成功获取并去重日历 ID，再调用 `_run_batch`。
- 日历获取异常必须抛出 `RuntimeError("日历获取失败")`，由 `main()` 统一将当前 `import_record` 标为 `FAILED`，退出码为 `1`。
- 失败时不得调用 `complete_import_record(..., "COMPLETED")`，不得清除 `checkpoint_json`、累计成功/失败计数或把 `subject_count` 伪造为 0 成功。
- 成功时 checkpoint 的 `offset` 必须到达本次日历 ID 总数；已有条目可返回 `SKIPPED`，这不等于导入失败。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| `get_calendar()` 返回有效列表 | 去重 ID 后执行批处理，完成时记录 `COMPLETED` |
| `get_calendar()` 超时、代理拒绝或响应异常 | 记录 `FAILED`、保留 checkpoint、返回退出码 1 |
| `--resume` 且记录为 `RUNNING/FAILED` | 校验扫描 ID SHA-256、offset 和最后 ID；不匹配则拒绝恢复 |
| 日历条目已存在且 `import_status=1` | 记录 `SKIPPED`，推进 checkpoint，不计入 failure |
| 代理不可用 | 不把空日历当作成功；错误日志只保留归一化错误类型/消息 |

#### 5. Good/Base/Bad Cases

- Good：代理可用，日历 113 条，resume 推进到 `offset=113`，所有条目已存在时状态为 `COMPLETED`、`failure_count=0`。
- Base：日历请求中断，状态为 `FAILED`，下次使用同一 checkpoint 可继续，不重复伪造成功。
- Bad：捕获日历异常后 `return 0`，让主流程把未扫描批次标记为 `COMPLETED`。

#### 6. Tests Required

- `tests/jobs/importer/test_recent_failure.py`：日历客户端抛异常时断言 `run_recent` 抛出 `RuntimeError`，消息为“日历获取失败”。
- `tests/jobs/importer` 全套：断言成功、跳过、失败计数和 checkpoint 行为不回归。
- 运行 `python -m compileall -q jobs/importer` 与 `git diff --check`。

#### 7. Wrong vs Correct

#### Wrong

```python
try:
    calendar = client.get_calendar()
except Exception:
    return 0  # main() 会错误地写入 COMPLETED
```

#### Correct

```python
try:
    calendar = client.get_calendar()
except Exception as error:
    logger.error("日历获取失败: %s", sanitize_import_error(error))
    raise RuntimeError("日历获取失败") from error
```

### Scenario: search indexer 基础设施错误码

#### 1. Scope / Trigger

- 触发：修改 `jobs.indexer.main.run_search_batch` 的 Embedding、Redis 或任务重试处理。
- 目的：错误码必须能区分 Embedding 与 Redis 故障，避免排障时把 Embedding 网络问题误判为 Redis 故障。

#### 2. Signatures

- `run_search_batch(...) -> IndexBatchResult`：批量消费 `search_index_job`，失败任务进入可重试状态。
- `SearchIndexJobRepository.mark_failed(job_id, error_code, error_message, retry_seconds, claimed_at)`：写入错误码并设置 `next_retry_at`。

#### 3. Contracts

- `EmbeddingUnavailable` 映射为 `EMBEDDING_UNAVAILABLE`。
- `EmbeddingRateLimited` 映射为 `EMBEDDING_RATE_LIMITED`。
- Redis 连接/超时异常映射为 `REDIS_UNAVAILABLE`。
- 上述异常都必须保持失败可重试语义；不能因为错误码分类改变而确认索引成功或激活 release。
- 其他异常保留稳定类型名，不把数据库/配置错误伪装成 Redis 故障。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| Embedding 服务不可用 | `EMBEDDING_UNAVAILABLE`、`FAILED + next_retry_at` |
| Embedding 限流 | `EMBEDDING_RATE_LIMITED`、`FAILED + next_retry_at` |
| Redis 连接或超时 | `REDIS_UNAVAILABLE`、`FAILED + next_retry_at` |
| 数据库/实体加载异常 | 使用异常类型名，不生成 Redis/Embedding 专属码 |
| 重试次数耗尽 | 由仓储层进入 `ABANDONED`，gate 必须拒绝发布 |

#### 5. Good/Base/Bad Cases

- Good：EmbeddingUnavailable 记录为 `EMBEDDING_UNAVAILABLE`，任务保留 `next_retry_at`。
- Base：Redis 写入连接失败记录为 `REDIS_UNAVAILABLE`，不写入 `search_document` 完成状态。
- Bad：对所有可重试异常统一写 `REDIS_UNAVAILABLE`，导致监控和修复方向错误。

#### 6. Tests Required

- `tests/jobs/indexer/test_main_multi_entity.py`：断言 EmbeddingUnavailable、EmbeddingRateLimited、Redis 连接失败分别产生准确错误码。
- 断言三类故障的 `IndexBatchResult` 均为 `retried=1、failed=0`，且仓储收到 `mark_failed`。
- 运行 `pytest tests/jobs/indexer tests/jobs/scheduler tests/rag` 与 `python -m compileall -q jobs/indexer`。

#### 7. Wrong vs Correct

#### Wrong

```python
code = "REDIS_UNAVAILABLE" if _is_retryable(error) else type(error).__name__
```

#### Correct

```python
if isinstance(error, EmbeddingUnavailable):
    code = "EMBEDDING_UNAVAILABLE"
elif isinstance(error, RedisConnectionError):
    code = "REDIS_UNAVAILABLE"
```

### Scenario: Shadow Vector Set 与 MySQL release 发布与回滚

#### 1. Scope / Trigger

- 触发：重建 RAG index version、生成容量/质量报告、切换或回滚 MySQL active release。

#### 2. Signatures

- `ShadowIndexManager.prepare_switch(version, quality_report_path, gate_passed) -> SwitchPlan`。
- `ShadowIndexManager.execute_switch(plan) -> SwitchResult`。
- `ShadowIndexManager.rollback(previous_version) -> SwitchResult`。
- `build_capacity_report(sample_bytes, sample_count, catalog_count, redis_used_memory, available_bytes)`。

#### 3. Contracts

- 新版本写入 `rag:vectors:{entity_kind}:{version}` shadow key 和 `search_document` 行；旧版本在回滚窗口内不得删除。
- 只有 `quality/capacity/eval/latency/human` 五份同一 `indexVersion/profileVersion` 报告通过 gate，`execute_switch` 才能调用 MySQL release store 激活版本；Redis 不提供 active alias。
- gate 必须满足：正式 eval 为 `RELEASE_CANDIDATE` 且 120/120 通过，Evidence completeness=100%，Recall@20≥0.85、MRR@10≥0.90、nDCG@10≥0.75，Redis P95<250ms、hydrated P95<500ms，容量≤60%，人工检查≥20 且严重错误为 0。
- 容量投影利用率必须不高于 60%；空样本报告必须 `allowed=false`。
- `rollback` 只切回已验证的 MySQL release，不删除任何 Redis Vector Set 或 MySQL 投影。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 报告缺失/版本不一致 | gate fail-closed，拒绝 release 切换 |
| Vector Set `VADD/VSIM/VREM` 不可用 | 不建向量、不激活 release，保持 RAG 关闭 |
| 容量利用率 > 60% | 报告拒绝发布 |
| release 切换失败 | 返回失败结果，保留旧 active release |
| 需要回滚 | 指向已验证的旧版本，保留新索引供排查 |

#### 5. Good/Base/Bad Cases

- Good：先写 MySQL/Vector Set 双 shadow → 生成同版本报告 → gate → 在 MySQL 事务中激活 release → 观察后再清理旧版本。
- Base：gate 未通过时只保留 shadow 构建结果，不影响在线旧 release。
- Bad：直接覆盖 active 版本、只写一侧投影、先删除旧版本，或用 `--activate` 绕过报告。

#### 6. Tests Required

- Shadow 单测断言 gate 未通过拒绝切换、旧 release 保留、rollback 调用正确版本。
- 容量报告单测断言投影、空样本拒绝和 JSON 字段稳定。
- Redis 门禁断言 `COMMAND INFO VADD/VSIM/VREM` 可用后才允许后续灰度；Business 词法响应缺少 `indexVersion` 时拒绝查询。

#### 7. Wrong vs Correct

```text
Wrong: 删除旧 Vector Set 后直接把新 key 当作 active，或让 Agent 自己猜版本。
Correct: 保留旧投影，通过 MySQL `search_index_release` 切换；词法响应携带版本，Agent 查询同版本 Vector Set，异常时回滚 release。
```

> 详细的 `RAG_ENABLED` 开关边界、灰度观察、回滚顺序和清理窗口见 [RAG 检索与版本发布契约](./rag-retrieval-contract.md)。

## Scenario: MySQL FULLTEXT 与 Vector Set 双投影

### 1. Scope / Trigger

- 触发：新增或修改 RAG indexer、词法召回 API、Vector Set 查询或索引发布流程。

### 2. Signatures

- `POST /api/client/subjects/lexical-search`：`q/tags/scoreMin/scoreMax/year/weekday/subjectIds/limit`。
- 成功响应：`{indexVersion, profileVersion, candidates[]}`；无 active release 返回 503。
- Vector Set key：`rag:vectors:{entity_kind}:{indexVersion}`；查询命令使用 `VSIM ... WITHSCORES WITHATTRIBS`。

### 3. Contracts

- MySQL `search_document` 是可重建投影；`search_index_release` 是唯一 active 版本指针。
- 一个 index job 必须先写 MySQL lexical shadow，再写 Vector Set；任一侧失败不得确认 job 完成。
- Agent 只使用 Business 返回的 `indexVersion` 查询 Vector Set，禁止跨版本融合。

### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 缺少 active release 或响应无 `indexVersion` | 词法/混合检索 fail-closed 到既有 Business 搜索 |
| Vector Set 命令不可用 | 不写入/不发布，返回可重试错误 |
| MySQL 投影写入失败 | 不写入完成状态，保留任务重试 |
| 旧版本清理请求 | 仅在回滚窗口结束且人工确认后执行 |

### 5. Good / Base / Bad Cases

- Good：双投影同一版本、gate 通过后激活 MySQL release，RRF 只融合同版本候选。
- Base：Vector Set/Embedding 失败时返回 Business 精确或词法 fallback，并记录结构化事件。
- Bad：把 Redis active alias 当作发布事实，或将 `subjectIds` 排除列表误传为 Business allowlist。

### 6. Tests Required

- Adapter：断言 `VADD/VSIM/VREM` 参数、版本 key 和属性解析。
- Retrieval：断言 `candidates`、`indexVersion` 解析和版本缺失 fail-closed。
- Indexer：断言 MySQL upsert 与 Vector Set 写入任一失败时 job 不完成。

### 7. Wrong vs Correct

#### Wrong

```python
redis.execute_command("FT.SEARCH", "idx:rag:subject:active", query)
```

#### Correct

```python
release = business.lexical_search(typed_request)
rows = vectors.vsim(release["indexVersion"], embedding)
```
