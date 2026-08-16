# AnimeTracker Agent

基于 **FastAPI + LangGraph + langchain create_agent** 构建的 AI 对话 Agent，面向番剧场景提供搜索、发现、推荐三类对话能力，通过工具调用后端业务 API 获取实时数据，经 SSE 流式输出。

- **默认端口**：`8090`（Swagger 文档：`/docs`）
- **LLM**：DeepSeek 官方直连或 DashScope 百炼 Qwen（同时配置时优先 DeepSeek）
- **存储**：Redis（会话 / 消息 + 托管提示词快照）

## 架构定位

本服务是真正的**大模型推理层**。业务后端 `backend/business` 内置 `agent` 代理模块（Maven 模块 `animetracker-agent`），在 `8080` 端口对外暴露 `/api/client/agent/*`（用户端）与 `/api/admin/agent/*`（管理端），并将请求转发到本服务：

```
前端 (5173) ──/api/client/agent/*──► business :8080 (agent 代理层) ──HTTP 转发──► 本服务 :8090
                                                                          │
                                                                          └─工具调用─► business API（获取番剧实时数据）
```

- 前端不直接访问 `8090`；所有 Agent 流量经 Vite 代理统一走 `8080` 的 `/api` 前缀。
- 本服务通过 `BACKEND_BASE_URL`（默认 `http://localhost:8080`）回查业务 API。
- 后端代理层配置见 [`../business/README.md`](../business/README.md)；后端总览见 [`../README.md`](../README.md)；项目总览见 [`../../README.md`](../../README.md)。

## 架构：单张 StateGraph

Agent 以一张 LangGraph 状态图驱动，节点内部用 `langchain.agents.create_agent` 执行，并经 ContextVar 事件总线把增量事件流式输出给前端：

```
                 ┌──────────────┐
                 │ entry_router │  条件入口：按角色分发
                 └──────┬───────┘
         ┌──────────────┴──────────────┐
         ▼                             ▼
   ┌──────────────┐             ┌────────────┐
   │ gateway_router│            │admin_denied│  静态回复（管理功能占位）
   └──────┬───────┘             └────────────┘
   ┌──────┴───────┐
   ▼              ▼            ▼
search_agent  discover_agent  recommend_agent
   │              │            │
   └──────────────┴────────────┘
               ▼
             END
```

### 流程

1. `entry_router` 按角色分发：`ADMIN` → `admin_denied`（静态中文占位，不烧模型调用）；`USER` → `gateway_router`。
2. `gateway_router` 用结构化路由（`create_agent` + JSON 输出）把用户问题路由到 `search_agent` / `discover_agent` / `recommend_agent`。
3. 三个 domain 节点统一走 `run_domain_agent`（`agent/run.py`）共享管道：用 `create_agent` 绑定各自工具与系统提示词，`agent_stream` 消费模型增量——思考增量走 `emit_thinking_delta`，回答增量走 `emit_answer_delta`，工具调用经中间件发 `function_call` 事件。
4. `core/streaming.py` 消费图的 `values` 事件 + 总线事件，产出 `AssistantResponse` SSE。

## 目录结构

```
backend/agent/
├── main.py                  # FastAPI 入口：lifespan 初始化 RedisStore + prompt 快照 + 图
├── requirements.txt
├── .env.example             # 配置模板（需 REDIS_URL）
├── tests/                   # pytest 测试（test_*.py）
├── importer/                # 番剧数据导入器（Bangumi，独立 CLI）
└── app/
    ├── config.py            # pydantic-settings 配置 + AgentChatModelSlot + create_agent_chat_llm
    ├── api/
    │   ├── chat.py          # /api/client/agent/* 路由（流式对话 / 会话管理）
    │   ├── admin_config.py  # /api/admin/agent/* 管理端（提示词 / 运行时模型配置）
    │   └── deps.py          # verify_token：本地 JWT 验签（共享业务后端密钥）
    ├── agent/
    │   ├── state.py         # AgentState / RoutingState（graph 级共享状态）
    │   ├── graph.py         # build_graph()：单张 StateGraph 装配
    │   ├── run.py           # run_domain_agent：三个 domain 节点共享的执行管道
    │   ├── http.py          # call_api：工具回查业务后端 API
    │   ├── time_tool.py     # get_current_time 当前时间工具
    │   ├── admin/node.py    # admin_denied 占位
    │   └── client/          # 用户端三个域（一域一文件）
    │       ├── gateway.py   # gateway_router：结构化意图路由
    │       ├── search.py    # search_agent + 搜索工具
    │       ├── discover.py  # discover_agent + 发现工具
    │       ├── recommend.py # recommend_agent
    │       ├── collections.py # 收藏查询工具，只读（collection_read_tools）
    │       └── actions/     # 收藏写操作工具（按业务能力拆分）
    │           ├── __init__.py          # 显式组合 action_tools
    │           ├── collection_progress.py # 追番进度预览/执行/取消
    │           └── wishlist.py          # 加入想看预览/执行/取消
    ├── core/
    │   ├── agent_runtime.py # agent_invoke / agent_stream / _run_async
    │   ├── event_bus.py     # ContextVar 事件总线
    │   ├── middleware.py    # tool_call_status 装饰器 + build_tool_status_middleware
    │   ├── pending_action.py# PendingAction 事件收集（ContextVar set/reset + emit_*）
    │   ├── prompt_sync.py   # 托管提示词 Redis 优先本地回退
    │   ├── runtime_config.py# 运行时模型配置（Redis + 短 TTL 缓存）
    │   └── streaming.py     # 精简流式引擎 → SSE
    ├── db/
    │   ├── base.py          # async ChatStore 抽象（含 get/save/delete_pending_action）
    │   ├── redis_store.py   # Redis 实现（会话 / 消息 / 待确认动作）
    │   └── models.py
    ├── llm/models.py        # LLM 工厂（create_llm）+ ChatTongyi 流式补丁
    ├── schemas/             # auth / chat / session / sse_response / admin_config / pending_action
    ├── service/chat.py      # ChatService：编排 store + graph + 流式引擎
    └── utils/prompt_utils.py
```

## SSE 协议

流式接口 `POST /api/client/agent/stream` 返回 `text/event-stream`，每条消息 `data: {json}\n\n`，序列化 `exclude_none=True`、`ensure_ascii=False`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `answer` / `thinking` / `function_call` / `status` | 事件类型 |
| `content.text` | 字符串 | answer / thinking 的增量文本 |
| `content.state` | `start` / `end` | function_call 生命周期 |
| `content.message` | 字符串 | 工具状态文案（如“正在调用 搜索番剧”） |
| `is_end` | 布尔 | 流结束标志 |
| `meta` | 对象 | 预留扩展 |

`used_tools` 的唯一权威来源是流式引擎消费方（`on_answer_completed` 回调）聚合，节点不返回。

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

- **待确认状态**：`PendingAction`（`app/schemas/pending_action.py`，强类型可辨识联合）经 `ChatStore.save_pending_action` 持久化到 Redis，`ChatService` 在每次会话开始时注入 `pending_action` / `pending_preview_id` 到 AgentState。
- **强制路由**：`gateway.py` 的 `_resolve_forced_pending_route` 对「待确认 + 明确确认」确定性返回 `recommend_agent`，与图路由 `_route_from_gateway` 期望的 `{"routing": {...}}` 结构一致，避免 LLM 把「确认」路由到其他 Agent。
- **工具**：`actions/collection_progress.py` 提供 `preview_weekly_collection_progress` / `execute_weekly_collection_progress` / `cancel_weekly_collection_progress`，共用 `_preview_data_to_pending_action` 构造待确认状态；`execute` 的 `preview_id` 参数用 `InjectedState("pending_preview_id")` 注入，Agent 不得自行编造。
- **提示词**：`recommend_agent_prompt.md` 增加「追番进度更新（待确认动作）」约束；`run.py` 的 `_build_pending_context` 把 previewId 与明细注入系统提示词。

## 推荐后加入「想看」（待确认动作）

用户要求把 Agent 推荐的番剧加入「想看」时，同样采用两段式确认：先预览（去重、过滤已收藏、最多 10 部），用户明确确认后才逐项调用 Business 原子接口写入，绝不覆盖已有收藏。

### 流程

```
用户:「把前两部加入想看」
  └─► recommend_agent 调用 preview_add_to_wishlist
        ├─ 去重并限制最多 10 部，逐项查询收藏详情，已收藏归入 skippedItems
        ├─ 未收藏条目写入 PendingAction（ADD_TO_WISHLIST，Redis 键 agent:pending-action:{session_id}，TTL 600s）
        └─ 返回 pendingItems / skippedItems 预览并询问确认
用户:「确认」
  └─► gateway_router 检测到 ADD_TO_WISHLIST 待确认动作 + 明确确认 → 确定性强制路由 recommend_agent
        └─ recommend_agent 调用 execute_add_to_wishlist
              ├─ 只读取 AgentState.pending_action.items，不接受模型自造列表
              ├─ 逐项 POST /api/client/collections/{subjectId}/wishlist（Business 幂等保证不覆盖）
              ├─ 按 成功/跳过/失败 分类汇报，完成后 CLEAR 待确认状态
              └─ 基础设施错误（写入结果不确定）保留待确认动作供重试
用户:「先不用」→ cancel_add_to_wishlist 仅清理本地待确认状态，不调用后端
```

### 关键点

- **强类型协议**：`PendingAction` 为可辨识联合（`app/schemas/pending_action.py`），按 `type` 区分 `COLLECTION_PROGRESS_UPDATE` 与 `ADD_TO_WISHLIST`；Redis 读取经 `parse_pending_action_json` 校验，未知/损坏数据安全失败，不交给模型猜测。
- **写操作工具**：`actions/` 包按业务能力拆分（`collection_progress.py` / `wishlist.py`），`actions/__init__.py` 组合 `action_tools`，`recommend.py` 显式组合只读工具与写操作工具，保持依赖可见。
- **上下文注入**：`run_domain_agent(include_pending_action=True)` 仅 recommend_agent 注入待确认上下文；search/discover 不接触隐藏写操作状态。
- **Business 原子保护**：`POST /api/client/collections/{subjectId}/wishlist` 仅在不存在收藏时插入（type=1），已存在任意收藏状态返回 `ALREADY_COLLECTED`，不依赖 Python 检查与写入时间差。

## 托管提示词（Redis + 本地回退）

四个托管键（`MANAGED_PROMPT_KEYS`）：`client_gateway_prompt`、`client_search_agent_prompt`、`client_discover_agent_prompt`、`client_recommend_agent_prompt`。

- Redis 键：`agent:prompt:{prompt_key}`，值为 `{"promptKey": ..., "promptContent": ...}` JSON。
- 启动时 `initialize_agent_prompt_snapshot()` 批量加载到进程内快照；任一失败仅告警，不中断启动。
- 未命中 / Redis 不可用 / 非托管键 → 回退本地 `resources/prompt/` 下的 md 文件。

## 配置（`.env`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `deepseek_api_key` | 空 | DeepSeek 官方 API Key；存在时优先使用 DeepSeek |
| `deepseek_base_url` | `https://api.deepseek.com` | DeepSeek OpenAI 兼容端点 |
| `deepseek_model` | `deepseek-chat` | DeepSeek 领域 Agent 模型 |
| `deepseek_model_route` | `deepseek-chat` | DeepSeek gateway 路由模型 |
| `dashscope_api_key` | 空 | DashScope API Key；未配置 DeepSeek 时作为回退供应商 |
| `dashscope_model` | `qwen3.7-plus` | DashScope 领域 Agent 模型 |
| `dashscope_model_route` | `qwen3.7-plus` | DashScope gateway 路由模型 |
| `llm_temperature` | `0.3` | 默认温度（route slot 固定 0.0） |
| `llm_max_tokens` | `4096` | 最大 token |
| `llm_thinking_budget` | `2048` | 思考预算 |
| `agent_host` / `agent_port` | `0.0.0.0` / `8090` | 服务监听 |
| `backend_base_url` | `http://localhost:8080` | 业务后端地址 |
| `redis_url` | `redis://localhost:6379/0` | Redis 地址（会话 / 消息 / 提示词 / 运行时模型配置） |
| `jwt_secret` | 开发占位密钥 | 与 Spring Boot 共享的 JWT 签名密钥——agent 本地验签，不回调业务后端 |
| `cors_origins` | `["http://localhost:5173"]` | 前端跨域来源（用户端 client :5173；如需联调管理端 admin :5174，追加 `http://localhost:5174`） |

> `DB_*` / `BANGUMI_*` / `MINIO_*` 等数据导入变量并入本 `.env`，仅供 `importer/` 侧 `load_dotenv()+os.getenv` 读取，不进入上表 pydantic Settings。详见 [importer/README.md](importer/README.md)。

## 数据导入 importer

`importer/` 是 Bangumi 数据导入器，与 Agent 共用本模块的 venv 与 `.env`（`DB_*` / `BANGUMI_*` / `MINIO_*`）。

手动触发：

```bash
cd backend/agent
python importer/main.py --mode season --key 2026-summer
```

通过管理后台触发的请求由 Java 转发到本模块的 `POST /api/admin/agent/import/run`，进程由 Agent 后台托管（单实例约束）。

## 本地运行

```bash
cd backend/agent
cp .env.example .env          # 填入 DEEPSEEK_API_KEY 或 DASHSCOPE_API_KEY，并配置 REDIS_URL
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
```

启动后 lifespan 初始化 RedisStore（会话 / 消息）、加载托管提示词快照、构建 client agent 图。Redis 不可用时仅告警并继续启动，但会话功能不可用。

交互接口：

- `POST /api/client/agent/stream` —— SSE 流式对话
- `GET /api/client/agent/sessions` / `POST /api/client/agent/sessions` —— 会话列表 / 新建
- `GET /api/client/agent/sessions/{id}/history` —— 历史消息
- `POST /api/client/agent/sessions/{id}` —— 删除会话
- `GET /api/client/agent/health` —— 健康检查
- `GET /api/admin/agent/prompts` / `GET /{key}` / `POST /{key}/update` / `POST /{key}/reset` —— 托管提示词查询 / 更新 / 重置
- `GET /api/admin/agent/config` / `POST /api/admin/agent/config/update` —— 运行时模型配置读写
- `/api/admin/agent/chat/*` —— 管理员独立会话、历史记录与 SSE 流式对话（与用户会话隔离）
- `GET /docs` —— Swagger 文档

> `/api/admin/agent/*` 为管理端接口，需 ADMIN 角色（本地验签）；管理端前端「Agent 配置」页即对接这些端点。

## 确定性评测

`evals/` 提供复用生产图结构的 Agent 评测。离线模式用确定性 LLM 与 Business API 替身覆盖路由、推荐、追番进度、想看和安全边界，不访问网络、不写入真实数据，并作为 CI 门禁：

```bash
python -m evals.runner --mode offline
```

Live 模式需要显式设置 `ALLOW_LIVE_AGENT_EVAL=true` 和供应商 Key，只用于诊断模型表现；业务写接口仍由 dry-run 替身接管。数据集、退出码和隐私约束详见 [`evals/README.md`](evals/README.md)。

## 相关文档

- 后端总览：[`../README.md`](../README.md)
- 业务后端：[`../business/README.md`](../business/README.md)
- 数据导入：[`importer/README.md`](importer/README.md)
- Agent 评测：[`evals/README.md`](evals/README.md)
- 项目总览：[`../../README.md`](../../README.md)
