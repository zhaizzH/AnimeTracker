---
name: agent-module-refactor
description: 基于 Python + FastAPI + LangChain + LangGraph + Pydantic 重构 AnimeTracker AI Agent 模块的设计文档
---

# Agent 模块重构设计

> 基于 Python + FastAPI + LangChain + LangGraph + Pydantic 重构 AnimeTracker AI 追番助手

## 1. 概述

### 1.1 目标
将现有的 Agent 模块（Python FastAPI + LangChain AgentExecutor + WebSocket）重构为基于 **LangGraph StateGraph** 的多 Agent 路由架构，支持角色感知、意图路由、SSE 流式推送。

### 1.2 技术栈
| 组件 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.11+ |
| Web 框架 | FastAPI | >=0.110.0 |
| Agent 框架 | LangChain + LangGraph | langchain>=1.3,<2.0 / langgraph>=0.2.0 |
| 数据模型 | Pydantic | v2 |
| 存储 | SQLite (WAL mode) | — |
| LLM | DashScope (通义千问) | langchain-community ChatTongyi |
| HTTP 客户端 | httpx | >=0.27.0 |
| 通信协议 | SSE (text/event-stream) | — |

### 1.3 当前问题
- 单 AgentExecutor 结构，所有工具在一个 Agent 中，角色无感知
- 使用 WebSocket 通信，前端集成复杂度高
- 代码平铺无分层，扩展新能力需修改核心代码
- 配置硬编码，SQLite 无连接管理

### 1.4 设计原则
- **职责分离**：API / Graph / Tools / DB / Service 各层独立
- **可扩展**：新增 Agent = 注册节点 + 路由条件边，不改核心逻辑
- **渐进式迁移**：先重构后端，再更新前端 store 层，无中断窗口
- **测试优先**：LLM 和 HTTP 均可 mock，核心逻辑全覆盖

## 2. 系统架构

### 2.1 整体架构

```
┌───────────────────────────────────────────┐
│             前端 (AnimeTracker)             │
│  ┌─────────────────────────────────────┐  │
│  │         ChatStore (frontend)         │  │
│  │  WebSocket → SSE 客户端适配          │  │
│  │  fetch('/api/chat/sessions') REST   │  │
│  │  EventSource('/api/chat/stream')    │  │
│  └──────────────┬──────────────────────┘  │
└─────────────────┼─────────────────────────┘
                  │ POST /api/chat/stream  (Bearer JWT)
                  │ SSE text/event-stream
                  ▼
┌──────────────────────────────────────────────┐
│              FastAPI Server (:8090)           │
│                                               │
│  ┌──────────┐   ┌─────────────────────────┐  │
│  │ verify_   │   │  ChatService            │  │
│  │ token     │   │  (编排引擎)              │  │
│  │ (httpx →  │   │  - load history         │  │
│  │  Spring   │   │  - execute graph        │  │
│  │  Boot     │   │  - stream SSE           │  │
│  │  /api/    │   │  - save messages        │  │
│  │  user/me) │   └──────────┬──────────────┘  │
│  └──────────┘              │                  │
│                            ▼                  │
│  ┌─────────────────────────────────────────┐  │
│  │           Router Graph                   │  │
│  │                                          │  │
│  │   entry → role_router                    │  │
│  │     ├── user → intent_router             │  │
│  │     │    ├── search_agent                │  │
│  │     │    ├── discover_agent              │  │
│  │     │    └── recommend_agent             │  │
│  │     └── admin → admin_router             │  │
│  │          ├── admin_agent (Phase 2)       │  │
│  │          └── denied (当前无权限拒绝)      │  │
│  └──────────────────┬──────────────────────┘  │
└─────────────────────┼────────────────────────┘
                      │
                      ▼
              SSE event stream
```

### 2.2 部署拓扑

```
                        Nginx / 网关
                     ┌──────────┐
                     │ 反向代理   │
                     │ /api/chat/* → agent:8090     │
                     │ /api/user/* → backend:8080    │
                     │ /api/admin/* → backend:8080   │
                     └──────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        Agent (:8090)  Backend (:8080)  Frontend (:5173)
        FastAPI        Spring Boot      Vite + Vue
        SQLite         MySQL + Redis
```

**说明**：Agent 服务独立部署，通过 Nginx 同域反代，与 Spring Boot 共享 `/api/*` 路径空间。Agent 无状态可水平扩展，SQLite 当前单实例部署，后续切换 MySQL 时需改为共享存储。

## 3. 认证与授权设计

### 3.1 JWT 验证流程

Agent 不独立验证 JWT，而是委托 Spring Boot 后端验证：

```
客户端                         Agent                          Spring Boot
  │                              │                              │
  │ POST /api/chat/stream        │                              │
  │ Authorization: Bearer <jwt>  │                              │
  │─────────────────────────────►│                              │
  │                              │ GET /api/user/me             │
  │                              │ Authorization: Bearer <jwt>  │
  │                              │─────────────────────────────►│
  │                              │ 200 { id, username, role }   │
  │                              │◄─────────────────────────────│
  │                              │                              │
  │ 验证通过 → 创建 SSE 流        │                              │
  │◄─────────────────────────────│                              │
```

### 3.2 UserInfo 模型

```python
class UserInfo(BaseModel):
    user_id: int
    username: str
    role: Literal["USER", "ADMIN"]

class AuthResult(BaseModel):
    ok: bool
    user: UserInfo | None = None
    error: str | None = None
```

### 3.3 Token 过期处理

| 场景 | Agent 行为 |
|------|-----------|
| JWT 过期 (401) | 返回 SSE `event: error` + message "登录已过期，请重新登录" |
| 后端不可用 (5xx/网络异常) | 返回 SSE `event: error` + message "认证服务暂时不可用，请稍后重试" |
| 无效 token | 返回 SSE `event: error` + message "认证失败" |

## 4. API 层与通信协议

### 4.1 端点定义

| 方法 | 路径 | Auth | 说明 |
|------|------|------|------|
| POST | `/api/chat/stream` | 是 | 发送消息，返回 SSE 流 |
| GET | `/api/chat/sessions` | 是 | 获取当前用户会话列表 |
| POST | `/api/chat/sessions` | 是 | 创建新会话 |
| GET | `/api/chat/sessions/{id}/history` | 是 | 获取会话历史消息 |
| DELETE | `/api/chat/sessions/{id}` | 是 | 删除会话 |
| GET | `/api/chat/health` | 否 | 健康检查 |

### 4.2 请求/响应 Schema

```python
# ===== 会话管理 (REST) =====

# POST /api/chat/stream
class ChatRequest(BaseModel):
    session_id: str                # 前端生成 UUID
    content: str = Field(..., min_length=1, max_length=4096)

# POST /api/chat/sessions
class SessionCreateRequest(BaseModel):
    session_id: str | None = None  # 不传则后端生成

class SessionCreateResponse(BaseModel):
    session_id: str

# GET /api/chat/sessions
class SessionInfo(BaseModel):
    session_id: str
    title: str
    message_count: int
    created_at: datetime

# GET /api/chat/sessions/{id}/history
class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[str] | None
    created_at: datetime

# DELETE /api/chat/sessions/{id}
class DeleteResponse(BaseModel):
    message: str = "deleted"
```

### 4.3 SSE 事件协议

完整的 SSE 事件列表：

| event 类型 | 说明 | 触发时机 | data payload |
|-----------|------|---------|-------------|
| `token` | 逐 token 推送 | LLM 流式输出每个 token | `{"content": "推荐"}` |
| `metadata` | 元数据 | Graph 执行完毕，保存消息前 | `{"session_id": "xxx", "used_tools": ["search_subjects"]}` |
| `done` | 完成 | 全部处理完毕，流关闭前 | `{"session_id": "xxx"}` |
| `error` | 错误 | 任何阶段发生不可恢复错误 | `{"message": "处理请求时出错，请重试"}` |

**错误场景对应：**

| data.message | 触发条件 |
|-------------|---------|
| "认证失败，请重新登录" | JWT 无效或过期 |
| "认证服务暂时不可用，请稍后重试" | Spring Boot 后端不可达 |
| "处理请求时出错，请重试" | LLM 调用超时 / Graph 执行异常 |
| "请求参数错误" | ChatRequest 校验失败 |
| "会话不存在或无权限" | session_id 不属于当前用户 |

### 4.4 WebSocket → SSE 迁移对照

| 旧协议 (WebSocket JSON) | 新协议 (SSE / REST) |
|------------------------|-------------------|
| `{"type":"message", "content":"..."}` | `POST /api/chat/stream` + SSE token 流 |
| `{"type":"new_session"}` | `POST /api/chat/sessions` |
| `{"type":"list_sessions"}` | `GET /api/chat/sessions` |
| `{"type":"load_history", "session_id":"..."}` | `GET /api/chat/sessions/{id}/history` |
| `{"type":"delete_session", "session_id":"..."}` | `DELETE /api/chat/sessions/{id}` |
| `{"type":"ping"}` / `pong` | 移除（SSE 由 HTTP 管理连接） |

**前端迁移要点**：
- 用 `EventSource` 替代 `WebSocket` 接收流式响应
- 会话管理操作从 WebSocket 消息改为 `fetch` REST 调用
- 移除心跳逻辑
- 重连策略从 WebSocket `onclose` + 定时重连改为 HTTP 请求级重试

```typescript
// 前端 SSE 客户端示例
function streamChat(sessionId: string, content: string) {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, content }),
  });
  const reader = response.body.getReader();
  // 逐 chunk 读取 SSE 事件
}
```

## 5. 路由架构

### 5.1 Graph State 定义

```python
class AgentState(BaseModel):
    """Router Graph 运行时状态"""
    messages: list[BaseMessage]       # LangChain BaseMessage 列表
    user: UserInfo                    # 当前用户信息
    next_agent: str | None = None     # 路由目标 Agent 名称
    final_output: str = ""            # 最终回复文本
    used_tools: list[str] = []        # 本次调用使用到的工具名

class SubAgentState(BaseModel):
    """Sub-agent 内部 ReAct 循环状态"""
    messages: list[BaseMessage]
    is_done: bool = False
    output: str = ""
    used_tools: list[str] = []
```

### 5.2 第一层路由：角色分发

```
entry_node → role_router (条件边)
  ├── role == "USER" → user_router
  ├── role == "ADMIN" → admin_router
  └── 未知 → denied_node
```

- `entry_node`：解析 `UserInfo`，加载会话历史，转为 `BaseMessage` 列表
- `role_router`：纯逻辑判断，不调用 LLM
- `denied_node`：返回 SSE error，无权限提示

### 5.3 第二层路由：意图分发

`user_router` 是一个 LLM 节点，调用 ChatTongyi 判断用户意图：

```python
ROUTER_PROMPT = """你是 AnimeTracker 的意图路由助手。根据用户的问题选择最合适的 Agent：

- search: 精确查询 — 搜索番剧、查详情、查剧集、查标签、按标签筛选
- discover: 发现探索 — 热度榜、评分榜、按季度/星期查询、本周更新、统计
- recommend: 推荐（当前直接回复推荐结果，不调用工具）

用户角色: {role}
历史消息: {history_summary}

只输出一个单词：search / discover / recommend

用户问题: {query}
"""

# 条件边
def intent_router(state: AgentState) -> str:
    return state.next_agent  # 必须匹配注册的节点名
```

**消歧规则**：当问题同时匹配多个意图时：
- 包含"推荐/安利/有什么好看的" → recommend
- 包含"搜索/查/找/有没有" + 具体番剧名 → search
- 包含"本周/今天/季度/排行/热门/评分最高" → discover
- 默认 → search（查询优先）

### 5.4 ADMIN 路由

当前 ADMIN 路径仅提供拒绝提示。后续 Phase 2 在此处添加 `admin_router` 和 `admin_agent`。

```python
ADMIN_DENIED_PROMPT = """你是 AnimeTracker 的管理助手。

当前用户 {username} 是你自己（管理员），但管理端 Agent 功能尚未启用。
请回复：管理功能正在开发中，请直接在管理后台操作。
"""
```

## 6. Sub-agent 设计

### 6.1 工厂函数

```python
def create_sub_agent(
    name: str,
    tools: list[BaseTool],
    system_prompt: str,
    llm: BaseChatModel,         # 由外层传入，复用统一 LLM 实例
    max_iterations: int = 5,
) -> CompiledStateGraph:
```

**说明**：
- LLM 实例由 Router Graph 的外层传入，Sub-agent 不创建自己的 LLM
- `max_iterations` 可通过 `.env` 的 `AGENT_MAX_ITERATIONS` 配置

### 6.2 内部 ReAct 循环

```
agent_node ─── should_continue ─── tools_node
     ▲               │                  │
     └───────────────┘                  │
     (结果追加到 messages)               │
     ▲                                  │
     └──────────────────────────────────┘
     (工具结果追加到 messages)
```

```python
async def call_agent(state: SubAgentState) -> dict:
    """LLM 节点：判断是否需要调用工具"""
    llm_with_tools = llm.bind_tools(tools)
    response = await llm_with_tools.ainvoke([
        SystemMessage(system_prompt),
        *state.messages[-10:],  # 最近上下文窗口
    ])
    if not response.tool_calls:
        return {"output": response.content, "is_done": True}
    return {"messages": [response], "is_done": False}

async def call_tools(state: SubAgentState) -> dict:
    """工具节点：并行执行所有工具调用"""
    tool_map = {t.name: t for t in tools}
    tasks = []
    for tc in state.messages[-1].tool_calls:
        tool = tool_map.get(tc["name"])
        if tool:
            tasks.append(tool.ainvoke(tc["args"]))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    tool_results = []
    for tc, result in zip(state.messages[-1].tool_calls, results):
        if isinstance(result, Exception):
            content = f"工具 {tc['name']} 调用失败: {str(result)}"
        else:
            content = str(result)
        tool_results.append(ToolMessage(content, tool_call_id=tc["id"]))
    return {"messages": tool_results, "used_tools": [tc["name"] for tc in state.messages[-1].tool_calls]}

def should_continue(state: SubAgentState) -> str:
    """条件边：继续工具循环或结束"""
    if state.is_done:
        return "finish"
    if len(state.messages) >= max_iterations * 2:
        return "finish"  # 超限保护
    return "continue"
```

### 6.3 Sub-agent 状态与 Router Graph 状态的关系

```
┌─────────────────────────────────────────────┐
│              Router Graph State              │
│  AgentState {                                │
│    messages: list[BaseMessage],              │
│    user: UserInfo,                           │
│    next_agent: str,                          │
│    final_output: str,                        │
│    used_tools: list[str]                     │
│  }                                           │
└──────────┬──────────────────────────────────┘
           │ Sub-agent 调用
           ▼
┌─────────────────────────────────────────────┐
│           Sub-agent Internal State          │
│  SubAgentState {                             │
│    messages: list[BaseMessage],  ← 共享引用  │
│    is_done: bool,                            │
│    output: str,       → 写回 final_output    │
│    used_tools: list   → 合并到父级           │
│  }                                           │
└─────────────────────────────────────────────┘
```

**交互方式**：当 Router Graph 的节点调用 Sub-agent 时，传入 `AgentState.messages` 的子集（最近 N 轮），Sub-agent 运行完毕后将 `output` 和 `used_tools` 写回父状态。

### 6.4 Sub-agent 与 System Prompts

| Sub-agent | 工具 | 职责 |
|-----------|------|------|
| **search_agent** | `search_subjects`, `get_subject_detail`, `get_episodes`, `get_tags`, `get_subjects_by_tag` | 精确查询：搜索番剧、详情、剧集、标签 |
| **discover_agent** | `get_schedule`, `get_season_subjects`, `get_popular_subjects`, `get_top_rated`, `get_stats` | 发现探索：榜单、日程、季度新番、统计 |
| **recommend_agent** | 当前不调用工具，直接基于已有知识推荐（Phase 2 接入用户收藏数据） | 个性化推荐 |

**注意**：`recommend_agent` 当前阶段不独立调用工具，而是基于 query 和上下文直接生成推荐。其工具列表在 Phase 2 用户收藏功能上线后扩展。

### 6.5 Sub-agent 错误处理

Sub-agent 内部不 catch 异常，将异常向上抛出到 Router Graph 层面统一处理：

| 异常类型 | 处理方式 |
|---------|---------|
| LLM 调用超时 | Router Graph catch → SSE error "处理超时" |
| 工具调用 HTTP 401/403 | 工具返回错误消息，LLM 重新组织回复告知用户 |
| 工具调用 HTTP 5xx | 工具返回错误消息，LLM 告知用户服务暂时不可用 |
| 工具调用网络异常 | 同上 |
| 超过 max_iterations | should_continue 强制结束，LLM 基于已有结果回复 |

## 7. 工具层设计

### 7.1 Backend Base URL

旧配置 `BACKEND_BASE_URL=http://localhost:8080/api/user` 硬编码了 user 路径前缀，无法调用 admin 端点。

**新配置**：

```python
# app/config.py
class Settings(BaseSettings):
    # Backend API — 去掉路径后缀，工具调用时自行拼接
    backend_base_url: str = "http://localhost:8080"
```

```python
# app/tools/user_tools.py
BASE = settings.backend_base_url  # http://localhost:8080

@tool
def search_subjects(query: str, page: int = 1, size: int = 20) -> list:
    """按关键词搜索番剧"""
    resp = httpx.get(f"{BASE}/api/user/subjects/search", params={...}, timeout=10)
    ...

# app/tools/admin_tools.py (预留)
@tool
def run_import() -> str:
    """触发番剧导入"""
    resp = httpx.post(f"{BASE}/api/admin/import/run", ...)
```

### 7.2 用户侧工具（当前 10 个）

保持与旧版相同的 10 个工具函数，全部通过 Pydantic `@tool` 装饰器定义：

| 工具 | 端点路径 | 说明 |
|------|---------|------|
| `search_subjects` | `GET /api/user/subjects/search` | 关键词搜索番剧 |
| `get_subject_detail` | `GET /api/user/subjects/{id}` | 番剧详情 |
| `get_episodes` | `GET /api/user/subjects/{id}/episodes` | 剧集列表 |
| `get_schedule` | `GET /api/user/subjects/schedule` | 每周追番日程 |
| `get_season_subjects` | `GET /api/user/subjects/season` | 季度新番 |
| `get_popular_subjects` | `GET /api/user/subjects` + sort=collectionTotal | 热度榜 |
| `get_top_rated` | `GET /api/user/subjects` + sort=score | 评分榜 |
| `get_tags` | `GET /api/user/tags` | 标签列表 |
| `get_subjects_by_tag` | `GET /api/user/tags/{tag}/subjects` | 按标签筛选 |
| `get_stats` | `GET /api/user/subjects` + size=1 | 统计数据 |

### 7.3 工具错误处理

所有工具函数统一使用 `try/except` 包裹，异常时返回结构化错误消息：

```python
def _safe_call(func):
    """工具调用包装器：统一处理 HTTP 异常"""
    try:
        return func()
    except httpx.TimeoutException:
        return {"error": True, "message": "后端服务超时"}
    except httpx.HTTPStatusError as e:
        return {"error": True, "message": f"后端返回错误: {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"error": True, "message": "后端服务不可用"}
```

## 8. 数据层

### 8.1 数据模型定义

`app/db/models.py` — 数据层 Pydantic 模型（与数据库记录一一对应）：

```python
class Session(BaseModel):
    session_id: str
    user_id: int
    title: str = "新对话"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    message_count: int = 0

class Message(BaseModel):
    id: int | None = None
    session_id: str
    role: str          # "user" | "assistant"
    content: str
    tool_calls: str | None = None  # JSON string
    created_at: datetime = Field(default_factory=datetime.now)
```

**注意**：`app/db/models.py` 是数据层模型，与 `app/schemas/` 中的 API 层模型职责分离。API 层可能包含数据层不存在的字段（如 `UserInfo`），而数据层可能包含 API 层不暴露的字段（如 `id`）。两者各自独立，通过 `.model_dump()` 和构造方法转换。

### 8.2 ChatStore 接口与实现

```python
from abc import ABC, abstractmethod

class ChatStore(ABC):
    """存储接口 —— 当前只有 SQLite 实现，后续可替换为 MySQL"""
    @abstractmethod
    def init_db(self): ...
    @abstractmethod
    def create_session(self, user_id: int, session_id: str, title: str = "新对话"): ...
    @abstractmethod
    def get_user_sessions(self, user_id: int) -> list[Session]: ...
    @abstractmethod
    def get_messages(self, session_id: str) -> list[Message]: ...
    @abstractmethod
    def save_message(self, session_id: str, role: str, content: str, tool_calls: str | None = None): ...
    @abstractmethod
    def delete_session(self, session_id: str, user_id: int): ...
```

### 8.3 SQLite 实现

```python
class SQLiteStore(ChatStore):
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")  # SQLite 并发写等待 5s
        return conn
```

**并发说明**：`busy_timeout=5000` 使 SQLite 在写冲突时等待最多 5 秒而非立即报错。当前单实例部署场景下，少量用户并发聊天可正常运行。后续用户量增长时切换到 MySQL 实现。

### 8.4 旧数据兼容性

新 SQLite 数据库表结构与旧版完全一致。旧的 `agent.db` 文件可以直接复制到新项目的运行目录使用，无需迁移脚本。

## 9. 服务编排流程

```
POST /api/chat/stream
  │
  ├── 1. JWT 认证
  │     ├── 从 Authorization Header 提取 Bearer token
  │     ├── httpx GET → Spring Boot /api/user/me
  │     ├── 成功 → 解析 UserInfo
  │     └── 失败 → SSE event: error → 关闭
  │
  ├── 2. 检查会话权限
  │     ├── session_id 是否存在？如果存在，验证 user_id 匹配
  │     └── 不匹配 → SSE event: error "会话不存在或无权限"
  │
  ├── 3. 保存用户消息到 SQLite
  │     └── Message(role="user", content=...)
  │
  ├── 4. 加载会话历史
  │     ├── 从 SQLite 读取该 session_id 所有消息
  │     ├── 转为 LangChain BaseMessage 列表
  │     └── 截取最近 50 条消息作为上下文
  │
  ├── 5. 自动标题生成（首条消息）
  │     └── content[:20] → 更新 session.title
  │
  ├── 6. 创建 SSE StreamingResponse
  │     ├── media_type = "text/event-stream"
  │     ├── Cache-Control: no-cache
  │     ├── Connection: keep-alive
  │     └── X-Accel-Buffering: no
  │
  ├── 7. 执行 Router Graph (astream_events)
  │     ├── 传入 initial_state
  │     └── 逐事件处理：
  │         ├── on_chat_model_stream → token event
  │         ├── on_tool_start → 记录工具名
  │         └── 异常 → SSE error event
  │
  ├── 8. Graph 执行完毕
  │     ├── 推送 SSE metadata event (session_id, used_tools)
  │     ├── 保存助手回复
  │     └── 推送 SSE done event
  │
  └── 9. 清理 & 关闭
        ├── 取消 asyncio task（客户端断连时）
        └── 关闭 StreamingResponse
```

### 9.1 客户端断连处理

```python
async def event_stream():
    try:
        async for event in graph.astream_events(...):
            yield ...
    except asyncio.CancelledError:
        # 客户端断开连接 → 取消 Graph 执行
        logger.info("Client disconnected, cancelling graph")
    finally:
        # 确保已生成的内容已保存
        ...
```

FastAPI 在客户端断连时会自动取消 StreamingResponse 的异步生成器（发送 `CancelledError`）。

## 10. 配置与部署

### 10.1 配置分层

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM
    dashscope_api_key: str = ""
    llm_model: str = "qwen3.7-max"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096

    # Server
    agent_host: str = "0.0.0.0"
    agent_port: int = 8090

    # Backend API
    backend_base_url: str = "http://localhost:8080"

    # Database
    database_url: str = "sqlite:///agent.db"

    # Agent Runtime
    agent_max_iterations: int = 5

    # CORS (开发环境)
    cors_origins: list[str] = ["http://localhost:5173"]
```

### 10.2 .env 模板

```bash
# ---- DashScope LLM ----
DASHSCOPE_API_KEY=sk-your-key-here
LLM_MODEL=qwen3.7-max
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096

# ---- Server ----
AGENT_HOST=0.0.0.0
AGENT_PORT=8090

# ---- Backend Spring Boot API ----
BACKEND_BASE_URL=http://localhost:8080

# ---- Database ----
DATABASE_URL=sqlite:///agent.db

# ---- Agent Runtime ----
AGENT_MAX_ITERATIONS=5

# ---- CORS ----
CORS_ORIGINS=["http://localhost:5173"]
```

### 10.3 健康检查

```python
@router.get("/api/chat/health")
async def health():
    return {"status": "ok", "llm_configured": bool(settings.dashscope_api_key)}
```

### 10.4 CORS 配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 10.5 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8090
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
```

## 11. 项目文件结构

```
backend/agent/
├── main.py                          # FastAPI 入口 + lifespan
├── requirements.txt                 # 依赖清单
├── .env.example                     # 环境变量模板
├── Dockerfile                       # 容器化部署
│
├── app/
│   ├── __init__.py
│   │
│   ├── config.py                    # Pydantic Settings
│   │
│   ├── api/                         # API 层
│   │   ├── __init__.py
│   │   ├── chat.py                  # /api/chat/* 端点
│   │   └── deps.py                  # 依赖注入 (verify_token, get_store, get_service)
│   │
│   ├── graph/                       # LangGraph 定义
│   │   ├── __init__.py
│   │   ├── state.py                 # AgentState, SubAgentState
│   │   ├── graph.py                 # Router Graph 构建
│   │   ├── sub_agent.py             # Sub-agent 工厂 + ReAct Loop
│   │   ├── nodes.py                 # entry, router, denied, collector
│   │   └── prompts.py               # 所有 System Prompt
│   │
│   ├── tools/                       # 工具层
│   │   ├── __init__.py
│   │   ├── user_tools.py            # 10 个用户侧工具
│   │   └── admin_tools.py           # 管理侧工具（预留）
│   │
│   ├── llm/                         # LLM 层
│   │   ├── __init__.py
│   │   └── models.py                # create_llm() + ChatTongyi monkey-patch
│   │
│   ├── db/                          # 数据层
│   │   ├── __init__.py
│   │   ├── base.py                  # ChatStore ABC
│   │   ├── sqlite_store.py          # SQLiteStore 实现
│   │   └── models.py                # Session, Message Pydantic
│   │
│   ├── schemas/                     # API 请求/响应模型
│   │   ├── __init__.py
│   │   ├── chat.py                  # ChatRequest, SSE events
│   │   ├── session.py               # SessionInfo, MessageOut
│   │   └── auth.py                  # UserInfo, AuthResult
│   │
│   └── service/                     # 服务层
│       ├── __init__.py
│       └── chat.py                  # ChatService (编排核心)
│
└── tests/
    ├── __init__.py
    ├── conftest.py                  # pytest fixtures
    ├── test_api.py                  # API 端点测试
    ├── test_graph.py                # Router Graph / Sub-agent
    ├── test_tools.py                # 工具函数
    └── test_db.py                   # SQLite 存储
```

## 12. 已知技术事项

### 12.1 ChatTongyi monkey-patch

旧代码包含对 `ChatTongyi.subtract_client_response` 的 monkey-patch，用于解决 `langchain-community==0.4.2` 中流式 delta 合并 bug。新项目需在 `pip install` 后测试：

```python
# app/llm/models.py
def _patch_chat_tongyi():
    """修复 langchain-community ChatTongyi 流式响应的 delta 合并问题。
    如果上游修复则可移除。"""
    import json
    _orig = ChatTongyi.subtract_client_response
    def _patched(self, resp, prev_resp):
        # ... 同旧版 core.py 第 14-29 行
    ChatTongyi.subtract_client_response = _patched
```

需在目标 LangChain 版本（>=1.3,<2.0）中测试是否仍需此补丁。

### 12.2 LangGraph astream_events 事件类型

新设计使用 `StateGraph.astream_events(version="v2")`，订阅的事件类型：

| 事件 | 用途 |
|------|------|
| `on_chat_model_stream` | 提取 token content，推送 SSE |
| `on_tool_start` | 记录使用的工具名 |
| `on_chain_end` | 检测 Graph 完成（备用）|

## 13. 测试策略

| 层级 | 内容 | 工具 |
|------|------|------|
| **单元测试** | DB CRUD、SQLite 并发、会话隔离 | pytest |
| | Pydantic 模型序列化/校验 | pytest |
| | 工具函数入参/出参、HTTP 错误处理 | pytest + respx |
| **集成测试** | Router Graph：注入 mock LLM → 验证路由分发逻辑 | pytest + unittest.mock |
| | Sub-agent ReAct 循环：工具调用 → 结果聚合 → 超限终止 | pytest |
| | API 端点：SSE 流格式、session CRUD | pytest + httpx + respx |
| **Mock 策略** | LLM：`AsyncMock` 返回固定 `AIMessage` + `tool_calls` | unittest.mock |
| | HTTP：`respx` mock Spring Boot 端点 | respx |
| | DB：内存 SQLite (`file::memory:`) 每次测试隔离 | pytest fixture |

## 14. 扩展性设计

| 场景 | 操作步骤 |
|------|---------|
| 新增 Sub-agent | ① `prompts.py` 加 System Prompt → ② `nodes.py` 加节点函数 → ③ `graph.py` 注册节点 + 条件边 |
| 新增工具 | ① `user_tools.py` / `admin_tools.py` 加 `@tool` → ② 注入到对应 Sub-agent 的 tools 列表 |
| 启用 ADMIN Agent | ① `admin_tools.py` 实现工具 → ② `admin_agent` Sub-agent → ③ `intent_router` 加 admin 分支 |
| 切换 MySQL | ① 实现 `MySQLStore(ChatStore)` → ② 修改 `config.py` database_url → ③ 注入新 store 实例 |
| 添加用户收藏查询 | ① `user_tools.py` 加收藏相关工具 → ② `recommend_agent` tools 列表扩展 → ③ Prompt 加入收藏数据说明 |
