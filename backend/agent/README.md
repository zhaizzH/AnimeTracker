# AnimeTracker Agent

> **一句话定位**：基于 FastAPI + LangGraph 构建的 AI 对话 Agent（v3.0.0），面向番剧场景提供搜索、发现、推荐三类对话能力，通过受控工具调用后端业务 API 获取实时数据，经 SSE 流式输出，并对写操作强制「预览 → 确认 → 执行」。

> 上级文档：[后端总览](../README.md) · [项目总览](../../README.md)

## 适用场景

- 为 AnimeTracker 用户端提供自然语言番剧搜索、内容发现与个性化推荐。
- 为管理端提供独立的 Agent 对话（可触发最近新番导入）。
- 承载托管提示词与运行时模型配置的管理接口（Redis 优先、本地文件回退）。
- 运行离线任务：Bangumi 数据导入、RAG 向量索引构建、定时调度（见 `jobs/`）。

不适合直接暴露给公网：本服务假定由 business 的代理层转发，自身只做本地 JWT 验签。

- **默认端口**：`8090`（Swagger 文档：`/docs`）
- **LLM**：DeepSeek 官方直连或 DashScope 百炼 Qwen，由 `LLM_PROVIDER` 显式指定
- **存储**：Redis（会话 / 消息、托管提示词、运行时模型配置、待确认动作、RAG 索引）

## 前置依赖

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10 及以上 | `pyproject.toml` 声明 `requires-python = ">=3.10"` |
| uv | 最新版 | 依赖由 `uv.lock` 锁定，CI 使用 `astral-sh/setup-uv@v5` |
| Redis | 5+ 协议兼容 | 必需；不可用时服务仍启动，但会话功能不可用 |
| MySQL | 8 | 仅 `jobs/importer`、`jobs/indexer` 需要 |
| MinIO | 任意近期版本 | 仅 `jobs/importer` 转存封面与原始快照需要 |
| Spring Boot business | :8080 | 工具回查目标；不启动时所有业务工具调用失败 |
| LLM API Key | — | `DEEPSEEK_API_KEY` 或 `DASHSCOPE_API_KEY` 至少一个 |

## 架构定位

本服务是真正的**大模型推理层**。业务后端 [`../business`](../business/README.md) 内置 `agent` 代理模块（Maven 模块 `animetracker-agent`），在 `8080` 端口对外暴露 `/api/client/agent/*`（用户端）与 `/api/admin/agent/*`（管理端），并将请求转发到本服务：

```
前端 (5173) ──/api/client/agent/*──► business :8080 (agent 代理层) ──HTTP 转发──► 本服务 :8090
                                                                          │
                                                                          └─工具调用─► business API（获取番剧实时数据）
```

- 前端不直接访问 `8090`；所有 Agent 流量经 Vite 代理统一走 `8080` 的 `/api` 前缀。
- 本服务通过 `BACKEND_BASE_URL`（默认 `http://localhost:8080`）回查业务 API。
- 本服务与 business 共享 `JWT_SECRET`，在本地验签，不回调业务后端。

## 架构：单张 StateGraph

Agent 以一张 LangGraph 状态图（`app/agent/graph.py`）驱动，节点内部用 LangChain agent 执行，并经 ContextVar 事件总线把增量事件流式输出给前端：

```
                 ┌──────────────┐
                 │ entry_router │  条件入口：按角色分发
                 └──────┬───────┘
         ┌──────────────┴──────────────┐
         ▼                             ▼
   ┌──────────────┐             ┌────────────┐
   │gateway_router│             │admin_agent │  管理端 Agent（含导入工具）
   └──────┬───────┘             └────────────┘
   ┌──────┴────────────────┬────────────────┐
   ▼                       ▼                ▼
search_agent        discover_agent    recommend_agent
   │                       │                │
   └───────────────────────┴────────────────┘
                           ▼
                          END
```

### 流程

1. `entry_router` 按角色分发（`app/agent/graph.py` 的 `_route_from_entry`）：`ADMIN` → `admin_agent`；其余 → `gateway_router`。
2. `gateway_router` 用结构化路由把用户问题路由到 `search_agent` / `discover_agent` / `recommend_agent`，写入 `state["routing"]["route_target"]`。
3. `_route_from_gateway` 校验 `route_target` 必须属于白名单，否则直接抛 `ValueError`——路由结果不信任模型自由输出。
4. 三个 domain 节点统一走 `run_domain_agent`（`app/agent/run.py`）共享管道：绑定各自工具与系统提示词，消费模型增量——思考增量走 `thinking`，回答增量走 `answer`，工具调用经中间件发 `function_call` 事件。
5. `app/chat/streaming.py` 消费图事件 + 总线事件，产出 SSE。
6. `admin_agent` 是独立的终端节点，持有导入类工具，不参与用户端三域路由。

## 目录结构

```
backend/agent/
├── main.py                  # FastAPI 入口：lifespan 初始化 Redis + 提示词快照 + 图，注册 4 组路由
├── pyproject.toml           # 依赖与 pytest 配置（uv 管理）
├── uv.lock
├── .env.example             # 配置模板（Agent 与 jobs 共用）
├── tests/                   # pytest 测试（当前覆盖 jobs/importer 的指标计算）
├── resources/prompt/        # 本地托管提示词（Redis 未命中时的回退）
│   ├── client/              # gateway / search / discover / recommend
│   └── admin/               # admin_agent
├── jobs/                    # 离线任务（与 Agent 共用 venv 与 .env）
│   ├── importer/            # Bangumi 数据导入 CLI
│   ├── indexer/             # RAG 向量索引构建
│   └── scheduler/           # 定时导入调度（Asia/Shanghai）
└── app/
    ├── config.py            # pydantic-settings 配置 + resolve_llm_provider
    ├── api/                 # HTTP 层
    │   ├── chat.py          # create_chat_router()：用户端 / 管理端会话与流式对话
    │   ├── admin_config.py  # /api/admin/agent 提示词与模型配置；require_admin 鉴权
    │   ├── import_api.py    # /api/admin/agent/import/run 触发导入
    │   ├── deps.py          # verify_token：本地 JWT 验签（共享业务后端密钥）
    │   ├── sse.py           # 事件序列化与 SSE 响应封装
    │   └── schemas/         # auth / chat / session / sse / admin_config
    ├── agent/               # 图与领域节点
    │   ├── graph.py         # build_graph()：单张 StateGraph 装配
    │   ├── state.py         # AgentState（graph 级共享状态）
    │   ├── run.py           # run_domain_agent：三个 domain 节点共享的执行管道
    │   ├── runtime.py / ports.py / dependencies.py / middleware.py
    │   ├── time_tool.py     # get_current_time 当前时间工具
    │   ├── tools/subject_catalog.py
    │   ├── admin/           # admin_agent 节点与导入工具
    │   └── client/          # 用户端三域（一域一文件）
    │       ├── gateway.py   # gateway_router：结构化意图路由
    │       ├── search.py    # search_agent
    │       ├── discover.py  # discover_agent
    │       ├── recommend.py # recommend_agent
    │       ├── rag_tools.py # RAG 检索工具（rag_search / rag_discover / rag_recommend）
    │       ├── collections.py # 收藏查询工具，只读
    │       └── actions/     # 收藏写操作工具（按业务能力拆分）
    │           ├── __init__.py          # build_action_tools 显式组合
    │           ├── collection_progress.py # 追番进度预览/执行/取消
    │           └── wishlist.py          # 加入想看预览/执行/取消
    ├── chat/                # 会话服务（端口在 ports.py）
    │   ├── service.py       # ChatService：编排 store + graph + 流式引擎
    │   ├── streaming.py     # 流式引擎 → SSE 事件流
    │   ├── events.py        # AgentEvent / AgentEventType
    │   ├── event_sink.py / pending_events.py
    │   ├── pending_action.py# PendingAction 强类型可辨识联合
    │   ├── models.py / user.py
    ├── rag/                 # 检索增强（默认关闭）
    │   ├── use_case.py / retrieval.py / profile.py / user_profile.py
    │   └── ports.py / schemas.py
    ├── admin/               # 配置与导入应用服务
    │   ├── config_service.py / import_service.py / ports.py
    ├── adapters/            # 端口实现（外部依赖唯一出口）
    │   ├── business_http.py # HttpBusinessGateway：回查 business API
    │   ├── llm/             # agent_factory（LLM 工厂）/ embeddings（DashScope 嵌入）
    │   ├── mysql/           # import_records（SQLAlchemy 引擎与导入记录）
    │   ├── prompts/         # file_prompt（本地提示词文件）
    │   ├── redis/           # chat_store / prompt_repository / model_config_repository
    │   │                    # / subject_index / user_preference
    │   └── subprocess/      # import_job（以子进程启动导入器）
    └── shared/observability.py  # 结构化日志与 trace 中间件
```

## SSE 协议

流式接口 `POST /api/client/agent/stream`（管理端为 `POST /api/admin/agent/chat/stream`）返回 `text/event-stream`，每条消息 `data: {json}\n\n`。

事件类型（`app/chat/events.py` 中 `AgentEventType`）：

| `type` | 说明 |
|--------|------|
| `answer` | 回答增量文本（`text` 字段） |
| `thinking` | 思考增量文本（`text` 字段） |
| `function_call` | 工具调用生命周期（`state` 为 `start` / `end`，`message` 为状态文案，如「正在调用 RAG 搜索番剧」） |
| `status` | 节点状态提示 |
| `end` | 流结束标志 |

`AgentEvent` 还可能携带 `result`、`name`、`node`、`parent_node`、`arguments`、`meta` 等字段，供前端展示工具调用树。

## 追番进度更新（待确认动作）

用户端的「本周追番进度更新」采用**两段式确认**：预览不改库、确认才写库，中间状态在 Redis 持久化，跨对话轮次保持。

### 流程

```
用户:「我把本周已经更新的追番都看完了」
  └─► recommend_agent 调用 preview_weekly_collection_progress
        ├─ 业务端 POST /api/client/collections/progress-preview 生成 previewId（10 分钟 TTL）
        ├─ 本服务把 PendingAction 写入 Redis 键 agent:pending-action:{session_id}（TTL 600s）
        └─ 向用户展示明细并询问确认
用户:「确认」
  └─► gateway_router 检测到待确认动作 + 明确确认 → 确定性强制路由 recommend_agent（不走 LLM 路由）
        └─ recommend_agent 调用 execute_weekly_collection_progress（previewId 由系统注入）
              ├─ COMPLETED         → 清理待确认状态，按 成功/跳过/失败 分类汇报
              ├─ PREVIEW_CHANGED   → 更新 PendingAction 为新预览，先向用户展示并再次确认
              └─ 用户含糊/否定/预览过期 → 不执行；cancel_weekly_collection_progress 仅清理本地状态
```

### 关键点

- **待确认状态**：`PendingAction`（`app/chat/pending_action.py`，以 `type` 为判别字段的可辨识联合）经 `ChatStore` 持久化到 Redis，`ChatService` 在每次会话开始时注入 `pending_action` / `pending_preview_id` 到 `AgentState`。
- **强制路由**：`gateway.py` 对「待确认 + 明确确认」确定性返回 `recommend_agent`，避免 LLM 把「确认」路由到其他 Agent。
- **工具**：`actions/collection_progress.py` 提供 `preview_weekly_collection_progress` / `execute_weekly_collection_progress` / `cancel_weekly_collection_progress`；`execute` 的 `preview_id` 参数用 `InjectedState("pending_preview_id")` 注入，Agent 不得自行编造。
- **上下文注入**：`run_domain_agent(include_pending_action=True)` 仅 `recommend_agent` 注入待确认上下文；search / discover 不接触隐藏写操作状态。

## 推荐后加入「想看」（待确认动作）

用户要求把 Agent 推荐的番剧加入「想看」时，同样采用两段式确认：先预览（去重、过滤已收藏、最多 10 部），用户明确确认后才逐项调用 business 原子接口写入，绝不覆盖已有收藏。

### 流程

```
用户:「把前两部加入想看」
  └─► recommend_agent 调用 preview_add_to_wishlist
        ├─ 去重并限制最多 10 部，逐项查询收藏详情，已收藏归入 skippedItems
        ├─ 未收藏条目写入 PendingAction（ADD_TO_WISHLIST，Redis TTL 600s）
        └─ 返回 pendingItems / skippedItems 预览并询问确认
用户:「确认」
  └─► gateway_router 检测到 ADD_TO_WISHLIST 待确认动作 + 明确确认 → 确定性强制路由 recommend_agent
        └─ recommend_agent 调用 execute_add_to_wishlist
              ├─ 只读取 AgentState.pending_action.items，不接受模型自造列表
              ├─ 逐项 POST /api/client/collections/{subjectId}/wishlist（business 幂等保证不覆盖）
              ├─ 按 成功/跳过/失败 分类汇报，完成后清理待确认状态
              └─ 基础设施错误（写入结果不确定）保留待确认动作供重试
用户:「先不用」→ cancel_add_to_wishlist 仅清理本地待确认状态，不调用后端
```

### 关键点

- **强类型协议**：`PendingAction` 为可辨识联合，按 `type` 区分 `COLLECTION_PROGRESS_UPDATE` 与 `ADD_TO_WISHLIST`；Redis 读取经判别校验，未知 / 损坏数据抛 `ValidationError`，不交给模型猜测。
- **写操作工具**：`actions/` 包按业务能力拆分（`collection_progress.py` / `wishlist.py`），由 `build_action_tools` 显式组合，`recommend.py` 显式组合只读工具与写操作工具，保持依赖可见。
- **只读收藏工具**：`collections.py` 提供 `get_my_collections` / `get_my_collection` / `get_my_stats` / `get_my_watch_profile`。
- **business 原子保护**：`POST /api/client/collections/{subjectId}/wishlist` 仅在不存在收藏时插入（type=1），已存在任意收藏状态返回 `ALREADY_COLLECTED`，不依赖 Python 检查与写入时间差。

## RAG 检索（默认关闭）

`app/rag/` 提供语义检索与证据回答能力，通过 `RAG_ENABLED` 开关控制：

- 关闭时（默认）：检索降级为直接调用 business 的 `/api/client/subjects/search` 与 `/api/client/subjects`（按 `collectionTotal` 降序取候选），嵌入与索引对象替换为抛错的占位实现。
- 开启时：使用 Redis 向量索引（`RAG_INDEX_ALIAS` / `RAG_INDEX_VERSION`）与 DashScope `text-embedding-v4`（1024 维）做 BM25 + KNN 混合检索，经 RRF 融合后批量回查 Business 权威数据，再经 Evidence API 补充证据字段后返回。

### 证据链（Evidence Enrichment）

检索结果统一经 `business.batch_subjects` 权威回查后再返回，避免向量库脏数据直接暴露。通过权威回查的候选会进一步调用 `POST /api/client/evidence/batch` 获取完整证据字段：

- `summaryExcerpt`：简介摘录（前 200 字）
- `matchedTags`：匹配的 meta tags
- `matchedCredits`：匹配的主创（人物+关系）
- `matchedCharacters`：匹配的角色（角色名+关系）
- `matchedRelations`：匹配的系列关系
- `score` / `ratingTotal` / `collectionTotal`：评分与热度
- `airStatus`：播出状态（从 airDate 推断）
- `sourceFetchedAt`：数据来源时间
- `sourceRefs`：Bangumi 来源链接
- `retrievalScore` / `retrievalReason`：检索分数与原因

Agent 提示词已更新为只可依据工具返回的证据字段陈述事实，严禁编造工具返回中不存在的证据。

### 故障降级矩阵

| 故障场景 | 降级行为 |
|----------|----------|
| Redis 不可用 | 回退 Business 搜索，继续权威回查 + Evidence |
| Embedding 不可用 | 仅使用 BM25 词法搜索 |
| Business 权威回查不可用 | fail-closed，返回 `available=False` |
| Evidence API 不可用 | 候选保持原样返回（无证据字段但不崩溃） |
| Redis + Business 同时不可用 | fail-closed，返回 `available=False` |

结构化事件 `rag.evidence.enriched` 记录 Evidence 回查结果（成功/失败/候选数）。

索引由 [`jobs/indexer/`](jobs/indexer/) 构建，数据在 `resources` 之外，存放于 Redis。

## 托管提示词（Redis + 本地回退）

托管键包括 `client_gateway_prompt`、`client_search_agent_prompt`、`client_discover_agent_prompt`、`client_recommend_agent_prompt` 与管理员提示词。

- Redis 键：`agent:prompt:{prompt_key}`，值为含 `promptKey` / `promptContent` 的 JSON。
- 启动时 `RedisPromptRepository.initialize_snapshot()` 批量加载到进程内快照；失败仅告警，不中断启动。
- 未命中 / Redis 不可用 / 非托管键 → 回退 `resources/prompt/` 下的 Markdown 文件。

## 配置（`.env`）

配置由 `app/config.py` 的 pydantic-settings 读取，文件位于本目录的 `.env`（从 `.env.example` 复制）。**`Settings` 设置了 `extra="forbid"`，任何未在下表声明的变量都会导致启动失败。**

### LLM

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | 空 | `deepseek` 或 `dashscope`；留空则回退按 API Key 判断并打印告警 |
| `LLM_REASONING_EFFORT` | `high` | DeepSeek 思考强度（`low` / `high` / `max`），仅 deepseek 生效 |
| `LLM_TEMPERATURE` | `0.3` | 采样温度（route slot 固定为 0.0） |
| `LLM_MAX_TOKENS` | `4096` | 最大 token |
| `LLM_THINKING_BUDGET` | `2048` | 百炼思考 token 上限 |
| `DEEPSEEK_API_KEY` | 空 | DeepSeek 官方 API Key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek OpenAI 兼容端点 |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | DeepSeek 领域 Agent 模型 |
| `DEEPSEEK_MODEL_ROUTE` | `deepseek-v4-flash` | DeepSeek gateway 路由模型 |
| `DASHSCOPE_API_KEY` | 空 | 百炼 API Key |
| `DASHSCOPE_MODEL` | `qwen3.7-plus` | 百炼领域 Agent 模型 |
| `DASHSCOPE_MODEL_ROUTE` | `qwen3.7-plus` | 百炼 gateway 路由模型 |

### 服务与集成

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AGENT_HOST` / `AGENT_PORT` | `0.0.0.0` / `8090` | 服务监听 |
| `BACKEND_BASE_URL` | `http://localhost:8080` | 业务后端地址 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis（会话 / 消息 / 提示词 / 模型配置 / 待确认动作） |
| `JWT_SECRET` | 开发占位密钥 | 与 Spring Boot 共享的签名密钥，本地验签，不回调业务后端 |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | 跨域来源（联调管理端需追加 `http://localhost:5174`） |

### RAG（默认关闭）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_ENABLED` | `false` | 总开关；关闭时检索降级为 business 直接搜索 |
| `RAG_REDIS_URL` | 空 | 索引专用 Redis；留空则复用 `REDIS_URL` |
| `RAG_INDEX_ALIAS` | `idx:rag:subject:active` | 活跃索引别名 |
| `RAG_INDEX_VERSION` | `v1` | 索引版本（同时作为 Redis 键前缀的一部分） |
| `RAG_EMBEDDING_MODEL` | `text-embedding-v4` | 嵌入模型（当前仅支持该值） |
| `RAG_EMBEDDING_DIM` | `1024` | 向量维度（当前仅支持该值） |

### 数据导入（`jobs/` 使用）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ANIMETRACKER_LOG` | 空 | 可选日志配置 |
| `BANGUMI_BASE_URL` | `https://api.bgm.tv` | Bangumi API 基址 |
| `BANGUMI_IMAGE_PROXY_URL` | 空 | 封面图代理前缀；空则直接下载原图 |
| `BANGUMI_ACCESS_TOKEN` | 空 | Bangumi 访问令牌（可选，提升限流额度） |
| `BANGUMI_USER_AGENT` | `zhaizzH/AnimeTracker` | 请求 UA |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | `127.0.0.1` / `3306` / `root` / 空 / `anime_tracker` | MySQL 连接 |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO 地址 |
| `MINIO_SECURE` | `false` | 是否走 https |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | `minioadmin` | MinIO 凭据 |
| `MINIO_BUCKET` | `anime-tracker` | 公开封面桶 |
| `MINIO_RAW_BUCKET` | `anime-tracker-private` | 原始 Bangumi 快照私有桶，**必须与 `MINIO_BUCKET` 不同**（启动校验） |

> 上表后两组变量不进入 Agent 的业务逻辑，仅为与 `jobs/` 共用同一 `.env` 而声明。详见 [`jobs/importer/README.md`](jobs/importer/README.md)。

## 离线任务（`jobs/`）

| 任务 | 入口 | 说明 |
|------|------|------|
| importer | `python -m jobs.importer.main` | 从 Bangumi 导入番剧数据，见 [`jobs/importer/README.md`](jobs/importer/README.md) |
| indexer | `python -m jobs.indexer.main` | 为已导入条目构建 RAG 向量索引，需开启 DashScope 嵌入 |
| scheduler | `python -m jobs.scheduler.main` | 常驻进程，按 Asia/Shanghai 时间触发导入：每日 03:00 `recent`、每周日 04:00 近一年 `since`、每季度首月 05:00 `full` |

管理端触发的导入请求由 business 转发到本服务的 `POST /api/admin/agent/import/run`，Agent 以子进程方式启动 `jobs/importer/main.py`，通过 MySQL 锁与 PID 文件保证单实例，并会清理僵尸导入记录。

## 快速开始

```bash
cd backend/agent
cp .env.example .env          # 填写 LLM_PROVIDER、对应 API Key、REDIS_URL、JWT_SECRET
uv sync --dev                 # 安装依赖（含 dev 组：pytest / pytest-asyncio / respx）
uv run uvicorn main:app --reload --port 8090
```

启动后 `lifespan` 会依次：校验 LLM 配置、初始化 RedisChatStore、加载托管提示词快照、构建 agent 图、创建 ChatService。Redis 不可用只告警并继续启动，但会话与历史消息功能不可用。

## 核心用法示例

### 流式对话（SSE）

```bash
curl -N -X POST http://localhost:8090/api/client/agent/stream \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "<session-id>", "content": "推荐几部 2026 年夏季的治愈系番剧"}'
```

> `sessionId` 必须已存在且属于当前用户，否则返回 404「会话不存在或无权限」。请先创建会话。

### 会话管理

```bash
# 创建会话（不传 sessionId 则由服务端生成 uuid4）
curl -X POST http://localhost:8090/api/client/agent/sessions \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" -d '{}'

# 会话列表
curl http://localhost:8090/api/client/agent/sessions -H "Authorization: Bearer <access-token>"

# 历史消息
curl http://localhost:8090/api/client/agent/sessions/<session-id>/history \
  -H "Authorization: Bearer <access-token>"

# 删除会话（注意是 POST）
curl -X POST http://localhost:8090/api/client/agent/sessions/<session-id> \
  -H "Authorization: Bearer <access-token>"
```

### 接口清单

| 方法与路径 | 鉴权 | 说明 |
|-----------|------|------|
| `POST /api/client/agent/stream` | 用户 | SSE 流式对话 |
| `GET` / `POST /api/client/agent/sessions` | 用户 | 会话列表 / 新建 |
| `GET /api/client/agent/sessions/{id}/history` | 用户 | 历史消息 |
| `POST /api/client/agent/sessions/{id}` | 用户 | 删除会话 |
| `GET /api/client/agent/health` | 用户 | 健康检查（含 LLM 配置校验） |
| `POST /api/admin/agent/chat/stream` | 管理员 | 管理员 SSE 流式对话 |
| `GET` / `POST /api/admin/agent/chat/sessions` | 管理员 | 管理员会话列表 / 新建 |
| `GET /api/admin/agent/chat/sessions/{id}/history` | 管理员 | 管理员历史消息 |
| `POST /api/admin/agent/chat/sessions/{id}` | 管理员 | 删除管理员会话 |
| `GET /api/admin/agent/prompts` / `GET /prompts/{key}` | 管理员 | 托管提示词查询 |
| `POST /api/admin/agent/prompts/{key}/update` / `POST /prompts/{key}/reset` | 管理员 | 提示词更新 / 重置 |
| `GET /api/admin/agent/config` / `POST /api/admin/agent/config/update` | 管理员 | 运行时模型配置读写 |
| `POST /api/admin/agent/import/run` | 管理员 | 触发导入（`mode` 必填，`key` / `since` / `workers` 可选） |
| `GET /docs` | — | Swagger 文档 |

> 管理端接口要求 JWT 中角色为 `ADMIN`（本地验签 + 角色校验，纵深防御）。管理端前端「Agent 配置」与「Agent 对话」页即对接这些端点。

## 测试

```bash
uv run pytest
```

pytest 配置在 `pyproject.toml`（`pythonpath = ["."]`、`asyncio_mode = "auto"`、`test.globals = true`）。当前 216 条测试覆盖：

| 目录 | 覆盖范围 |
|------|----------|
| `tests/evals/` | 50-case 确定性评测框架（metrics、runner、golden cases） |
| `tests/rag/` | 证据契约、故障矩阵、多实体 profile、结构化实体 ID/名称 allowlist 与 fail-closed |
| `tests/jobs/importer/` | 导入漂移检测（eps/volumes、credit_type、AIRING、stale replace-set、profile hash） |
| `tests/jobs/indexer/` | 实体加载、shadow index、search repository |
| `tests/jobs/backfill/` | 详情回填 repository 与 worker |
| `tests/jobs/scheduler/` | 定时调度（import/indexer/backfill） |
| `tests/adapters/` | Business HTTP 网关（batch_evidence、evidence/resolve）与 Redis 实体名称解析 |

## 常见问题

**Q：启动即报 `LLM API Key 未配置`？**
A：`resolve_llm_provider` 在 `lifespan` 阶段就会校验。设置 `LLM_PROVIDER` 并配置对应 Key；两者都留空时直接抛错终止启动。

**Q：启动报 `无效的 LLM_PROVIDER`？**
A：`LLM_PROVIDER` 只接受 `deepseek` 或 `dashscope`，且必须配套该供应商的 Key。

**Q：启动报 `Extra inputs are not permitted`？**
A：`Settings` 使用 `extra="forbid"`，`.env` 中存在未在 `app/config.py` 声明的变量。以 `.env.example` 为模板核对。

**Q：启动报 `MINIO_RAW_BUCKET must differ from MINIO_BUCKET`？**
A：原始快照桶与公开封面桶必须不同名，为 `MINIO_RAW_BUCKET` 另起一个桶名。

**Q：日志出现 `Redis 连接失败,启动继续`？**
A：非致命告警。服务继续启动，但会话、历史、托管提示词与待确认动作全部不可用。修复 `REDIS_URL` 后重启。

**Q：对话返回 404「会话不存在或无权限」？**
A：`/stream` 要求 `sessionId` 已存在且属于当前用户（服务端会拉取用户会话列表做归属校验）。先调用 `POST /sessions` 创建。

**Q：模型一直走不到 RAG 检索？**
A：`RAG_ENABLED` 默认为 `false`，此时 `rag_*` 工具降级为 business 直接搜索，嵌入与索引对象是抛错占位。需要先构建索引（见 `jobs/indexer`）再开启开关。

**Q：改了提示词但没生效？**
A：托管提示词优先读 Redis 且启动时已加载为进程内快照。在管理端更新后需确认快照已同步，必要时重启服务。

**Q：`POST /sessions/{id}` 为什么是删除？**
A：这是既有设计，删除会话使用 POST 而非 DELETE。

## 与相邻模块的关联

- **business**（[`../business/README.md`](../business/README.md)）：本服务的调用方（代理转发）与被调方（工具回查）。两者必须共享 `JWT_SECRET`。
- **导入器**（[`jobs/importer/README.md`](jobs/importer/README.md)）：由本服务以子进程方式启动，共用环境与 `.env`。
- **索引器**（`jobs/indexer/`）：为 RAG 提供向量数据，依赖 DashScope 嵌入与 `rag_index_job` 表。
- **提示词**：本地 Markdown 位于 `resources/prompt/`，线上托管版本存于 Redis。
- **后端总览**：[`../README.md`](../README.md) · **项目总览**：[`../../README.md`](../../README.md)
