# AI 追番助手 Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 AnimeTracker 添加 AI 聊天助手功能，前端嵌入聊天窗口，后端以 Tool-based Agent 聚合推荐、搜索、问答、追番建议、数据查询等能力。

**Architecture:** FastAPI + LangChain 1.3+ 作为独立 Agent 服务（port 8090），通过 WebSocket 与前端通信，通过 Tool Calling 调用 Spring Boot 后端 API（port 8080）。聊天记录持久化到 SQLite。

**Tech Stack:** Python 3.11+, FastAPI, LangChain 1.3+ (ChatDashScope), httpx, SQLite, Vue 3, Pinia, TypeScript

## Global Constraints

- `backend/agent/` 目录已存在但为空——在此目录下创建全部文件
- LLM 使用 DashScope qwen3.7-max，通过 `langch
ain_community.chat_models.ChatDashScope` 集成
- WebSocket 连接时通过 URL query 传 JWT Token，Agent 调 Spring Boot `/api/user/me` 校验获取 userId（仅连接时一次）
- 前端 ChatWidget 放在 `App.vue`，所有页面全局可用
- 聊天记录存 SQLite（`sessions` + `messages` 两张表）
- 不引入 Kafka/MongoDB/ES/Milvus/Neo4j/Agent 侧 Redis
- 前端不加新 npm 依赖——使用原生 WebSocket API

---

## File Structure

```
backend/agent/
├── .env.example
├── requirements.txt
├── main.py                         # FastAPI 入口 + WebSocket 路由
├── app/
│   ├── __init__.py
│   ├── config.py                   # Settings 统一配置
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py                 # AgentExecutor 初始化
│   │   ├── tools.py                # 10 个 @tool 定义
│   │   └── prompt.py               # System prompt
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py             # SQLite 连接 + 建表
│   │   └── models.py               # CRUD 方法
│   ├── chat/
│   │   ├── __init__.py
│   │   ├── manager.py              # WebSocket 连接管理 + 心跳 + 认证
│   │   └── protocol.py             # 消息协议 dataclass
│   └── tests/
│       ├── __init__.py
│       ├── test_db.py
│       ├── test_protocol.py
│       ├── test_tools.py
│       └── test_ws.py
frontend/client/src/
├── types/index.ts                  # + ChatSession, ChatMessage 类型
├── stores/chat.ts                  # + 新建 Chat store
├── components/chat/
│   ├── ChatWidget.vue              # 容器：FAB + 面板 + WebSocket 生命周期
│   ├── ChatSessionList.vue         # 会话列表侧栏
│   ├── ChatMessageList.vue         # 消息展示 + 流式渲染
│   └── ChatInput.vue               # 输入框 + 快捷提问
├── layouts/MainLayout.vue          # 不变
└── App.vue                         # + ChatWidget 全局引入
```

---

### Task 1: Agent 项目脚手架

**Files:**
- Create: `backend/agent/.env.example`
- Create: `backend/agent/requirements.txt`
- Create: `backend/agent/app/__init__.py`
- Create: `backend/agent/app/config.py`
- Create: `backend/agent/app/agent/__init__.py`
- Create: `backend/agent/app/db/__init__.py`
- Create: `backend/agent/app/chat/__init__.py`

**Interfaces:**
- Produces: `Settings` dataclass 全局单例，其他模块通过 `from app.config import settings` 使用

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p backend/agent/app/{agent,db,chat,tests}
touch backend/agent/app/__init__.py
touch backend/agent/app/agent/__init__.py
touch backend/agent/app/db/__init__.py
touch backend/agent/app/chat/__init__.py
touch backend/agent/app/tests/__init__.py
```

- [ ] **Step 2: 编写 `.env.example`**

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

- [ ] **Step 3: 编写 `requirements.txt`**

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
langchain>=1.3.0
langchain-community>=1.3.0
langchain-core>=1.3.0
httpx>=0.27.0
python-dotenv>=1.0.0
websockets>=12.0
pytest>=8.0
respx>=0.21.0
```

- [ ] **Step 4: 编写 `app/config.py`**

```python
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # LLM
    dashscope_api_key: str = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""))
    llm_model: str = os.getenv("LLM_MODEL", "qwen3.7-max")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    # Server
    agent_host: str = os.getenv("AGENT_HOST", "0.0.0.0")
    agent_port: int = int(os.getenv("AGENT_PORT", "8090"))

    # Backend
    backend_base_url: str = os.getenv("BACKEND_BASE_URL", "http://localhost:8080/api/user")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///agent.db")

    # Agent runtime
    agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
    ws_heartbeat_interval: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))


settings = Settings()
```

- [ ] **Step 5: 验证**

```bash
cd backend/agent && python -c "from app.config import settings; print(settings.dashscope_api_key[:5] or 'empty, ok')"
```
Expected: `empty, ok`（.env 不存在，取默认空值）

- [ ] **Step 6: Commit**

```bash
git add backend/agent/
git commit -m "feat(agent): 项目脚手架 + 配置层"
```

---

### Task 2: 数据库层 — SQLite 连接与 CRUD

**Files:**
- Create: `backend/agent/app/db/database.py`
- Create: `backend/agent/app/db/models.py`
- Create: `backend/agent/app/tests/test_db.py`

**Interfaces:**
- Produces: `get_connection() -> sqlite3.Connection` — 返回带 Row factory 的连接
- Produces: `init_db()` — 创建 sessions + messages 表
- Produces: `create_session(user_id, session_id, title)` — 插入新会话
- Produces: `get_user_sessions(user_id) -> list[dict]` — 按 updated_at 降序，含 message_count
- Produces: `get_session_messages(session_id) -> list[dict]` — 按 created_at 升序
- Produces: `save_message(session_id, role, content, tool_calls=None)`
- Produces: `update_session_title(session_id, title)`
- Produces: `delete_session(session_id, user_id)` — 级联删除会话 + 消息
- Produces: `update_session_time(session_id)` — 更新 updated_at

- [ ] **Step 1: 编写 `database.py`**

```python
import sqlite3
import os
from app.config import settings


def _get_db_path() -> str:
    """从 database_url 中提取文件路径"""
    url = settings.database_url
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    return url


DB_PATH = _get_db_path()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated_at);
    """)
    conn.commit()
    conn.close()
```

- [ ] **Step 2: 编写 `models.py`**

```python
from app.db.database import get_connection


def create_session(user_id: int, session_id: str, title: str = ""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (session_id, user_id, title) VALUES (?, ?, ?)",
        (session_id, user_id, title),
    )
    conn.commit()
    conn.close()


def get_user_sessions(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.session_id, s.title, s.created_at, s.updated_at,
               (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.session_id) AS message_count
        FROM sessions s
        WHERE s.user_id = ?
        ORDER BY s.updated_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_messages(session_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, session_id, role, content, tool_calls, created_at FROM messages WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_message(session_id: str, role: str, content: str, tool_calls: str | None = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
        (session_id, role, content, tool_calls),
    )
    conn.commit()
    conn.close()


def update_session_title(session_id: str, title: str):
    conn = get_connection()
    conn.execute("UPDATE sessions SET title = ?, updated_at = datetime('now') WHERE session_id = ?", (title, session_id))
    conn.commit()
    conn.close()


def update_session_time(session_id: str):
    conn = get_connection()
    conn.execute("UPDATE sessions SET updated_at = datetime('now') WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def delete_session(session_id: str, user_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, user_id))
    conn.commit()
    conn.close()
```

- [ ] **Step 3: 编写测试 `tests/test_db.py`**

```python
import os
import pytest
from app.db.database import get_connection, init_db, DB_PATH
from app.db import models

@pytest.fixture(autouse=True)
def setup_db():
    """每个测试使用独立的临时数据库"""
    test_db = "/tmp/test_agent.db"
    original = DB_PATH
    import app.db.database as db_mod
    db_mod.DB_PATH = test_db
    init_db()
    yield
    db_mod.DB_PATH = original
    if os.path.exists(test_db):
        os.remove(test_db)


class TestDatabase:
    def test_init_creates_tables(self):
        conn = get_connection()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        names = [r["name"] for r in tables]
        assert "sessions" in names
        assert "messages" in names
        conn.close()

    def test_create_and_list_sessions(self):
        models.create_session(1, "sess-1", "测试会话")
        sessions = models.get_user_sessions(1)
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "sess-1"
        assert sessions[0]["title"] == "测试会话"
        assert sessions[0]["message_count"] == 0

    def test_messages_belong_to_session(self):
        models.create_session(1, "sess-1")
        models.save_message("sess-1", "user", "Hello")
        models.save_message("sess-1", "assistant", "Hi!")
        msgs = models.get_session_messages("sess-1")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_delete_session_cascades(self):
        models.create_session(1, "sess-1")
        models.save_message("sess-1", "user", "Hello")
        models.delete_session("sess-1", 1)
        assert models.get_session_messages("sess-1") == []
        assert models.get_user_sessions(1) == []

    def test_session_ordering(self):
        models.create_session(1, "sess-old", "旧的")
        import time; time.sleep(0.01)
        models.create_session(1, "sess-new", "新的")
        sessions = models.get_user_sessions(1)
        assert sessions[0]["session_id"] == "sess-new"

    def test_other_user_not_visible(self):
        models.create_session(1, "sess-1")
        models.create_session(2, "sess-2")
        assert len(models.get_user_sessions(1)) == 1
```

- [ ] **Step 4: 运行测试**

```bash
cd backend/agent && python -m pytest tests/test_db.py -v
```
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add backend/agent/app/db/ backend/agent/app/tests/
git commit -m "feat(agent): SQLite 数据库层 + CRUD"
```

---

### Task 3: 消息协议定义

**Files:**
- Create: `backend/agent/app/chat/protocol.py`
- Create: `backend/agent/app/tests/test_protocol.py`

**Interfaces:**
- Produces: `InboundMessage` — dataclass，客户端消息类型
- Produces: `OutboundMessage` — dataclass，服务端消息类型
- Produces: `to_dict()` 方法用于序列化

- [ ] **Step 1: 编写 `protocol.py`**

```python
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SessionInfo:
    session_id: str
    title: Optional[str] = None
    message_count: int = 0
    created_at: str = ""


@dataclass
class ChatMessage:
    role: str  # 'user' | 'assistant'
    content: str
    tool_calls: Optional[str] = None  # JSON string
    created_at: Optional[str] = None


# Client → Server
@dataclass
class ClientMessage:
    type: str  # message | new_session | load_history | list_sessions | delete_session | pong
    session_id: Optional[str] = None
    content: Optional[str] = None


# Server → Client
@dataclass
class ServerToken:
    type: str = "token"
    session_id: Optional[str] = None
    content: str = ""

    def to_dict(self):
        return {"type": self.type, "session_id": self.session_id, "content": self.content}


@dataclass
class ServerDone:
    type: str = "done"
    session_id: Optional[str] = None
    full_content: str = ""
    tool_calls: list[str] = field(default_factory=list)

    def to_dict(self):
        return {"type": self.type, "session_id": self.session_id, "full_content": self.full_content, "tool_calls": self.tool_calls}


@dataclass
class ServerError:
    type: str = "error"
    session_id: Optional[str] = None
    message: str = ""

    def to_dict(self):
        return {"type": self.type, "session_id": self.session_id, "message": self.message}


@dataclass
class ServerSessionList:
    type: str = "session_list"
    sessions: list[dict] = field(default_factory=list)

    def to_dict(self):
        return {"type": self.type, "sessions": self.sessions}


@dataclass
class ServerHistory:
    type: str = "history"
    session_id: Optional[str] = None
    messages: list[dict] = field(default_factory=list)

    def to_dict(self):
        return {"type": self.type, "session_id": self.session_id, "messages": self.messages}


@dataclass
class ServerPing:
    type: str = "ping"

    def to_dict(self):
        return {"type": self.type}
```

- [ ] **Step 2: 编写测试 `tests/test_protocol.py`**

```python
from app.chat.protocol import (
    ServerToken, ServerDone, ServerError,
    ServerSessionList, ServerHistory, ServerPing,
)


class TestProtocol:
    def test_token(self):
        d = ServerToken(session_id="s1", content="推荐").to_dict()
        assert d == {"type": "token", "session_id": "s1", "content": "推荐"}

    def test_done(self):
        d = ServerDone(session_id="s1", full_content="推荐完毕", tool_calls=["search"]).to_dict()
        assert d == {"type": "done", "session_id": "s1", "full_content": "推荐完毕", "tool_calls": ["search"]}

    def test_error(self):
        d = ServerError(session_id="s1", message="出错了").to_dict()
        assert d == {"type": "error", "session_id": "s1", "message": "出错了"}

    def test_session_list(self):
        d = ServerSessionList(sessions=[{"session_id": "s1", "title": "测试"}]).to_dict()
        assert d["type"] == "session_list"
        assert len(d["sessions"]) == 1

    def test_history(self):
        d = ServerHistory(session_id="s1", messages=[{"role": "user", "content": "hi"}]).to_dict()
        assert d["type"] == "history"
        assert len(d["messages"]) == 1

    def test_ping(self):
        d = ServerPing().to_dict()
        assert d == {"type": "ping"}
```

- [ ] **Step 3: 运行测试**

```bash
cd backend/agent && python -m pytest tests/test_protocol.py -v
```
Expected: 6 passed

- [ ] **Step 4: Commit**

```bash
git add backend/agent/app/chat/protocol.py backend/agent/app/tests/test_protocol.py
git commit -m "feat(agent): WebSocket 消息协议定义"
```

---

### Task 4: Tools — 10 个工具函数

**Files:**
- Create: `backend/agent/app/agent/tools.py`
- Create: `backend/agent/app/tests/test_tools.py`

**Interfaces:**
- Produces: `tools` — `list[Tool]`，10 个工具实例
- 每个工具通过 `@tool` 装饰器定义，调用 `settings.backend_base_url` + 具体路径

- [ ] **Step 1: 编写 `tools.py`**

```python
import httpx
from langchain_core.tools import tool
from app.config import settings

BASE = settings.backend_base_url


@tool
def search_subjects(query: str, page: int = 1, size: int = 20) -> list:
    """按关键词搜索番剧。query: 搜索关键词"""
    resp = httpx.get(f"{BASE}/subjects/search", params={"q": query, "page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_subject_detail(subject_id: int) -> dict:
    """获取番剧详细信息。subject_id: 番剧 ID"""
    resp = httpx.get(f"{BASE}/subjects/{subject_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


@tool
def get_episodes(subject_id: int) -> list:
    """获取番剧的剧集列表。subject_id: 番剧 ID"""
    resp = httpx.get(f"{BASE}/subjects/{subject_id}/episodes", timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


@tool
def get_schedule(weekday: int = -1, year: int = 0, quarter: str = "") -> dict:
    """按星期获取每周追番列表。weekday: 0=周日 1=周一 ... 6=周六，-1=全部；year: 年份，默认当前年；quarter: spring/summer/autumn/winter"""
    params = {"weekday": weekday, "page": 1, "size": 50}
    if year:
        params["year"] = year
    if quarter:
        params["quarter"] = quarter
    resp = httpx.get(f"{BASE}/subjects/schedule", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


@tool
def get_season_subjects(year: int, quarter: str, page: int = 1, size: int = 20) -> list:
    """按季度获取新番。year: 年份；quarter: spring/summer/autumn/winter"""
    resp = httpx.get(f"{BASE}/subjects/season", params={"year": year, "quarter": quarter, "page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_popular_subjects(page: int = 1, size: int = 10) -> list:
    """获取热度榜（按收藏数降序）"""
    resp = httpx.get(f"{BASE}/subjects", params={"sort": "collectionTotal", "order": "desc", "page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_top_rated(page: int = 1, size: int = 10) -> list:
    """获取评分榜（按评分降序）"""
    resp = httpx.get(f"{BASE}/subjects", params={"sort": "score", "order": "desc", "page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_tags() -> list:
    """获取所有标签（按使用次数降序）"""
    resp = httpx.get(f"{BASE}/tags", timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


@tool
def get_subjects_by_tag(tag: str, page: int = 1, size: int = 20) -> list:
    """按标签获取番剧。tag: 标签名称"""
    resp = httpx.get(f"{BASE}/tags/{tag}/subjects", params={"page": page, "size": size}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["content"]


@tool
def get_stats() -> dict:
    """获取番剧统计数据（总数等）"""
    resp = httpx.get(f"{BASE}/subjects", params={"page": 1, "size": 1}, timeout=10)
    resp.raise_for_status()
    data = resp.json()["data"]
    return {"total": data["total"], "page": data["page"], "size": data["size"]}


tools = [
    search_subjects,
    get_subject_detail,
    get_episodes,
    get_schedule,
    get_season_subjects,
    get_popular_subjects,
    get_top_rated,
    get_tags,
    get_subjects_by_tag,
    get_stats,
]
```

- [ ] **Step 2: 编写测试 `tests/test_tools.py`**

```python
import pytest
import respx
from httpx import Response
from app.agent.tools import (
    search_subjects, get_subject_detail, get_episodes,
    get_schedule, get_season_subjects, get_popular_subjects,
    get_top_rated, get_tags, get_subjects_by_tag, get_stats,
)
from app.config import settings

BASE = settings.backend_base_url


class TestTools:
    @respx.mock
    def test_search_subjects(self):
        route = respx.get(f"{BASE}/subjects/search").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1, "name": "Test"}], "total": 1}
        }))
        result = search_subjects.invoke({"query": "热血"})
        assert route.called
        assert result[0]["id"] == 1

    @respx.mock
    def test_get_subject_detail(self):
        respx.get(f"{BASE}/subjects/42").mock(Response(200, json={
            "code": 200, "data": {"id": 42, "name": "钢之炼金术师"}
        }))
        result = get_subject_detail.invoke({"subject_id": 42})
        assert result["name"] == "钢之炼金术师"

    @respx.mock
    def test_get_schedule(self):
        respx.get(f"{BASE}/subjects/schedule").mock(Response(200, json={
            "code": 200, "data": {"content": [], "total": 0}
        }))
        result = get_schedule.invoke({"weekday": 1})
        assert "content" in result

    @respx.mock
    def test_get_tags(self):
        respx.get(f"{BASE}/tags").mock(Response(200, json={
            "code": 200, "data": [{"name": "热血", "count": 50}]
        }))
        result = get_tags.invoke({})
        assert result[0]["name"] == "热血"

    @respx.mock
    def test_get_stats(self):
        respx.get(f"{BASE}/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [], "total": 500}
        }))
        result = get_stats.invoke({})
        assert result["total"] == 500

    @respx.mock
    def test_tool_http_error(self):
        respx.get(f"{BASE}/subjects/search").mock(Response(500))
        result = search_subjects.invoke({"query": "error"})
        # 工具异常时 @tool 会抛异常，让 LLM 处理
        assert result is None or "error" in str(result).lower()
```

- [ ] **Step 3: 运行测试**

```bash
cd backend/agent && python -m pytest tests/test_tools.py -v
```
Expected: 6 passed

- [ ] **Step 4: Commit**

```bash
git add backend/agent/app/agent/tools.py backend/agent/app/tests/test_tools.py
git commit -m "feat(agent): 10 个 Tool 定义 + 测试"
```

---

### Task 5: System Prompt

**Files:**
- Create: `backend/agent/app/agent/prompt.py`

**Interfaces:**
- Produces: `SYSTEM_PROMPT` — str，ReAct Agent 的 system prompt

- [ ] **Step 1: 编写 `prompt.py`**

```python
SYSTEM_PROMPT = """你是 AnimeTracker 的 AI 追番助手，帮助用户查找、推荐和了解动漫番剧。

回答规则：
1. 始终使用中文回答
2. 推荐番剧时给出简短的推荐理由
3. 回答要简洁，避免冗长
4. 如果不确定某个信息，请如实告知用户
5. 当用户问今天/本周有什么更新时，请查询追番日程

你有以下工具可用：
- search_subjects: 按关键词搜索番剧
- get_subject_detail: 获取番剧详细信息（简介、评分、标签等）
- get_episodes: 获取番剧剧集列表
- get_schedule: 按星期获取每周追番列表（weekday: 0=周日, -1=全部）
- get_season_subjects: 按季度获取新番
- get_popular_subjects: 获取热度榜（收藏数降序）
- get_top_rated: 获取评分榜（评分降序）
- get_tags: 获取所有标签
- get_subjects_by_tag: 按标签获取番剧
- get_stats: 获取番剧统计数据

当用户提出推荐请求时，先搜索或获取数据，然后结合数据给出有根据的推荐。"""
```

- [ ] **Step 2: 验证**

```bash
cd backend/agent && python -c "from app.agent.prompt import SYSTEM_PROMPT; print(len(SYSTEM_PROMPT), 'chars')"
```
Expected: 输出字符数（约 600+）

- [ ] **Step 3: Commit**

```bash
git add backend/agent/app/agent/prompt.py
git commit -m "feat(agent): System prompt"
```

---

### Task 6: Agent Core — AgentExecutor 初始化

**Files:**
- Create: `backend/agent/app/agent/core.py`

**Interfaces:**
- Consumes: `SYSTEM_PROMPT`, `tools` list, `settings`
- Produces: `create_agent_executor() -> AgentExecutor` — 初始化 ReAct Agent

- [ ] **Step 1: 编写 `core.py`**

```python
from langchain_community.chat_models import ChatDashScope
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.agent.tools import tools
from app.agent.prompt import SYSTEM_PROMPT

PROMPT_TEMPLATE = PromptTemplate.from_template(
    SYSTEM_PROMPT + "\n\n{chat_history}\nQuestion: {input}\n{agent_scratchpad}"
)


def create_agent_executor() -> AgentExecutor:
    llm = ChatDashScope(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        dashscope_api_key=settings.dashscope_api_key,
        streaming=True,
    )

    agent = create_react_agent(llm, tools, PROMPT_TEMPLATE)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=settings.agent_max_iterations,
        handle_parsing_errors=True,
        verbose=False,
    )
```

- [ ] **Step 2: 验证导入**

```bash
cd backend/agent && python -c "from app.agent.core import create_agent_executor; print('ok')"
```
Expected: `ok`（不需要 API key 验证——只在首次调用时请求 LLM）

- [ ] **Step 3: Commit**

```bash
git add backend/agent/app/agent/core.py
git commit -m "feat(agent): AgentExecutor 初始化"
```

---

### Task 7: WebSocket 连接管理器

**Files:**
- Create: `backend/agent/app/chat/manager.py`
- Create: `backend/agent/app/tests/test_ws.py`

**Interfaces:**
- Produces: `ConnectionManager` — 管理 WebSocket 连接、认证、心跳、消息分发
- Produces: `verify_token(token: str) -> int | None` — 调 Spring Boot 校验 JWT，返回 userId 或 None

- [ ] **Step 1: 编写 `manager.py`**

```python
import json
import asyncio
import logging
import httpx
from fastapi import WebSocket
from app.config import settings
from app.chat.protocol import (
    ClientMessage, ServerToken, ServerDone, ServerError,
    ServerSessionList, ServerHistory, ServerPing,
)
from app.db import models as db

logger = logging.getLogger(__name__)


async def verify_token(token: str) -> int | None:
    """调 Spring Boot /api/user/me 校验 JWT，返回 userId"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.backend_base_url.replace('/api/user', '/api/user')}/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json()["data"]["id"]
    except Exception as e:
        logger.warning(f"Token verify failed: {e}")
    return None


class ConnectionManager:
    def __init__(self, agent_executor):
        self.agent_executor = agent_executor
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}  # session_id -> task

    async def handle(self, ws: WebSocket):
        token = ws.query_params.get("token", "")
        user_id = await verify_token(token)
        if user_id is None:
            await ws.send_json(ServerError(message="认证失败，请重新登录").to_dict())
            await ws.close(code=4001)
            return

        await ws.accept()
        user_key = f"user_{user_id}"
        logger.info(f"User {user_id} connected")

        # 启动心跳
        heartbeat_task = asyncio.create_task(self._heartbeat(ws))
        self._heartbeat_tasks[user_key] = heartbeat_task

        try:
            await self._message_loop(ws, user_id)
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            heartbeat_task.cancel()
            self._heartbeat_tasks.pop(user_key, None)
            logger.info(f"User {user_id} disconnected")

    async def _heartbeat(self, ws: WebSocket):
        interval = settings.ws_heartbeat_interval
        try:
            while True:
                await asyncio.sleep(interval)
                await ws.send_json(ServerPing().to_dict())
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def _message_loop(self, ws: WebSocket, user_id: int):
        while True:
            raw = await ws.receive_json()
            msg = ClientMessage(**raw)

            if msg.type == "pong":
                continue

            if msg.type == "list_sessions":
                sessions = db.get_user_sessions(user_id)
                await ws.send_json(ServerSessionList(sessions=sessions).to_dict())
                continue

            if msg.type == "new_session":
                import uuid
                session_id = str(uuid.uuid4())
                db.create_session(user_id, session_id, "新对话")
                await ws.send_json(ServerDone(session_id=session_id, full_content="").to_dict())
                continue

            if msg.type == "load_history" and msg.session_id:
                messages = db.get_session_messages(msg.session_id)
                await ws.send_json(ServerHistory(session_id=msg.session_id, messages=messages).to_dict())
                continue

            if msg.type == "delete_session" and msg.session_id:
                db.delete_session(msg.session_id, user_id)
                await ws.send_json(ServerDone(session_id=msg.session_id, full_content="").to_dict())
                continue

            if msg.type == "message" and msg.session_id and msg.content:
                await self._handle_message(ws, user_id, msg.session_id, msg.content)

    async def _handle_message(self, ws: WebSocket, user_id: int, session_id: str, content: str):
        # 保存用户消息
        db.save_message(session_id, "user", content)

        # 新会话自动更新标题
        messages = db.get_session_messages(session_id)
        if len(messages) == 1:
            title = content[:20]
            db.update_session_title(session_id, title)

        db.update_session_time(session_id)

        # 构造 Agent 输入
        history = messages[:-1]  # 排除当前消息
        chat_history = ""
        for h in history:
            role = "Human" if h["role"] == "user" else "Assistant"
            chat_history += f"{role}: {h['content']}\n"

        # 收集使用的工具名
        used_tools = []
        full_content = ""

        try:
            async for event in self.agent_executor.astream_events(
                {"input": content, "chat_history": chat_history},
                version="v2",
            ):
                kind = event["event"]

                # 流式 LLM token
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        full_content += chunk.content
                        await ws.send_json(ServerToken(session_id=session_id, content=chunk.content).to_dict())

                # 跟踪 tool 调用
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    if tool_name and tool_name not in used_tools:
                        used_tools.append(tool_name)

        except Exception as e:
            logger.error(f"Agent error: {e}")
            await ws.send_json(ServerError(session_id=session_id, message="处理请求时出错，请重试").to_dict())
            return

        # 保存助手回复
        db.save_message(session_id, "assistant", full_content, json.dumps(used_tools) if used_tools else None)

        # 发送完成信号
        await ws.send_json(ServerDone(session_id=session_id, full_content=full_content, tool_calls=used_tools).to_dict())
```

- [ ] **Step 2: 编写测试 `tests/test_ws.py`**

```python
import pytest
from app.chat.manager import verify_token


@pytest.mark.asyncio
async def test_verify_token_invalid():
    """无效 token 返回 None"""
    user_id = await verify_token("invalid-token")
    assert user_id is None


@pytest.mark.asyncio
async def test_verify_token_no_backend():
    """后端不可用时返回 None"""
    user_id = await verify_token("some-token")
    assert user_id is None
```

- [ ] **Step 3: 运行测试**

```bash
cd backend/agent && python -m pytest tests/test_ws.py -v
```
Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add backend/agent/app/chat/manager.py backend/agent/app/tests/test_ws.py
git commit -m "feat(agent): WebSocket 连接管理器 + 认证 + 心跳"
```

---

### Task 8: FastAPI 入口

**Files:**
- Create: `backend/agent/main.py`

**Interfaces:**
- Produces: WebSocket 端点 `ws://localhost:8090/ws/chat`

- [ ] **Step 1: 编写 `main.py`**

```python
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.db.database import init_db
from app.agent.core import create_agent_executor
from app.chat.manager import ConnectionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

agent_executor = None
connection_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_executor, connection_manager
    logger.info("Initializing database...")
    init_db()
    logger.info("Creating agent executor...")
    agent_executor = create_agent_executor()
    connection_manager = ConnectionManager(agent_executor)
    yield
    logger.info("Shutting down...")


app = FastAPI(title="AnimeTracker Agent", version="1.0.0", lifespan=lifespan)


@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    try:
        await connection_manager.handle(ws)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run(
        "main:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=True,
    )
```

- [ ] **Step 2: 验证启动**

```bash
cd backend/agent && python -c "from main import app; print(f'FastAPI app: {app.title}')"
```
Expected: `FastAPI app: AnimeTracker Agent`

- [ ] **Step 3: Commit**

```bash
git add backend/agent/main.py
git commit -m "feat(agent): FastAPI 入口 + WebSocket 路由"
```

---

### Task 9: 前端 Chat 类型 + Store

**Files:**
- Modify: `frontend/client/src/types/index.ts` — 追加 ChatSession, ChatMessage 类型
- Create: `frontend/client/src/stores/chat.ts`

**Interfaces:**
- Produces: `ChatSession`, `ChatMessage` 接口类型
- Produces: `useChatStore` — Pinia store，管理 WebSocket 状态、会话列表、消息

- [ ] **Step 1: `types/index.ts` 追加类型**

在文件末尾追加：

```typescript
// --- Chat / Agent ---
export interface ChatSession {
  session_id: string
  title: string
  message_count: number
  created_at: string
  updated_at?: string
}

export interface ChatMessage {
  id?: number
  role: 'user' | 'assistant'
  content: string
  tool_calls?: string
  created_at?: string
}

export type WsConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'
```

- [ ] **Step 2: 编写 `stores/chat.ts`**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatSession, ChatMessage, WsConnectionState } from '@/types'
import { useAuthStore } from '@/stores/auth'

const WS_URL = 'ws://localhost:8090/ws/chat'

export const useChatStore = defineStore('chat', () => {
  const connectionState = ref<WsConnectionState>('disconnected')
  const sessions = ref<ChatSession[]>([])
  const messages = ref<ChatMessage[]>([])
  const currentSessionId = ref<string | null>(null)
  const streamingContent = ref('')
  const isStreaming = ref(false)

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  const currentMessages = computed(() => {
    if (streamingContent.value && messages.value.length > 0) {
      const msgs = [...messages.value]
      const last = { ...msgs[msgs.length - 1] }
      last.content = streamingContent.value
      msgs[msgs.length - 1] = last
      return msgs
    }
    return messages.value
  })

  function connect() {
    const auth = useAuthStore()
    if (!auth.token) return

    connectionState.value = 'connecting'
    const token = encodeURIComponent(auth.token)
    ws = new WebSocket(`${WS_URL}?token=${token}`)

    ws.onopen = () => {
      connectionState.value = 'connected'
      fetchSessions()
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleMessage(data)
    }

    ws.onclose = () => {
      connectionState.value = 'disconnected'
      scheduleReconnect()
    }

    ws.onerror = () => {
      connectionState.value = 'error'
      ws?.close()
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      if (connectionState.value === 'disconnected') {
        connect()
      }
    }, 3000)
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
    ws = null
    connectionState.value = 'disconnected'
    sessions.value = []
    messages.value = []
    currentSessionId.value = null
    streamingContent.value = ''
    isStreaming.value = false
  }

  function handleMessage(data: any) {
    switch (data.type) {
      case 'token':
        isStreaming.value = true
        streamingContent.value += data.content || ''
        break

      case 'done':
        if (isStreaming.value) {
          // 流式完成，追加完整消息
          messages.value.push({
            role: 'assistant',
            content: data.full_content || streamingContent.value,
            tool_calls: data.tool_calls?.join(', '),
          })
          streamingContent.value = ''
          isStreaming.value = false
        }
        // 如果是 new_session 或 delete_session 的响应，刷新列表
        fetchSessions()
        break

      case 'error':
        messages.value.push({
          role: 'assistant',
          content: `❌ ${data.message}`,
        })
        isStreaming.value = false
        streamingContent.value = ''
        break

      case 'session_list':
        sessions.value = data.sessions || []
        break

      case 'history':
        messages.value = (data.messages || []).map((m: any) => ({
          role: m.role,
          content: m.content,
          tool_calls: m.tool_calls,
        }))
        break

      case 'ping':
        send({ type: 'pong' })
        break
    }
  }

  function send(data: any) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }

  function sendMessage(content: string) {
    if (!currentSessionId.value) {
      newSession()
    }
    messages.value.push({ role: 'user', content })
    send({ type: 'message', session_id: currentSessionId.value, content })
  }

  function newSession() {
    send({ type: 'new_session' })
  }

  function fetchSessions() {
    send({ type: 'list_sessions' })
  }

  function loadHistory(sessionId: string) {
    currentSessionId.value = sessionId
    messages.value = []
    streamingContent.value = ''
    send({ type: 'load_history', session_id: sessionId })
  }

  function deleteSession(sessionId: string) {
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      messages.value = []
    }
    send({ type: 'delete_session', session_id: sessionId })
  }

  // 处理 new_session 响应中的 session_id
  function onSessionCreated(sessionId: string) {
    currentSessionId.value = sessionId
    messages.value = []
    streamingContent.value = ''
  }

  return {
    connectionState, sessions, messages, currentSessionId,
    streamingContent, isStreaming, currentMessages,
    connect, disconnect, sendMessage, newSession,
    fetchSessions, loadHistory, deleteSession, onSessionCreated,
  }
})
```

- [ ] **Step 3: 检查类型一致性**

确保 `types/index.ts` 中新增的类型与 store 中使用的类型一致。

- [ ] **Step 4: Commit**

```bash
git add frontend/client/src/types/index.ts frontend/client/src/stores/chat.ts
git commit -m "feat(agent): 前端 Chat store + 类型定义"
```

---

### Task 10: 前端 ChatMessageList 组件

**Files:**
- Create: `frontend/client/src/components/chat/ChatMessageList.vue`

**Interfaces:**
- Consumes: `useChatStore` — `currentMessages`, `isStreaming`, `connectionState`
- Props: 无（直接从 store 读）

- [ ] **Step 1: 编写 `ChatMessageList.vue`**

```vue
<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const store = useChatStore()
const container = ref<HTMLElement | null>(null)

// Auto scroll to bottom
watch(
  () => store.currentMessages.length + store.streamingContent.length,
  async () => {
    await nextTick()
    if (container.value) {
      container.value.scrollTop = container.value.scrollHeight
    }
  },
  { flush: 'post' }
)

const isEmpty = computed(() => store.currentMessages.length === 0 && !store.isStreaming)
const isConnected = computed(() => store.connectionState === 'connected')

function formatRole(role: string) {
  return role === 'assistant' ? '🤖 AI' : '👤 我'
}
</script>

<template>
  <div
    ref="container"
    class="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
    style="min-height: 0;"
  >
    <!-- Empty state: welcome -->
    <div v-if="isEmpty && isConnected" class="flex flex-col items-center justify-center h-full text-center py-8">
      <div class="text-4xl mb-3">🎌</div>
      <h3 class="text-lg font-semibold mb-2" style="color: var(--color-text);">AI 追番助手</h3>
      <p class="text-sm mb-4" style="color: var(--color-text-secondary);">
        问我关于番剧的任何问题
      </p>
      <ul class="space-y-1 text-xs" style="color: var(--color-text-secondary);">
        <li>💡 &nbsp;推荐这季度热门番</li>
        <li>💡 &nbsp;今晚有什么更新</li>
        <li>💡 &nbsp;评分最高的番</li>
        <li>💡 &nbsp;推荐几部热血战斗番</li>
      </ul>
    </div>

    <!-- Connection lost -->
    <div v-if="store.connectionState === 'disconnected' || store.connectionState === 'error'"
      class="flex items-center justify-center py-4">
      <span class="text-sm text-red-500">连接已断开，正在重连...</span>
    </div>

    <!-- Messages -->
    <div
      v-for="(msg, idx) in store.currentMessages"
      :key="idx"
      class="flex"
      :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
    >
      <div
        class="max-w-[85%] rounded-2xl px-4 py-2.5"
        :style="{
          background: msg.role === 'user' ? 'var(--color-primary)' : 'var(--color-card)',
          color: msg.role === 'user' ? '#fff' : 'var(--color-text)',
          border: msg.role === 'user' ? 'none' : '1px solid var(--color-border)',
        }"
      >
        <div class="text-[11px] opacity-60 mb-1">{{ formatRole(msg.role) }}</div>
        <div class="text-sm whitespace-pre-wrap break-words leading-relaxed">
          {{ msg.content }}
          <!-- Streaming cursor -->
          <span v-if="idx === store.currentMessages.length - 1 && store.isStreaming" class="inline-block w-1.5 h-4 ml-0.5 animate-pulse rounded-sm" style="background: var(--color-text);" />
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 创建组件目录**

```bash
mkdir -p frontend/client/src/components/chat
```

- [ ] **Step 3: Commit**

```bash
git add frontend/client/src/components/chat/ChatMessageList.vue
git commit -m "feat(agent): ChatMessageList 组件"
```

---

### Task 11: 前端 ChatSessionList 组件

**Files:**
- Create: `frontend/client/src/components/chat/ChatSessionList.vue`

**Interfaces:**
- Consumes: `useChatStore` — `sessions`, `currentSessionId`, `connectionState`
- Emits: 无（所有操作通过 store 方法）

- [ ] **Step 1: 编写 `ChatSessionList.vue`**

```vue
<script setup lang="ts">
import { useChatStore } from '@/stores/chat'

const store = useChatStore()

function selectSession(sessionId: string) {
  store.loadHistory(sessionId)
}

function confirmDelete(sessionId: string, event: MouseEvent) {
  event.stopPropagation()
  if (confirm('确定删除该会话？')) {
    store.deleteSession(sessionId)
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr.replace(' ', 'T'))
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 86400000) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="flex flex-col h-full" style="background: var(--color-card); border-right: 1px solid var(--color-border);">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b shrink-0" style="border-color: var(--color-border);">
      <h3 class="text-sm font-semibold" style="color: var(--color-text);">会话</h3>
      <button
        class="text-xs px-3 py-1.5 rounded-full font-medium transition-colors"
        style="background: var(--color-primary); color: #fff;"
        @click="store.newSession()"
        :disabled="store.connectionState !== 'connected'"
      >
        + 新对话
      </button>
    </div>

    <!-- Session list -->
    <div class="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
      <div v-if="store.sessions.length === 0" class="text-center py-8 text-xs" style="color: var(--color-text-secondary);">
        暂无会话记录
      </div>
      <button
        v-for="s in store.sessions"
        :key="s.session_id"
        class="flex items-center gap-2 w-full px-3 py-2.5 rounded-xl text-left text-sm transition-colors duration-150"
        :class="s.session_id === store.currentSessionId ? '' : ''"
        :style="{
          background: s.session_id === store.currentSessionId ? 'var(--color-hover)' : 'transparent',
          color: 'var(--color-text)',
        }"
        @click="selectSession(s.session_id)"
      >
        <span class="text-base shrink-0">💬</span>
        <div class="flex-1 min-w-0">
          <div class="text-sm truncate">{{ s.title || '新对话' }}</div>
          <div class="text-[11px] mt-0.5" style="color: var(--color-text-secondary);">
            {{ s.message_count }} 条消息 · {{ formatDate(s.updated_at || s.created_at) }}
          </div>
        </div>
        <button
          class="shrink-0 w-6 h-6 flex items-center justify-center rounded-full text-xs opacity-0 group-hover:opacity-100 hover:bg-red-100 hover:text-red-500 transition-all"
          style="color: var(--color-text-secondary);"
          @click="confirmDelete(s.session_id, $event)"
        >
          ✕
        </button>
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/components/chat/ChatSessionList.vue
git commit -m "feat(agent): ChatSessionList 组件"
```

---

### Task 12: 前端 ChatInput 组件

**Files:**
- Create: `frontend/client/src/components/chat/ChatInput.vue`

**Interfaces:**
- Consumes: `useChatStore` — `sendMessage`, `isStreaming`, `connectionState`

- [ ] **Step 1: 编写 `ChatInput.vue`**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'

const store = useChatStore()
const input = ref('')
const quickQuestions = [
  '推荐这季度热门番',
  '今晚有什么更新',
  '评分最高的番是哪些',
  '推荐几部热血战斗番',
]

function send() {
  const text = input.value.trim()
  if (!text || store.isStreaming || store.connectionState !== 'connected') return
  store.sendMessage(text)
  input.value = ''
}

function sendQuick(q: string) {
  if (store.isStreaming) return
  store.sendMessage(q)
}
</script>

<template>
  <div class="border-t px-4 py-3 shrink-0" style="border-color: var(--color-border); background: var(--color-card);">
    <!-- Quick questions -->
    <div v-if="store.messages.length === 0 && !store.isStreaming" class="flex flex-wrap gap-1.5 mb-3">
      <button
        v-for="q in quickQuestions"
        :key="q"
        class="text-[11px] px-2.5 py-1.5 rounded-full transition-colors"
        style="background: var(--color-hover); color: var(--color-text-secondary);"
        @click="sendQuick(q)"
        :disabled="store.connectionState !== 'connected'"
      >
        {{ q }}
      </button>
    </div>

    <!-- Input row -->
    <div class="flex items-center gap-2">
      <input
        v-model="input"
        type="text"
        placeholder="输入你想问的..."
        class="flex-1 px-4 py-2.5 rounded-xl text-sm outline-none transition-all"
        :style="{
          background: 'var(--color-bg)',
          color: 'var(--color-text)',
          border: '1px solid var(--color-border)',
        }"
        @keyup.enter="send"
        :disabled="store.connectionState !== 'connected'"
      />
      <button
        class="shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-colors"
        :style="{
          background: store.isStreaming ? 'var(--color-hover)' : 'var(--color-primary)',
          color: store.isStreaming ? 'var(--color-text-secondary)' : '#fff',
        }"
        @click="send"
        :disabled="!input.trim() || store.connectionState !== 'connected'"
      >
        <span class="text-sm">{{ store.isStreaming ? '···' : '➤' }}</span>
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/components/chat/ChatInput.vue
git commit -m "feat(agent): ChatInput 组件 + 快捷提问"
```

---

### Task 13: 前端 ChatWidget 容器组件 + 集成到 App.vue

**Files:**
- Create: `frontend/client/src/components/chat/ChatWidget.vue`
- Modify: `frontend/client/src/App.vue`

**Interfaces:**
- Consumes: `useChatStore` — `connect`, `disconnect`, `connectionState`, `onSessionCreated`
- 全局 FAB 按钮 + 侧滑面板

- [ ] **Step 1: 编写 `ChatWidget.vue`**

```vue
<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatSessionList from './ChatSessionList.vue'
import ChatMessageList from './ChatMessageList.vue'
import ChatInput from './ChatInput.vue'

const store = useChatStore()
const open = ref(false)
const showSessions = ref(true)

function toggle() {
  open.value = !open.value
  if (open.value) {
    store.connect()
  } else {
    store.disconnect()
  }
}

// 监听 new_session 响应，设置 currentSessionId
watch(
  () => store.sessions.length,
  (_, old) => {
    if (old === 0 && store.sessions.length > 0) {
      // 新建会话后自动选中最新的
      const latest = store.sessions[0]
      store.loadHistory(latest.session_id)
    }
  }
)

// 当收到 done 且没有 currentSessionId 时（new_session 响应）
watch(
  () => store.messages.length,
  (n, prev) => {
    // 如果消息从 0 变为 1 且是 new_session 响应，检查 session_id
    if (n === 1 && prev === 0 && store.currentSessionId === null) {
      store.fetchSessions()
    }
  }
)

onUnmounted(() => {
  store.disconnect()
})
</script>

<template>
  <!-- FAB -->
  <button
    class="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-xl flex items-center justify-center text-2xl transition-transform duration-200 hover:scale-105 active:scale-95"
    style="background: var(--color-primary); color: #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.15);"
    @click="toggle"
  >
    {{ open ? '✕' : '💬' }}
  </button>

  <!-- Panel overlay -->
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div
      v-if="open"
      class="fixed bottom-24 right-6 z-50 w-[720px] max-w-[calc(100vw-2rem)] h-[600px] max-h-[calc(100vh-8rem)] rounded-2xl shadow-2xl flex overflow-hidden"
      style="background: var(--color-card); border: 1px solid var(--color-border);"
    >
      <!-- Session sidebar -->
      <div v-if="showSessions" class="w-52 shrink-0 hidden md:block">
        <ChatSessionList />
      </div>

      <!-- Main chat area -->
      <div class="flex-1 flex flex-col min-w-0">
        <!-- Top bar -->
        <div class="flex items-center justify-between px-4 py-2.5 border-b shrink-0" style="border-color: var(--color-border);">
          <div class="flex items-center gap-2">
            <button
              v-if="store.currentSessionId"
              class="text-xs px-2 py-1 rounded-md transition-colors md:hidden"
              style="background: var(--color-hover); color: var(--color-text-secondary);"
              @click="showSessions = !showSessions"
            >
              ☰
            </button>
            <span class="text-sm font-semibold" style="color: var(--color-text);">
              AI 追番助手
            </span>
            <span
              class="w-2 h-2 rounded-full"
              :style="{
                background: store.connectionState === 'connected' ? '#22c55e'
                  : store.connectionState === 'connecting' ? '#f59e0b'
                  : '#ef4444'
              }"
            />
          </div>
          <span class="text-[11px]" style="color: var(--color-text-secondary);">
            {{ store.connectionState === 'connected' ? '已连接' : store.connectionState === 'connecting' ? '连接中...' : '已断开' }}
          </span>
        </div>

        <!-- Messages -->
        <ChatMessageList />

        <!-- Input -->
        <ChatInput />
      </div>
    </div>
  </Transition>
</template>
```

- [ ] **Step 2: 修改 `App.vue` — 引入 ChatWidget**

```diff
  <script setup lang="ts">
  import { onMounted } from 'vue'
  import { useAuthStore } from '@/stores/auth'
+ import ChatWidget from '@/components/chat/ChatWidget.vue'

  const auth = useAuthStore()

  onMounted(() => {
    if (auth.token && !auth.user) {
      auth.fetchMe()
    }
  })
  </script>

  <template>
    <router-view />
+   <ChatWidget />
  </template>
```

- [ ] **Step 3: 验证 TypeScript 编译**

```bash
cd frontend/client && npx vue-tsc --noEmit 2>&1 | head -20
```
Expected: 无类型错误

- [ ] **Step 4: 验证构建**

```bash
cd frontend/client && npm run build 2>&1 | tail -5
```
Expected: 构建成功

- [ ] **Step 5: Commit**

```bash
git add frontend/client/src/components/chat/ frontend/client/src/App.vue
git commit -m "feat(agent): ChatWidget 全局聊天窗口 + App.vue 集成"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ 10 个 Tool 定义（Task 4 覆盖 §4）
- ✅ WebSocket 消息协议（Task 3 覆盖 §3）
- ✅ SQLite 持久化（Task 2 覆盖 §5）
- ✅ 配置层（Task 1 覆盖 §6）
- ✅ 认证流程（Task 7 覆盖 §9）
- ✅ AgentExecutor 初始化（Task 6 覆盖 §2）
- ✅ 前端 ChatWidget + 3 个子组件（Tasks 9-13 覆盖 §8）
- ✅ 流式渲染（Task 10 + Task 7 覆盖）
- ✅ 快捷提问（Task 12 覆盖）

**2. Placeholder scan:** 无 TBD/TODO，所有代码为最终内容。

**3. Type consistency:**
- `ClientMessage` dataclass ↔ WebSocket JSON 协议一致 ✓
- `settings.backend_base_url` (str) ↔ `httpx.get(f"{BASE}/...")` ✓
- 前端 `ChatSession` ↔ 后端 `SessionInfo` dataclass ✓
- `useChatStore.connect/disconnect` ↔ `ChatWidget.vue` 生命周期 ✓
- `verify_token(token: str) -> int | None` ↔ WS handler 中使用 ✓

**4. Frontend build:** 不引入新 npm 依赖，原生 WebSocket API，PASS ✓
