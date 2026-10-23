# Agent 编排、运行与流式协议

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [Agent 编排与流式协议](#agent-编排与流式协议)
- [Agent 角色、提示词与流式输出契约](#agent-角色提示词与流式输出契约)

## Agent 编排与流式协议

### 组合与路由

- `backend/agent/main.py` 是组合根，创建 store、配置仓库、Business Gateway、RAG 用例和 LangGraph。
- 领域节点只依赖 `AgentDependencies` 或端口，不读取环境变量、不创建基础设施客户端。
- `app/agent/graph.py` 先按角色分流；普通用户只允许 `search_agent / discover_agent / recommend_agent`。
- `ADMIN` 直接进入 `admin_agent`，其当前工具集不含 RAG；角色工具、Prompt 缓存、语言与日期的完整现状见 [Agent 运行与提示词契约](./agent-guidelines.md#agent-角色提示词与流式输出契约)。
- 每个节点只注册完成职责所需的工具；新增工具先确定最小可见节点。
- `RetrievalQuery` 的 `person_ids`、`character_ids`、`actor_ids`、`relation_subject_ids` 只能通过 Business `/api/client/evidence/resolve` 解析为活跃、非 NSFW 动画 Subject allowlist；解析失败不得访问 Redis 或返回未过滤候选。
- Agent 提示词禁止陈述工具返回中不存在的证据；`app/rag/use_case.py::_compact` 当前输出 20 个键，包含 `airDate`、播出状态、来源、匹配事实和检索解释。字段清单以该函数与 `tests/rag/test_evidence_contract.py` 核对，缺项按字段使用空列表、空字符串或 None；不能用旧字段数量代替契约检查。
- 故障矩阵必须在测试中覆盖：Redis/Embedding/Business/Evidence 每层独立故障与组合故障，证明 fail-closed 或既定降级行为。

> RAG 开关边界、Vector Set 命令门禁、`indexVersion` 唯一版本来源、发布/灰度/回滚历史与 Evidence 权威性均以 [RAG 检索与版本发布契约](./rag-retrieval-contract.md) 为唯一来源，本节不再复制。

#### Scenario: Subject batch 权威边界与 Evidence 过滤顺序

##### 1. Scope / Trigger

- 触发：修改 Agent `RagRetrievalService`、Business `/api/client/subjects/batch` 或 Evidence DTO/VO；尤其是新增 `active`、标签、评分、年份、季度和播出状态过滤。
- 目的：防止把不完整的 batch 响应当成 Evidence 事实，或在 Evidence 补全前错误丢弃候选。

##### 2. Signatures

- `POST /api/client/subjects/batch` 请求：`{ "subjectIds": [1, ...], "excludeCollected": boolean }`。
- batch item 至少包含：`id`, `type`, `nsfw`, `active`；其中 `active` 必须由 `subject.import_status = 1` 派生。
- `POST /api/client/evidence/batch` 返回 `EvidenceCandidateVO[]`，每项必须包含 `subjectId`, `type`, `nsfw`, `active`，以及可选的 `metaTags`, `score`, `ratingTotal`, `airDate` 等事实字段。
- `RagRetrievalService._authoritative_result(...) -> RetrievalResult`：先校验 batch 安全边界，再批量 Evidence 回查，最后执行结构化过滤和重排。

##### 3. Contracts

- batch 阶段只校验 `type=2`、`nsfw=false`、`active=true` 和排除 ID；不得在该阶段读取不存在的 `metaTags`/`airStatus` 字段。
- Evidence 响应必须覆盖候选 ID 的全集；当前实现拒绝缺项、额外 ID、非法 ID、错误类型、NSFW、inactive 和重复合法 ID（整批 fail-closed）。重复 ID 的完整契约与其唯一实现位置见 [RAG 检索与版本发布契约](./rag-retrieval-contract.md#在线装配与当前缺口)。
- `meta_tags`、评分、评分人数、年份、季度和播出状态过滤只能使用 Evidence 字段；Evidence 缺少需要的字段时必须排除候选，不得用 Redis 详情伪造事实。
- 所有外部 `id/subjectId` 必须拒绝布尔值、非数字、非正数和溢出转换；坏行不能抛出未处理异常进入 fallback。

##### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| batch item 缺少 `active` 或 `active != true` | 丢弃该候选；不进入 Evidence/模型上下文 |
| Evidence 超时、错误、部分结果或字段不安全 | `available=false`、`reason=evidence_unavailable` |
| Evidence 过滤后为空 | `available=true`、`reason=no_results`，不扩大查询范围 |
| ID 为布尔值、非正数或不可转换 | 丢弃该行并继续安全处理；不得 500 |
| 无 ACTIVE release 或 Business lexical 缺 `indexVersion` | 词法/混合链 fail-closed，允许既定 Business fallback |

##### 5. Good/Base/Bad Cases

- Good：batch 返回 `active=true`，Evidence 返回完整 `metaTags`，Agent 再执行标签/年份过滤并附证据。
- Base：batch 有候选但 Evidence 缺一项，整个批次不可用，不把其余候选静默送入模型。
- Bad：因为 batch 没有 `metaTags` 就提前过滤，或使用 Redis 的 `air_status` 覆盖 Evidence；把 `subjectId=true` 转成 `1` 更是禁止行为。

##### 6. Tests Required

- Java：batch VO 序列化 `active`；Service 从 `import_status` 映射 active；OpenAPI 与 Controller 测试同步。
- Python：batch `active` 安全边界、Evidence 完整性、Evidence 后结构化过滤、非法 ID fail-closed/不抛异常。
- 运行 `pytest tests/rag tests/jobs/indexer`、`mvn -B clean test`，并对真实 shadow 报告断言 `evidenceCompleteness=1.0`。

##### 7. Wrong vs Correct

##### Wrong

```python
if not detail.get("metaTags"):
    continue  # batch 没有该字段，错误地把合法候选过滤掉
subject_id = int(row.get("subjectId"))  # True 会被转换成 1
```

##### Correct

```python
if detail.get("active") is not True:
    continue
safe, ok = self._enrich_evidence(candidates, token, evidence_lookup)
if not ok:
    return RetrievalResult(available=False, items=[], reason="evidence_unavailable")
safe = [item for item in safe if self._matches_query_filters(item.evidence or {}, query)]
```

### RAG 结构化实体筛选契约

#### 1. Scope / Trigger

- Trigger：RAG 工具新增人物、角色、声优和关联条目 ID 过滤，并跨 Agent → Business → MySQL 传递实体关系。

#### 2. Signatures

- `RetrievalQuery`: `person_ids`, `character_ids`, `actor_ids`, `relation_subject_ids` 均为最多 50 个正整数。
- `POST /api/client/evidence/resolve`: `{ "entityType": "PERSON|CHARACTER|ACTOR|SUBJECT|RELATION_SUBJECT", "ids": [1, ...] }`；`RELATION_SUBJECT` 沿 `subject_relation` 双向扩展。
- `BusinessGateway.resolve_evidence(entity_type, entity_ids, *, token) -> dict | list | None`（无结果时返回 None）。
- `plan_retrieval_query(query) -> RetrievalQuery` 只补全带明确标记的中文年份、季度、播出状态、评分和评分人数；显式结构化字段优先。

#### 3. Contracts

- Business 只返回 `type=2`、`nsfw=false`、`active=true` 的证据候选；Agent 仅提取 `subjectId`。
- 多种实体过滤取交集；allowlist 同时约束 Redis 召回和 Business fallback，再执行 Subject 权威回查与 Evidence 回查。
- 实体 ID 不得拼接进 Vector Set `FILTER` 或 SQL 字符串。

#### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| ID 非正整数、超过 50 个 | Pydantic 校验失败，工具返回空结果 |
| `/resolve` 超时、错误、异常或返回缺失/不安全字段 | `available=false`、`reason=entity_resolution_unavailable` |
| `/resolve` 返回空集合 | `available=true`、`reason=no_results`，不得扩大查询范围 |
| Redis 故障 | Business fallback 仍应用同一 allowlist |

#### 5. Good/Base/Bad Cases

- Good：`person_ids=[7]` 解析出 Subject 42，Redis 返回 41/42 时只回查 42。
- Base：没有实体过滤时保持旧检索路径和 Business fallback。
- Bad：把 `person_ids` 作为 `@person_id:{7}` 拼入 Subject 索引，或解析失败后继续返回 Redis 候选。

#### 6. Tests Required

- Schema：严格拒绝字符串、布尔值、非正数和第 51 个 ID。
- Retrieval：实体解析调用顺序、交集、空集合、异常 fail-closed、Redis 故障 fallback allowlist。
- Planner：明确条件提取、显式字段优先，以及不明确/越界提示保留在原始语义查询。
- Adapter：断言 `/api/client/evidence/resolve` 方法、路径、JSON body 和 Authorization，以及 malformed response。

#### 7. Wrong vs Correct

##### Wrong

```python
expression = f"@subject_id:{{{query.person_ids[0]}}}"
```

##### Correct

```python
allowed = resolve_evidence("PERSON", query.person_ids, token=token)
candidates = [item for item in candidates if item.subject_id in allowed_subject_ids]
```

### Scenario: Agent SSE 事件契约

#### 1. Scope / Trigger

- Trigger：任何新增/修改 `/api/client/agent/stream`、`/api/admin/agent/chat/stream` 的事件字段、帧格式或结束语义。这是 Python 生产方 → Spring 透传 → 浏览器消费方的跨层契约，改动会同时影响 `app/api/schemas/sse.py`、`app/api/sse.py` 与前端 `useAgentChat.ts`。

#### 2. Signatures

- 序列化单一入口：`app/api/sse.py`；结束事件必须设置 `is_end=true`。
- **两层枚举，别搞混**：内部事件 `AgentEvent` / `AgentEventType` 定义在 `app/chat/events.py`（**五值**，含 `END`）；wire 侧 `AssistantResponse` / `MessageType` 定义在 `app/api/schemas/sse.py`（**四值**，无 `end`）。`app/api/sse.py:10-11` 把 `AgentEventType.END` 显式转成 `is_end=true` 后再转成 `MessageType.ANSWER`，即内部五值 → wire 四值的唯一收敛点。
- 传输路径：浏览器只请求 Spring 代理路径（`/api/{client,admin}/agent/...`），不配置或直连 Agent 的 `:8090`。
- **wire 帧格式（不得凭 spec 文字推断）**：每帧只有 `data:` 行、`\n\n` 分帧、类型在 JSON 内部的 `type` 字段；不使用 `event:` / `id:` / `retry:` 行。

#### 3. Contracts

- 响应头保持 `Content-Type: text/event-stream`、`Cache-Control: no-cache`、`X-Accel-Buffering: no`。
- `MessageType` 只有 `answer / thinking / function_call / status` —— **不存在 `end` 类型**。内部 `AgentEventType` 多一个 `END`，但它不会出现在 wire 上。
- 结束帧为 `type="answer"`（默认值）+ `is_end=true` + 空 `content`。
- `exclude_none=True` 使每帧字段集随事件类型变化；前端因此必须把 `content` 子字段视为可选。`meta={}` 会保留，`meta=None` 被剔除。
- 改事件字段时必须同时看两个文件：内部结构改 `app/chat/events.py`，wire 结构改 `app/api/schemas/sse.py`，并同步前端 `useAgentChat.ts`。`docs/spec/openapi.yaml` 的 `/api/client/agent/stream` 已声明 `text/event-stream` 与单帧 `SSEFrame` schema，但事件内容字段的语义仍以源码为准；本节口径由 `backend/agent/tests/contracts/test_sse_contract.py` 自动钉住（详见 [Agent↔Business 契约测试](./contract-tests.md#3-contracts)）。

#### 4. Validation & Error Matrix

| 情况 | 契约行为 |
|---|---|
| 正常增量 | 逐帧 `data:` + `\n\n`，`is_end=false` |
| 结束 | `type="answer"` + `is_end=true` + 空 `content`；消费方据此停止写入 |
| 工具开始/结束 | `function_call` 帧，`state=start|end` |
| 工具失败 | `function_call` `state=end` + `result=error`（**不是** `state=error`） |
| 执行异常（回答落库 / PendingAction 持久化） | 发送 `status` 错误事件后结束流；客户端视为可重试的部分失败，不显示为保存成功 |
| 客户端断开 | 现在只是**退订**：run 继续跑完并落库，流不产生错误帧（详见下节 Run 生命周期） |
| 字段缺失 | 因 `exclude_none`，消费方不得假设字段恒存在 |

#### 5. Good / Base / Bad Cases

- Good：新增事件字段时同步 `app/chat/events.py`（内部）、`app/api/schemas/sse.py`（wire）、`app/api/sse.py`（序列化）与前端 `useAgentChat.ts`，并补帧格式回归。
- Base：只改内部实现，不动 wire 契约。
- Bad：在 spec 或任务描述里写「五值联合（含 end）」，或在 JSON 外新增 `event:` 行。

#### 6. Tests Required

- `tests/api/test_sse_serialization.py` 钉住帧形态、`exclude_none`、`end` 语义、响应头与逐帧消费（当前回归入口）。
- 新增/修改事件字段时同步断言 `AgentEventType` 与 `MessageType` 两侧取值，以及结束帧形态。
- 枚举一致性是**通过契约 enum 传递**的：`test_all_serializable_event_types_are_covered` 断言 `AgentEventType`（去 END）等于契约 enum，`test_message_type_matches_agent_event_type` 断言 `MessageType` 也等于该 enum，故两者必然相等（注意后者的 docstring 写作「与 AgentEventType 同步」，但它实际比的是契约 enum）。
- 契约侧对齐由 `backend/agent/tests/contracts/test_sse_contract.py` 负责（四值枚举、`content` 子字段集、单帧 `SSEFrame`、错误语义分离、唯一 `is_end` 收尾）；两侧必须同时绿，见 [契约测试](./contract-tests.md#6-tests-required)。

#### 7. Wrong vs Correct

- Wrong：把 `end` 当作 `type` 枚举值（旧 spec 文字曾如此表述）；或假设每个帧都带 `content` 子字段。
- Correct：类型枚举只有四值，结束由 `is_end=true` 表达；消费方把 `content` 子字段视为可选。实现以 `app/api/sse.py:10-11` 为准，spec 文字与之冲突时以代码为权威。

### Scenario: Chat run 生命周期与重连

#### 1. Scope / Trigger

- Trigger：任何改动「一次对话生成」的生命周期——`app/chat/runs.py`、`app/chat/service.py` 的 `start_run` / `stream_chat`、`app/api/chat.py` 的 `/stream` 与 `/runs/*` 路由、`app/adapters/redis/run_state.py`。
- 背景：2026-10-22 之前，落库回调位于 SSE 消费循环之后；客户端刷新触发 `GeneratorExit` 时整段跳过，已上屏的回答从未落库。根因是**收尾职责与读者绑定**。

#### 2. Signatures

- 一次生成 = 一个 `ChatRun`，由 `ChatRunManager` 持有，驱动体是本进程内一个 `asyncio.Task`。
- SSE 响应只是 run 的**订阅者**：`subscribe(after)` 先回放缓冲再推增量，退订只从 `run.subscribers` 摘队。
- `POST /stream` 首帧带 `meta.run_id`；`GET /runs/{run_id}/stream?after=N` 重连同一 run；`GET /sessions/{session_id}/run` 查该会话当前/最近 run；`POST /runs/{run_id}/stop` 主动停止。

#### 3. Contracts

- **断连 ≠ 取消**：客户端断开只退订，run 继续跑到自然结束并落库。只有进程关闭才 `cancel()`。
- **落库单一责任人**：持久化只在 `ChatRunManager._drive` 的 `finally` 执行（`on_answer_completed` / `on_pending_action`）。`stream_agent_events` 是纯事件生产者，不调任何回调。
- **每 run 恰好一条 assistant 消息**：有内容则落内容；非 `DONE`（失败/被 stop）且无内容则落 `*（生成已中断）*`；`DONE` 且无内容不落（不留空消息噪声）。
- **恰好一个 `is_end` 帧且位于末尾**：由 `_finish` 统一合成，覆盖异常、落库失败、被 stop 三条路径。
- **`stop` 是逻辑停止**：标记 `cancelled` + 合成未闭合工具的 `state=end, result=aborted` 帧 + END 帧，立即返回 200；**不 cancel 底层 task**（节点是同步闭包，跑在 LangGraph executor 里，cancel 只能落在节点边界）。底层跑完后落库部分答案并跳过 `pending_action`。
- **封存**：`stop` 之后产出的事件不再进缓冲、不再广播（但仍聚合答案以便落库）。
- **同会话并发**：已有 `status=running` 的 run → `POST /stream` 返回 409，body 形如 `{"detail": {"active_run_id": ..., "status": "running", "capabilities": ["interrupt"]}}`。`cancelled` 不算 active。消息顺序由 per-session `persist_future` 保证（新 run 落 user 消息前最多等 5s，超时降级）。
- **归属校验**：`/runs/*` 与 `/sessions/*` 的 run 查询必须校验 `user_id` / 会话归属，不符一律 404，不暴露存在性。
- **重启边界（任何重连设计都必须写明）**：run 的执行状态**不跨进程持久化**。`agent:run:{run_id}`（TTL 900s）与 `agent:session_runs:{session_id}` 只是状态投影；读到投影为 `running` 但内存无此 run → 懒收敛为 `failed`。重启后不会「接着跑」，也不会自动补写回答——用户看到的只能是历史里已有的内容。

#### 4. Validation & Error Matrix

| 情况 | 行为 |
|---|---|
| 客户端刷新（断连） | 退订；run 继续；答案落库；无错误帧 |
| 用户主动停止 | 立即 200 + 工具终态帧 + END；底层跑完后落库带 `*（生成已中断）*` 前缀的部分答案；不落 `pending_action` |
| 落库失败 | 发 `status`/`error` 帧（`meta.persistence` 标明是 answer 还是 pending_action），END 仍最后且唯一 |
| 同会话已有 running run | `POST /stream` → 409 |
| 投影为 running 但内存无此 run | 收敛为 `failed`；不补写消息（历史里是什么就是什么） |
| 他人 run_id | 404 |

#### 5. Good / Base / Bad Cases

- Good：把「生成」与「推送」分开思考——生成是 run 的职责，推送是订阅者的职责。
- Base：只改 `_drive` 的落库细节，不动 run 边界。
- Bad：把落库挪回 SSE 响应体、在 `subscribe` 里 cancel run、或在断连时合成工具终态帧（那会让「还在跑的工具」被前端误判为中断）。

#### 6. Tests Required

- `tests/agent/test_chat_run_manager.py`：断连不取消、stop 立即返回、工具终态、封存、`pending_action`、游标回放、`persist_future`、投影与懒收敛。
- `tests/agent/test_run_side_effects.py`：四项副作用（孤立 user 消息三态、工具中间态、断连不合成终态、退订摘队列、`shutdown` 取消与超时上限）。
- `tests/agent/test_run_disconnect.py`：AC1 直接回归（断连后答案落库）。
- `tests/api/test_run_api.py`：`run_id` 注入、409、归属 404、回放唯一 `is_end`、stop 幂等。
- `tests/adapters/redis/test_run_state.py`：投影读写与 TTL。

#### 7. Wrong vs Correct

- Wrong：把 `POST /runs/{id}/stop` 实现成 `task.cancel()` 并等它停——同步节点不会响应，调用会挂住或只有表面效果；也不要指望「停」之后再去补写答案。
- Correct：`stop` 只标记状态、合成终态帧、立即返回；落库等 run 自然跑完在 `finally` 里做。
- Wrong：用 `asyncio.wait_for(gather(...), timeout=...)` 做关闭超时——超时会二次 cancel 并等取消完成，遇到对 cancel 免疫的任务则无上限挂住（保护变陷阱）。
- Correct：`asyncio.wait(tasks, timeout=...)`，超时只记日志。

### Gateway 路由结果解析

- `gateway.py::_resolve_routing_result` 是结构化路由结果的唯一解析入口；`route_target` 必须属于 `("search_agent", "discover_agent", "recommend_agent")`，否则**抛错而非静默回退默认路由**——路由错误会导致幻觉工具调用。
- 解析顺序（`tests/agent/test_gateway_routing_result.py` 逐条钉住）：非 mapping 载荷 → `messages` 空 → 末条 content 空 → JSON 非法 → JSON 非对象 → `route_target` 缺失/非法。全部路径均 `ValueError`；JSON 为标量/数组（`"x"`/`123`/`true`/`["a"]`）归入「`route_target` 缺失」而非 `AttributeError`。
- `extract_text`（`runtime.py:27`）统一处理「字符串 content」与「content 块列表」两种模型返回形态；无 `text` 项时返回空串。

### Business 响应守卫

- `HttpBusinessGateway.request` 返回类型为 `dict | list | None`：Java 成功响应缺 `data` 时**显式 `return None`**（`business_http.py:68`）。
- 消费方一律以 `if isinstance(data, dict) and data.get("error")` 守卫，**不得裸调 `response.get(...)`**。既有守卫见 `app/agent/client/actions/collection_state.py:24`、`actions/collection_type.py:141`、`actions/subject_resolution.py`（5 处）、`actions/wishlist.py:107`、`actions/collection_progress.py:44,65`，以及 `app/agent/client/collections.py:76`（唯一不在 `actions/` 子目录的消费方）。

### 安全写操作

> 本节已拆为独立文件：[Agent 安全写操作契约](./write-operations.md)。包含预览→确认→执行协议、`write_guard` 硬门禁、`PendingAction` 三种变体差异、持久化失败矩阵与 SUBJECT_RESOLUTION 选择状态。新增或修改任何写链路前必须先读该文件。

### 认证与配置

- Agent 使用共享 `JWT_SECRET` 本地 HS256 验签，避免回调 Spring 形成代理环路。
- 管理路由必须使用 `require_admin`，不能只靠提示词限制。
- `Settings` 使用 `extra="forbid"`；新增环境变量同步 `app/config.py` 与 `.env.example`。
- `LLM_PROVIDER` 支持 `deepseek|dashscope`；显式设置时缺少对应 Key 必须失败。未设置时当前实现会按 DeepSeek→DashScope Key 存在性回退并记录 warning，不得把“显式选择”写成必需事实。
**对话模型只有 DeepSeek 一家**（2026-10-19 起）：`langchain-deepseek` 的 `ChatDeepSeek`，走官方 OpenAI 兼容端点。

- **阿里云百炼已退出对话链路**：`DASHSCOPE_API_KEY` 保留但**仅用于 RAG 嵌入**（`DashScopeEmbeddingClient` / `text-embedding-v4`）。`DASHSCOPE_MODEL`、`DASHSCOPE_MODEL_ROUTE`、`DASHSCOPE_BASE_URL`、`LLM_THINKING_BUDGET` 与 `thinkingBudget` 管理字段均已删除，**不得恢复**。
- `LLM_PROVIDER` 只接受 `deepseek`。设成 `dashscope`（或任何其它值）**必须报错**，不得静默回退到 DeepSeek——静默回退会让人以为切到了百炼却在跑 DeepSeek。
- 历史：`ChatTongyi` 曾随 `langchain-community` sunset（2026-05-26 归档）迁到百炼 OpenAI 兼容端点，随后百炼对话模型整体移除。官方从未有通义千问 partner 包（`langchain-tongyi` PyPI 404；`langchain-dashscope` 停更 2024-07；`langchain-qwq` 为个人包），故**不得**为“加回第二家”而引入 `langchain-community` 或第三方 Qwen 包。
- **DeepSeek 的字段形态是契约、不是 bug**：
  - `max_tokens` 仍用**旧字段名**发给 DeepSeek。这与百炼相反（百炼 2026-04-20 起用 `max_completion_tokens`）；若将来加回一家用新名的供应商，**不得**把两家统一成同一个键。
  - 思考经 `extra_body={"thinking": {"type": "enabled"}}` 开启，强度走 `reasoning_effort`（`low`/`high`/`max`）。不要套用 qwen3 的 `enable_thinking`/`thinking_budget`——那不是 DeepSeek 的参数。
- `reasoning_content` **不需要项目侧补丁**：`ChatDeepSeek._convert_chunk_to_generation_chunk` 自己写入 `additional_kwargs`，`runtime._extract_reasoning_content_from_chunk` 读取。此前的 `_patch_chat_openai_reasoning` 打的是 `_convert_delta_to_message_chunk`，而 `ChatDeepSeek` 从不经过该路径——它是 dead code，已随百炼分支一并删除。回归见 `tests/adapters/test_llm_factory.py::TestReasoningCapture`。
- LLM 模型/温度等运行时配置优先读取 Redis `agent:config:model`；本地缓存约 5 秒，Redis 不可用时回退环境配置。
- 托管 Prompt 在启动时从 Redis 建立快照；单项读取失败回退仓库内本地 Prompt，不因 Prompt Redis 不可用阻止启动。
- 共享 `.env` 中由 importer 使用的字段也必须声明在 `Settings` 中，否则 `extra="forbid"` 会导致启动失败；业务读取仍需说明真实来源。
- 日志只记录供应商和模型名，绝不记录 Key、JWT、用户输入或完整回答。

#### 健康检查语义

- Agent `/api/client/agent/health` 已实现分项探测（2026-09-21）：`checks` 覆盖 `llm`/`redis`/`business`/`rag`，取值为有限枚举 `ok`/`down`/`disabled`；`RAG_ENABLED=false` 报 `disabled` 而非 `down`。仍**恒返回 HTTP 200**，降级在 body 表达（见 `error-handling.md` 的例外登记）。MinIO 仍不探测——它是 importer 离线依赖，`app/` 零网络调用。
- 探测**真实触网**且**不短路**：Redis 执行 `PING`、Business 发起 `GET /actuator/health/liveness`（**非**默认 `/actuator/health`，后者聚合 Business 自身 MySQL/Redis，会错误归因）、RAG 执行 `COMMAND INFO VADD/VSIM/VREM`（经 `probe_vector_set_commands`，不依赖 `index_version`）。仅 `llm` 分项是纯配置判定。各项 2s、总预算 3s，超时判 `down`。
- Business 的 liveness/readiness 配置见 `backend/business/app/src/main/resources/application.yml`；readiness 检查 MySQL 与 Redis，Security 只匿名放行 `/actuator/health` 与 `/actuator/health/**`，其他未显式允许的 URL 仍拒绝；修改健康探针时必须补授权测试。
- 授权为**两层有意不一致**（不得当作缺陷「修复」）：经 Spring 代理的浏览器路径由 `ClientAgentController` 必填 `Authorization` + `SecurityConfig` 的 `/api/client/**` `.authenticated()` 强制登录；直连 Agent `:8090` 的 Python 侧匿名。`tests/api/test_health.py::test_health_is_anonymous` 钉住该行为。
- 变更健康检查时必须明确：检查项、HTTP 状态、依赖不可用时的响应、公开字段和是否允许匿名访问。

#### Scenario: 管理端模型配置回显与稀疏保存（2026-10-14）

##### 1. Scope / Trigger

- Trigger：`GET /api/admin/agent/config` 原先直接返回 Redis 原始内容（`get() or {}`）。Redis 空时返回 `{}`，
  管理页表单全空，管理员看不到 `.env` 里实际生效的值。
- 关键风险：`RedisModelConfigRepository.set()` 是 `SET` 整体替换。若把「继承的默认值」填进表单再保存，
  默认值会被固化进 Redis，此后改 `.env` **不再生效**（工厂侧 `or` / `runtime.get(k, default)` 会让 Redis 值永久压过 Settings）。
- 故：**回显生效值 + 标注逐字段来源**，且**保存只写显式覆盖的字段**。两者不可分离。

##### 2. Signatures

- `GET /api/admin/agent/config` → `ModelConfigView`（5 个配置字段 + `_sources`）
- `POST /api/admin/agent/config/update` body: `ModelConfig`（**无** `_sources`）→ `ModelConfigView`
- `AdminConfigService(model_configs, prompts, settings)` — 构造签名含 `settings`；唯一构造点 `main.py` lifespan
- `AdminConfigService.get_effective_config() -> dict`

##### 3. Contracts

| 字段 | 类型 | 来源 |
|---|---|---|
| `model` | `str` | `resolve_llm_provider(settings).model` |
| `modelRoute` | `str` | `resolve_llm_provider(settings).route_model` |
| `temperature` | `float` | `settings.llm_temperature` |
| `maxTokens` | `int` | `settings.llm_max_tokens` |
| `reasoningEffort` | `str` | `resolve_llm_provider(settings).reasoning_effort` |
| `_sources` | `Record<field, "default" \| "override">` | 只读派生；GET 响应专有 |

- 线上键名 `_sources` 由 `Field(alias="_sources")` 产生。FastAPI 响应路径默认 `by_alias=True`，
  实测 `TestClient` 返回体即为 `_sources`；**无需**再加 `serialization_alias`（重复且易误导）。
- 请求侧仍是 `ModelConfig`：`_sources` 是只读派生信息，不进入入参。
- 空对象 `{}` 提交 = **没有修改**（service 直接返回现值、不写存储），不是「全部回退」。

##### 4. Validation & Error Matrix

| 条件 | 行为 |
|---|---|
| `temperature` 不在 `[0,2]` | `ValueError` → HTTP 400 |
| `maxTokens <= 0` | `ValueError` → HTTP 400 |
| 提交体为空 `{}` | 不写存储，返回现值（no-op） |
| `model`/`modelRoute` 为空串 | 视为未设置，回退 Settings，标 `default` |
| 数值字段值为 `0` | **合法覆盖**，不得当作未设置（`temperature=0`） |
| 提交体缺少某字段 | 整体替换后该键消失 → 回退继承默认（即「清空字段 = 撤销覆盖」） |

##### 5. Good/Base/Bad Cases

- Good：Redis 空 → 5 字段均为 `.env` 值 + `_sources` 全 `default`；页面留空并以 placeholder 显示继承值。
- Base：仅 `{"temperature":0.9}` 覆盖 → 该字段 `override`，其余 `default`。
- Bad：GET 返回的生效值直接填进表单 value 并整体提交 → `.env` 默认值被固化进 Redis，`.env` 变更静默失效。

##### 6. Tests Required

`backend/agent/tests/admin/test_config_service.py`（13 例，钉住断言点）：

- Redis 空 → 全 `default` 且值等于 Settings（AC1）
- 局部覆盖 → 仅该字段 `override`（AC2）
- `temperature=0` → 保留且标 `override`（边界，防误判未设置）
- 空串 `model` → 回退默认（与工厂 `or` 语义对齐）
- 改 Settings（`llm_temperature`/`llm_max_tokens`）→ 回显随之变化（AC3，证明值来自 Settings 非常量）
- 稀疏提交 → `repo.set_calls == [{"model":"custom-x"}]`，其余仍 `default`（AC4）
- 空提交 → `set_calls == []` 且既有覆盖保留（D2 no-op）
- 越界 `temperature` / `maxTokens<=0` → `ValueError` 且未写存储

前端 `frontend/admin/src/pages/AgentConfig.test.tsx`：default 留空 + placeholder、override 填值、override 的 `0` 值、
稀疏提交（含空对象、清空撤销、数值类型、越界拦截）。

##### 7. Wrong vs Correct

###### Wrong

```python
# 用 GET 的"生效值"打底再覆盖表单字段 —— 会把 .env 默认值整体写回 Redis
saveCfg.mutate({ ...serverCfg, temperature: 0.9 })
```

###### Correct

```python
# 只提交被显式填写的字段；未填字段不进提交体 → 整体替换后该键消失 → 回退继承
saveCfg.mutate(toSparseBody(cfg))   # -> {"temperature": 0.9}
```

> **Warning**：回显值必须与 `agent_factory.AgentLlmFactory.create()` 的解析链**逐字对齐**，否则管理页显示的值
> 与运行时实际使用的值会分叉。两类语义不可互换：`model`/`modelRoute` 走 `or`（空串 = 未设置），
> 其余看键是否存在（`0` 是合法值）。

### 离线任务

> 本节已拆为独立文件：[Agent 离线任务契约](./offline-jobs.md)。覆盖 importer / indexer / backfill / scheduler 的幂等、锁、重试与错误分类。在线链路改动无需读它；改离线任务时必须读。

## Agent 角色、提示词与流式输出契约

源码核对：2026-09-12。适用于能力自述、中文输出、日期工具、Prompt 热更新及聊天 SSE 排障。

### 角色与工具是能力判断的依据

入口由 `backend/agent/app/agent/graph.py::_route_from_entry` 读取 `state.user.role` 决定。`ADMIN` 直接进入 `admin_agent`，普通用户经过 `gateway_router` 进入三个客户端节点。页面名称不决定节点；必须核对 JWT 角色、服务端 state 和实际注册工具。

| 节点 | 当前注册的主要能力 | 源码（相对 backend/agent） |
|---|---|---|
| search_agent | rag_search_subjects、详情、剧集、收藏读取、当前时间 | `app/agent/client/search.py` |
| discover_agent | rag_discover_subjects、日程、收藏读取、当前时间 | `app/agent/client/discover.py` |
| recommend_agent | rag_recommend_subjects、收藏读取、待确认收藏/进度动作、当前时间 | `app/agent/client/recommend.py` |
| admin_agent | 目录只读工具、recent 导入、当前时间；未注册 rag_* | `app/agent/admin/tools.py` |

客户端始终注册对应 `rag_*` 工具；`main.py::_build_agent_dependencies` 在 `RAG_ENABLED=false` 时注入不可用索引/Embedding 与 Business fallback。工具名称、功能开关、索引 ACTIVE 和本次实际召回路径是四种不同事实。

当前图没有 `capability_agent` 或对 RAG 能力问题的确定性响应。客户端提示词规定依据工具回答能力问题，但管理员提示词只描述目录查询与导入，不能把客户端 RAG 自述规则当成所有角色的已实现功能。新增工具应在对应节点显式注册，禁止仅改提示词宣称具备能力。

### Prompt 与模型配置的加载时序

1. `app/adapters/redis/prompt_repository.py::initialize_snapshot` 启动时读取 `agent:prompt:{key}` 的 JSON `promptContent`，建立进程内快照。
2. `get` 优先读快照，缺失时读本地文件。直接修改 Redis 不会自动更新已运行进程；`set/reset` 会刷新当前仓储实例，其他 worker 仍需刷新或重启。
3. `app/adapters/prompts/file_prompt.py::load_prompt` 有 `_PROMPT_CACHE`。本地 Markdown 修改也不保证已运行实例立即生效；`reset` 删除托管项不等于清空文件缓存。
4. `app/agent/run.py::run_domain_agent` 取 Prompt 并按需追加 PendingAction，再传入 `SystemMessage`；没有统一语言过滤层。
5. 模型配置使用另一套 `app/adapters/redis/model_config_repository.py` 短缓存，不能套用 Prompt 快照规则。供应商与模型参数装配见 `app/adapters/llm/agent_factory.py`。

排障依次核对实际服务地址/进程、用户角色、节点、Prompt 来源、进程内快照与模型配置。只检查磁盘文件或当前 shell 环境，不能证明另一运行进程加载了同样配置。不得把连接检查未返回结果直接判定为服务不存在。

### 中文与 thinking 的实际边界

客户端三个领域 Prompt 明确要求简体中文思考与回答；gateway 也有中文指令。`resources/prompt/admin/admin_agent_prompt.md` 只要求简体中文回答风格，没有同样的内部 reasoning 指令。Prompt 属于模型指令，不是确定性语言校验。

当前链路：`agent_factory.py` 捕获供应商 reasoning → `runtime.py::_extract_reasoning_content_from_chunk` → `run.py` 回调 → `app/chat/event_sink.py` → `app/chat/streaming.py` → 前端。

当前行为与限制：

- `runtime.py` 保留非空 reasoning chunk 的原始首尾空格，只丢弃空块和规范化后完全重复的 payload；不能据此断定模型原始输出一定为中文。
- 没有英文检测、中文翻译或中文状态替换；不得宣称 SSE 保证只输出中文。
- `agent_stream` 一旦收到正文就置 `is_answering=true`，后续 reasoning 不再输出；多个模型轮次的正文会串接，可能同时包含工具前说明和最终回答。
- `ChatService` 保存回答与工具名；前端加载历史仅恢复 role/content，不恢复 thinking。
- 若未来用固定状态替代原始 reasoning，应标为处理状态，不得伪称模型已经用中文思考。

### 日期、日程与状态

`app/agent/time_tool.py` 返回 Asia/Shanghai 当前时间；缺少系统时区库时回退固定 UTC+8。Gateway Prompt 注入当日日期，领域节点依赖 `get_current_time` 工具，当前没有代码强制“先取时间再查日程”。历史回答日期不能作为今天的事实。

推荐契约：今天/本周/本季请求使用当前时间工具结果生成条件；日程约定 `weekday=0` 为周日、`-1` 为全部。不要直接把 Python `weekday()`（周一为 0）作为 Business 参数。

季度映射已跨层对齐（唯一词表 `app/rag/seasons.py`，回归锚 `tests/rag/test_season_alignment.py`）；播出状态推断仍有跨层差异，详见 [RAG 检索契约](./rag-retrieval-contract.md)。日程、评分和主创描述必须来自本次权威工具结果；工具可调用并不能证明模型已使用正确日期。

### 验证与当前测试缺口

- `tests/agent/test_client_prompt_contract.py` 仅验证三个本地 Prompt 包含指定文字；不验证管理员、Redis 覆盖、模型遵循程度或 SSE 展示。
- `tests/agent/test_capability_route.py` 当前按 entry/gateway/runtime 契约验证角色路由、显式动作、确认词和 reasoning 空格；Prompt 字符串测试仍不代表模型一定遵循指令。
- `stream_agent_events` 的兜底文本与正常增量共用聚合缓冲区；答案或待确认动作持久化失败会记录异常并发出 `status` 错误事件，随后安全发送 `end`。真实 Redis/Business 故障与模型回放仍需单独验证。
