# AnimeTracker Agent

基于 **FastAPI + LangGraph + langchain create_agent** 构建的 AI 对话 Agent，面向番剧场景提供搜索、发现、推荐三类对话能力，通过工具调用后端业务 API 获取实时数据，经 SSE 流式输出。

- **默认端口**：`8090`（Swagger 文档：`/docs`）
- **LLM**：DashScope Qwen（默认 `qwen-plus`）
- **存储**：Redis（会话 / 消息 + 托管提示词快照）

## 在整体架构中的位置

本服务是真正的**大模型推理层**。业务后端 `backend/business` 内置 `agent` 代理模块（Maven 模块 `anime-tracker-agent`），在 `8080` 端口对外暴露 `/api/client/agent/*`（用户端）与 `/api/admin/agent/*`（管理端），并将请求转发到本服务：

```
前端 (5173) ──/api/client/agent/*──► business :8080 (agent 代理层) ──HTTP 转发──► 本服务 :8090
                                                                          │
                                                                          └─工具调用─► business API（获取番剧实时数据）
```

- 前端不直接访问 `8090`；所有 Agent 流量经 Vite 代理统一走 `8080` 的 `/api` 前缀。
- 本服务通过 `BACKEND_BASE_URL`（默认 `http://localhost:8080`）回查业务 API。
- 后端代理层配置见 [`../business/README.md`](../business/README.md)；项目总览见 [`../../README.md`](../../README.md)。

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

### 目录结构

```
backend/agent/
├── main.py                  # FastAPI 入口：lifespan 初始化 RedisStore + prompt 快照 + 图
├── requirements.txt
├── .env.example             # 配置模板（需 REDIS_URL）
├── tests/                   # pytest 测试（test_*.py）
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
    │       └── collections.py # user_collections_tools（InjectedState 注入用户态）
    ├── core/
    │   ├── agent_runtime.py # agent_invoke / agent_stream / _run_async
    │   ├── event_bus.py     # ContextVar 事件总线
    │   ├── middleware.py    # tool_call_status 装饰器 + build_tool_status_middleware
    │   ├── prompt_sync.py   # 托管提示词 Redis 优先本地回退
    │   ├── runtime_config.py# 运行时模型配置（Redis + 短 TTL 缓存）
    │   └── streaming.py     # 精简流式引擎 → SSE
    ├── db/
    │   ├── base.py          # async ChatStore 抽象
    │   ├── redis_store.py   # Redis 实现（会话 / 消息）
    │   └── models.py
    ├── llm/models.py        # LLM 工厂（create_llm）+ ChatTongyi 流式补丁
    ├── schemas/             # auth / chat / session / sse_response / admin_config
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

## 托管提示词（Redis + 本地回退）

四个托管键（`MANAGED_PROMPT_KEYS`）：`client_gateway_prompt`、`client_search_agent_prompt`、`client_discover_agent_prompt`、`client_recommend_agent_prompt`。

- Redis 键：`agent:prompt:{prompt_key}`，值为 `{"promptKey": ..., "promptContent": ...}` JSON。
- 启动时 `initialize_agent_prompt_snapshot()` 批量加载到进程内快照；任一失败仅告警，不中断启动。
- 未命中 / Redis 不可用 / 非托管键 → 回退本地 `resources/prompt/` 下的 md 文件。

## 配置（`.env`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `dashscope_api_key` | 空 | DashScope API Key（必填） |
| `llm_model` | `qwen-plus` | 模型名 |
| `llm_model_route` | `qwen-plus` | gateway 路由专用模型（快速模型，降低首段等待） |
| `llm_temperature` | `0.3` | 默认温度（route slot 固定 0.0） |
| `llm_max_tokens` | `4096` | 最大 token |
| `llm_thinking_budget` | `2048` | 思考预算 |
| `agent_host` / `agent_port` | `0.0.0.0` / `8090` | 服务监听 |
| `backend_base_url` | `http://localhost:8080` | 业务后端地址 |
| `redis_url` | `redis://localhost:6379/0` | Redis 地址（会话 / 消息 / 提示词 / 运行时模型配置） |
| `jwt_secret` | 开发占位密钥 | 与 Spring Boot 共享的 JWT 签名密钥——agent 本地验签，不回调业务后端 |
| `cors_origins` | `["http://localhost:5173"]` | 前端跨域来源（用户端 client :5173；如需联调管理端 admin :5174，追加 `http://localhost:5174`） |

## 本地运行

```bash
cd backend/agent
cp .env.example .env          # 填入 DASHSCOPE_API_KEY 与 REDIS_URL（本地需启动 Redis）
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
- `GET /docs` —— Swagger 文档

> `/api/admin/agent/*` 为管理端接口，需 ADMIN 角色（本地验签）；管理端前端「Agent 配置」页即对接这些端点。
