# AI 追番助手 Agent 设计文档

> 基于 Tool-based Agent 的方案，为 AnimeTracker 添加 AI 聊天助手功能

**日期:** 2026-07-14
**状态:** 设计稿
**技术栈:** FastAPI + LangChain 1.3+ / ChatDashScope (qwen3.7-max) / WebSocket / SQLite / Vue 3

---

## 1. 概述

在现有 `backend/agent/` 目录基础上，实现一个多能力聚合的 AI 追番助手。用户通过前端聊天窗口与 Agent 交互，Agent 通过 Tool Calling 调用现有 Spring Boot 后端 API 完成推荐、搜索、问答、追番建议、数据查询等任务。

### 能力范围

| 能力 | 说明 |
|------|------|
| A) 番剧推荐 | 基于 LLM 知识 + 番剧详情推荐类似作品或满足特定条件的番剧 |
| B) 自然语言搜索 | 用户用自然语言描述需求，Agent 提取关键词调搜索 API |
| C) 番剧问答 | 回答关于番剧的问题（播出信息、制作公司、剧情等） |
| D) 追番建议 | 查询每周追番日程，告诉用户今天/本周有什么更新 |
| E) 数据查询 | 查询热度榜、评分榜、标签统计等全局数据 |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                  │
│  ┌───────────────────────────────────────────────┐  │
│  │  ChatWidget (右下角 FAB → 侧滑面板)            │  │
│  │  ├─ ChatSessionList (会话列表)                 │  │
│  │  ├─ ChatMessageList (消息 + 流式渲染)          │  │
│  │  └─ ChatInput (输入框 + 快捷提问)              │  │
│  │  WebSocket ws://localhost:8090/ws/chat         │  │
│  └──────────────────────┬────────────────────────┘  │
└─────────────────────────┼───────────────────────────┘
                          │ WebSocket (连接时传 JWT Token)
┌─────────────────────────┼───────────────────────────┐
│  backend/agent (FastAPI + LangChain 1.3+)            │
│                                                       │
│  ws://localhost:8090/ws/chat                          │
│  └─ WS Handler → ChatSessionManager                   │
│       ├─ 连接校验 (调 Spring Boot -> userId)          │
│       ├─ 消息分发 → AgentExecutor                     │
│       ├─ 流式回调 → WebSocket 推送                    │
│       └─ 心跳保活 (30s)                               │
│                                                       │
│  AgentExecutor                                        │
│  ├─ LLM: ChatDashScope(model="qwen3.7-max")           │
│  ├─ Prompt: ReAct Agent (中文 system prompt)          │
│  └─ Tools: 10 个工具 (见 §4)                          │
│                                                       │
│  SQLite                                               │
│  ├─ sessions (会话元数据)                              │
│  ├─ messages (消息记录)                                │
│  └─ CRUD 封装                                         │
│                                                       │
│  ──→ HTTP (localhost:8080) ──→ Spring Boot API       │
└───────────────────────────────────────────────────────┘
```

### 数据流

```
用户输入 → WebSocket → FastAPI → AgentExecutor
  → LLM 分析意图 → 选择 Tool → httpx 调 Spring Boot API
  → LLM 组织回答 → 流式分块 WebSocket 返回 → 前端逐字展示
```

---

## 3. WebSocket 消息协议

### 连接建立

```
ws://localhost:8090/ws/chat?token=<JWT_TOKEN>
```

服务端收到连接请求后，调 `GET http://localhost:8080/api/user/me` 校验 Token 并获取 `userId`。校验失败返回 401 断开连接。

### 消息类型

#### 客户端 → 服务端

```jsonc
// 发送消息
{ "type": "message", "session_id": "uuid", "content": "推荐几部热血战斗番" }

// 新会话
{ "type": "new_session" }

// 加载历史
{ "type": "load_history", "session_id": "uuid" }

// 获取会话列表
{ "type": "list_sessions" }

// 删除会话
{ "type": "delete_session", "session_id": "uuid" }
```

#### 服务端 → 客户端

```jsonc
// 流式 token
{ "type": "token", "session_id": "uuid", "content": "推荐" }

// 完成
{ "type": "done", "session_id": "uuid", "full_content": "...", "tool_calls": ["search_subjects"] }

// 错误
{ "type": "error", "session_id": "uuid", "message": "查询超时，请重试" }

// 会话列表
{ "type": "session_list", "sessions": [{ "session_id": "...", "title": "...", "message_count": 5, "created_at": "..." }] }

// 历史消息
{ "type": "history", "session_id": "uuid", "messages": [{ "role": "user", "content": "..." }, { "role": "assistant", "content": "..." }] }

// 心跳 pong
{ "type": "pong" }
```

### 心跳

- 服务端每 30 秒发送 `{ "type": "ping" }`
- 客户端响应 `{ "type": "pong" }`
- 60 秒无响应则断开连接

---

## 4. Tools 定义

10 个工具，全部通过 `httpx` 调用 Spring Boot 后端 API。

| 工具 | 后端 API | 用途 |
|------|----------|------|
| `search_subjects` | `GET /api/user/subjects/search?q=` | 关键词搜索番剧 |
| `get_subject_detail` | `GET /api/user/subjects/{id}` | 番剧详细信息 |
| `get_episodes` | `GET /api/user/subjects/{id}/episodes` | 番剧剧集列表 |
| `get_schedule` | `GET /api/user/subjects/schedule` | 按星期获取追番日程 |
| `get_season_subjects` | `GET /api/user/subjects/season` | 按季度获取新番 |
| `get_popular_subjects` | `GET /api/user/subjects?sort=collectionTotal` | 热度榜 |
| `get_top_rated` | `GET /api/user/subjects?sort=score` | 评分榜 |
| `get_tags` | `GET /api/user/tags` | 所有标签 |
| `get_subjects_by_tag` | `GET /api/user/tags/{tag}/subjects` | 按标签查番剧 |
| `get_stats` | `GET /api/user/subjects` (取 total) | 统计数据 |

每个工具使用 `@tool` 装饰器（LangChain 1.3+），明确定义参数类型和 docstring 作为 LLM 的指引。

---

## 5. 数据存储 (SQLite)

### 表结构

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    role TEXT NOT NULL,         -- 'user' | 'assistant'
    content TEXT NOT NULL,
    tool_calls TEXT,            -- JSON array, optional
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_messages_session ON messages(session_id, created_at);
CREATE INDEX idx_sessions_user ON sessions(user_id, updated_at);
```

### CRUD 接口

- `create_session(user_id, session_id, title)`
- `get_user_sessions(user_id)` → 按 `updated_at` 降序
- `get_session_messages(session_id)` → 按 `created_at` 升序
- `save_message(session_id, role, content, tool_calls)`
- `update_session_title(session_id, title)` — 取首条消息前 20 字
- `delete_session(session_id, user_id)` — 删除会话及其所有消息

---

## 6. 配置文件

### `.env.example`

```ini
# ---- DashScope LLM ----
DASHSCOPE_API_KEY=sk-your-key-here
LLM_MODEL=qwen3.7-max
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096

# ---- Server ----
AGENT_HOST=0.0.0.0
AGENT_PORT=8090

# ---- Backend Spring Boot API ----
BACKEND_BASE_URL=http://localhost:8080/api/user

# ---- Database ----
DATABASE_URL=sqlite:///agent.db

# ---- Agent Runtime ----
AGENT_MAX_ITERATIONS=5
WS_HEARTBEAT_INTERVAL=30
```

### `app/config.py`

`Settings` dataclass，将 `.env` 值转为类型安全字段，全局单例。

---

## 7. 文件结构

```
backend/agent/
├── .env                          # 实际配置 (gitignore)
├── .env.example                  # 配置模板 (git tracked)
├── requirements.txt
├── main.py                       # FastAPI 入口 + WebSocket 路由
├── app/
│   ├── __init__.py
│   ├── config.py                 # Settings 统一配置
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py               # AgentExecutor 初始化 (create_react_agent)
│   │   ├── tools.py              # 10 个 @tool 定义
│   │   └── prompt.py             # System prompt
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py           # SQLite 连接 + 初始化建表
│   │   └── models.py             # CRUD 方法
│   └── chat/
│       ├── __init__.py
│       ├── manager.py            # WebSocket 连接管理 + 心跳
│       └── protocol.py           # 消息协议 dataclass 定义
```

---

## 8. 前端组件

### 组件树

```
App.vue / MainLayout.vue
  └─ ChatWidget.vue                    ← 容器，管理 WebSocket
       ├─ FAB 按钮 (右下角固定)
       └─ 侧滑面板
            ├─ ChatSessionList.vue     ← 左侧会话列表
            ├─ ChatMessageList.vue      ← 消息展示（流式支持）
            └─ ChatInput.vue            ← 输入框 + 4 个快捷提问按钮
```

### 组件职责

**ChatWidget.vue**
- WebSocket 连接/断开生命周期（打开面板 → 连接，关闭面板 → 断开）
- 连接状态跟踪（`connecting` / `connected` / `disconnected` / `error`）
- 透传 JWT Token（从 auth store 拿）
- 消息分发给子组件

**ChatSessionList.vue**
- `list_sessions` 渲染
- 点击切换 session → `load_history`
- 新建会话按钮 → `new_session`
- 删除会话 → `delete_session`

**ChatMessageList.vue**
- 消息区域，自动滚动到底部
- 流式输出：`type: "token"` 逐字追加到当前消息末尾
- Markdown 渲染（消息完成时）
- 错误状态 + 重试按钮

**ChatInput.vue**
- 文本输入框 + Enter 发送
- 4 个快捷提问按钮（"推荐这季度热门番" / "今晚有什么更新" / "评分最高的番" / "热血战斗番推荐"）
- 发送中禁用输入

### 状态矩阵

| 状态 | ChatWidget | ChatSessionList | ChatMessageList | ChatInput |
|------|-----------|----------------|----------------|-----------|
| 连接中 | spinner | 隐藏 | 隐藏 | 隐藏 |
| 连接成功 + 无会话 | — | 空态提示 | 欢迎语 + 快捷问 | 可用 |
| 连接成功 + 有会话 | — | 列表 | 上次对话 | 可用 |
| 发送中 | — | 禁用 | 流式动画 | 禁用+发送中 |
| 完成 | — | 刷新列表 | 完整渲染 | 可用 |
| 出错 | — | — | 红色提示 | 可用 |
| 连接断开 | 显示"已断开" | 禁用 | 禁用 | 禁用 |

---

## 9. 无状态认证流程

```
[客户端] ws.connect(ws://localhost:8090/ws/chat?token=<JWT>)
    ↓
[Agent] 调 GET http://localhost:8080/api/user/me
    ├─ 200 → 取出 userId, 存入 ws 对象上下文, 返回连接成功
    └─ 401 → 断开连接, 返回认证失败

[每次消息]
Agent 从 ws 上下文取 userId, 不需要再次调 Spring Boot

[ws 断开]
清理内存中的 userId, 释放连接
```

---

## 10. 被排除的中间件

| 组件 | 排除理由 |
|------|----------|
| Kafka | 个人项目，单消费者，无削峰填谷需求 |
| MongoDB | SQLite 两张表即可承载聊天记录 |
| Elasticsearch | 现有 MySQL LIKE + LLM 理解能力已够 |
| Milvus | qwen3.7-max 本身具备动漫知识，不需要向量检索 |
| Neo4j | LLM 训练数据已包含番剧关联知识 |
| Agent 侧 Redis | 无缓存/限流/队列需求（项目原有 Redis 留给 Spring Boot 认证用） |

---

## 11. 最终交付清单

### 后端 Agent 服务
- [ ] `backend/agent/` — FastAPI + LangChain 1.3+ 项目结构
- [ ] `.env.example` + `config.py`
- [ ] `requirements.txt`
- [ ] 10 个 Tool 定义
- [ ] ReAct Agent 初始化
- [ ] WebSocket 连接管理 + 心跳
- [ ] SQLite 数据持久化

### 前端
- [ ] `ChatWidget.vue` + 3 个子组件
- [ ] WebSocket 连接/状态管理
- [ ] 流式消息渲染
- [ ] 快捷提问功能
