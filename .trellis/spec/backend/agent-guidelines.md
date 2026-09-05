# Agent 编排与流式协议

## 组合与路由

- `backend/agent/main.py` 是组合根，创建 store、配置仓库、Business Gateway、RAG 用例和 LangGraph。
- 领域节点只依赖 `AgentDependencies` 或端口，不读取环境变量、不创建基础设施客户端。
- `app/agent/graph.py` 先按角色分流；普通用户只允许 `search_agent / discover_agent / recommend_agent`。
- 每个节点只注册完成职责所需的工具；新增工具先确定最小可见节点。
- RAG 关闭时使用显式不可用适配器与 Business fallback，不能把检索失败静默伪装为空结果。
- RAG 索引运行前必须验证 Redis 提供 Vector Set 命令（至少 `VADD`、`VSIM`、`VREM`）；MySQL 8.4 `ngram` FULLTEXT 负责词法召回，Redis 8 Vector Set 只负责语义向量召回。没有 Vector Set 时保持 `RAG_ENABLED=false` 或走 Business fallback，不得宣称已发布 RAG。
- 通过权威回查的候选必须经 Evidence API 补充证据字段（`_enrich_evidence`）；Evidence 失败、错误、部分或不安全响应时必须 fail-closed（`available=false`、空候选），并记录 `rag.evidence.enriched` 事件。
- `RetrievalQuery` 的 `person_ids`、`character_ids`、`actor_ids`、`relation_subject_ids` 只能通过 Business `/api/client/evidence/resolve` 解析为活跃、非 NSFW 动画 Subject allowlist；解析失败不得访问 Redis 或返回未过滤候选。
- Agent 提示词禁止陈述工具返回中不存在的证据；`_compact` 输出必须包含全部 18 个证据字段，缺失字段使用空默认值。
- 故障矩阵必须在测试中覆盖：Redis/Embedding/Business/Evidence 每层独立故障与组合故障，证明 fail-closed 或既定降级行为。

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
- 名称解析由 Business typed resolver 负责；Vector Set 只保存向量属性，名称命中后必须先按类型调用 Business `/resolve`，不得把向量属性直接输出给模型。`RELATION_SUBJECT` 映射到 SUBJECT shadow 文档后仍调用关系扩展查询。
- 未指定 `entity_kind` 时，PERSON 与 CHARACTER 的名称候选在名称约束内取并集；与显式 ID/关系字段仍取交集。查询声优关系时必须显式传 `entity_kind=ACTOR`；ACTOR 使用 PERSON shadow 文档，但必须保留 `ACTOR` 的关系解析语义。

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

`streaming.py` 当前会捕获 `on_pending_action` 异常并继续发送结束事件；这是已知安全债务，不得被新代码复制。任何新增或修改必须满足以下契约：

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

### Scenario: Shadow Vector Set 与 MySQL release 发布与回滚

#### 1. Scope / Trigger

- 触发：重建 RAG index version、生成容量/质量报告、切换或回滚 active alias。

#### 2. Signatures

- `ShadowIndexManager.prepare_switch(version, quality_report_path, gate_passed) -> SwitchPlan`。
- `ShadowIndexManager.execute_switch(plan) -> SwitchResult`。
- `ShadowIndexManager.rollback(previous_version) -> SwitchResult`。
- `build_capacity_report(sample_bytes, sample_count, catalog_count, redis_used_memory, available_bytes)`。

#### 3. Contracts

- 新版本写入 `rag:vectors:{entity_kind}:{version}` shadow key 和 `search_document` 行；旧版本在回滚窗口内不得删除。
- 只有五份同一版本报告通过 gate，`execute_switch` 才能调用 MySQL release store 激活版本；Redis 不提供 active alias。
- 容量投影利用率必须不高于 60%；空样本报告必须 `allowed=false`。
- `rollback` 只切回已验证的 MySQL release，不删除任何 Redis Vector Set 或 MySQL 投影。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 报告缺失/版本不一致 | gate fail-closed，拒绝 alias 切换 |
| Vector Set `VADD/VSIM/VREM` 不可用 | 不建向量、不激活 release，保持 RAG 关闭 |
| 容量利用率 > 60% | 报告拒绝发布 |
| alias 切换失败 | 返回失败结果，保留旧 alias |
| 需要回滚 | 指向已验证的旧版本，保留新索引供排查 |

#### 5. Good/Base/Bad Cases

- Good：先写 MySQL/Vector Set 双 shadow → 生成同版本报告 → gate → 在 MySQL 事务中激活 release → 观察后再清理旧版本。
- Base：gate 未通过时只保留 shadow 构建结果，不影响在线旧 alias。
- Bad：直接覆盖 active 版本、只写一侧投影、先删除旧版本，或用 `--activate` 绕过报告。

#### 6. Tests Required

- Shadow 单测断言 gate 未通过拒绝切换、旧 release 保留、rollback 调用正确版本。
- 容量报告单测断言投影、空样本拒绝和 JSON 字段稳定。
- Redis 门禁断言 `COMMAND INFO VADD/VSIM/VREM` 可用后才允许后续灰度；Business 词法响应缺少 `indexVersion` 时拒绝查询。

#### 7. Wrong vs Correct

```text
Wrong: 删除旧 Vector Set 后直接把新 key 当作 active，或让 Agent 自己猜版本。
Correct: 保留旧投影，通过 MySQL `search_index_release` 切换；词法响应携带版本，Agent 查询同版本 Vector Set，异常时回滚 release。

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
```
