# AnimeTracker Agent

基于 **FastAPI + LangGraph** 构建的 AI 对话 Agent，面向番剧场景提供搜索、发现、推荐三类对话能力，并通过工具调用后端业务 API 获取实时数据。

- **默认端口**：`8090`（Swagger 文档：`/docs`）
- **LLM**：DashScope Qwen（默认 `qwen-plus`）

## 架构：Router Graph

Agent 以一张 LangGraph 状态图驱动多轮对话，流程如下：

```
                 ┌──────────────┐
                 │ role_router  │  条件入口：按角色分发
                 └──────┬───────┘
         ┌──────────────┴──────────────┐
         ▼                             ▼
   ┌────────────┐               ┌────────────┐
   │user_router │               │admin_router│
   └─────┬──────┘               └─────┬──────┘
         │ 意图分发                     │ (Phase 2)
   ┌─────┼─────┐                     ▼
   ▼     ▼     ▼                 ┌────────┐
search discover recommend       │ denied │  (无权限/占位)
   └─────┬─────┘                 └────────┘
         │ 整理回复
         ▼
    ┌──────────┐
    │finalizer │  汇总为最终自然语言回答
    └──────────┘
```

### 节点说明（`app/graph/`）

| 节点 | 文件 | 职责 |
|------|------|------|
| `user_router` / `admin_router` | `nodes.create_*_router` | LLM 判断用户意图 / 角色 |
| `role_router` | `nodes.create_role_router` | 条件入口：分发到 user / admin |
| `search` / `discover` / `recommend` | `nodes.create_sub_agent_node` | 子 Agent，绑定 `user_tools` 与各自 Prompt 循环调用工具 |
| `denied` | `nodes.create_denied_node` | 拒绝 / 占位回复（管理侧能力 Phase 2） |
| `finalizer` | `nodes.create_finalizer_node` | 汇总子 Agent 结果生成最终回复 |

### 工具（`app/tools/`）

`user_tools` 通过 HTTP 调用 business 后端（`backend_base_url`，默认 `http://localhost:8080`）：

- `search_subjects` —— 关键词搜索番剧
- `get_subject_detail` —— 番剧详情
- `get_episodes` —— 剧集列表
- `get_schedule` —— 每周放送表
- `get_season_subjects` —— 季度新番
- `get_popular_subjects` / `get_top_rated` —— 热门 / 高分
- `get_tags` / `get_subjects_by_tag` —— 标签与按标签筛选
- `get_stats` —— 平台统计

> `admin_tools` 当前为占位（空列表），管理侧工具计划在 Phase 2 实现。

## 目录结构

```
agent/
├── main.py              # FastAPI 入口，挂载 chat 路由与 lifespan 初始化
├── requirements.txt
├── .env.example         # 配置模板
└── app/
    ├── config.py        # pydantic-settings 配置（Settings）
    ├── api/chat.py      # /chat 接口，注入 ChatService 与 SQLiteStore
    ├── db/              # SQLite 存储（models / sqlite_store）
    ├── graph/           # LangGraph 状态图（graph/nodes/state/prompts/sub_agent）
    ├── llm/models.py    # LLM 工厂（create_llm）
    ├── schemas/         # 请求/响应模型（auth / chat / session）
    ├── service/chat.py  # ChatService：编排 store + router_graph
    └── tools/           # 用户/管理工具定义
```

## 配置（`.env`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `dashscope_api_key` | 空 | DashScope API Key（必填） |
| `llm_model` | `qwen-plus` | 模型名 |
| `llm_temperature` | `0.3` | 温度 |
| `llm_max_tokens` | `4096` | 最大 token |
| `agent_host` / `agent_port` | `0.0.0.0` / `8090` | 服务监听 |
| `backend_base_url` | `http://localhost:8080` | 业务后端地址 |
| `database_url` | `sqlite:///agent.db` | 会话库（SQLite） |
| `agent_max_iterations` | `5` | 子 Agent 最大工具循环次数 |
| `cors_origins` | `["http://localhost:5173"]` | 前端跨域来源 |

## 本地运行

```bash
cd backend/agent
cp .env.example .env          # 填入 DASHSCOPE_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
```

启动后自动建库（`SQLiteStore.init_db`）并构建 Router Graph。
交互接口：

- `POST /chat` —— 发送消息，返回 Agent 回复
- `GET /docs` —— Swagger 文档
