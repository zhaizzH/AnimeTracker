# Agent 模块重构 — 实施计划
# 使用中文commit messages
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有基于 LangChain AgentExecutor + WebSocket 的 Agent 重构为 LangGraph 多 Agent 路由架构 + SSE 通信

**Architecture:** FastAPI 应用接收 POST /api/chat/stream 请求，通过两层 LangGraph StateGraph 路由（角色分发 → 意图分发）派发到独立 Sub-agent ReAct 循环，结果通过 SSE 逐 token 推送到前端。会话/消息持久化使用 SQLite + Pydantic。

**Tech Stack:** Python 3.11+, FastAPI, LangChain (>=1.3), LangGraph (>=1.2.0), Pydantic v2, SQLite, httpx, DashScope/ChatTongyi

## Global Constraints

- 所有 Pydantic model 使用 v2 风格（`BaseModel` / `field_validator` / `model_dump`）
- 所有工具函数使用 `from langchain_core.tools import tool` 装饰器
- FastAPI `verify_token` 依赖注入中调用 Spring Boot `/api/user/me` 验证 JWT
- pydantic-settings 用于配置管理
- SQLite WAL 模式 + `busy_timeout=5000`
- reqiurements.txt 锁定 `langchain>=1.3.0`、`langgraph>=1.2.0`、`pydantic>=2.0`
- 兼容旧版 `agent.db` 文件（表结构不变）

---

### Task 1: 项目脚手架 — Config + 目录结构

**Files:**
- Create: `backend/agent/requirements.txt`
- Modify: `backend/agent/.env.example`
- Create: `backend/agent/app/config.py`
- Create: 所有 `app/*/__init__.py`（空文件）
- Create: `backend/agent/app/schemas/__init__.py`
- Create: `backend/agent/app/api/__init__.py`
- Create: `backend/agent/app/graph/__init__.py`
- Create: `backend/agent/app/tools/__init__.py`
- Create: `backend/agent/app/llm/__init__.py`
- Create: `backend/agent/app/service/__init__.py`
- Create: `backend/agent/app/db/__init__.py`

**Interfaces:**
- Consumes: (none, first task)
- Produces: `Settings` dataclass with all config fields, `requirements.txt` with pinned deps, empty `__init__.py` files for all sub-packages

- [ ] **Step 1: Write requirements.txt**

```text
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
langchain>=1.3.0
langchain-community==0.4.2
langchain-core>=1.3.0
langgraph>=1.2.0
httpx>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
websockets>=12.0
pytest>=8.0
pytest-asyncio>=0.24.0
respx>=0.21.0
```

- [ ] **Step 2: Write .env.example**

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

- [ ] **Step 3: Write app/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Backend API — 去掉路径后缀，工具调用时自行拼接完整路径
    backend_base_url: str = "http://localhost:8080"

    # Database
    database_url: str = "sqlite:///agent.db"

    # Agent Runtime
    agent_max_iterations: int = 5

    # CORS (开发环境)
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
```

- [ ] **Step 4: Create all __init__.py files**

```bash
cd /home/zzz/workspace/project/AnimeTracker
# 每个新的子包创建空的 __init__.py
mkdir -p backend/agent/app/{schemas,api,graph,tools,llm,service,db}
touch backend/agent/app/schemas/__init__.py
touch backend/agent/app/api/__init__.py
touch backend/agent/app/graph/__init__.py
touch backend/agent/app/tools/__init__.py
touch backend/agent/app/llm/__init__.py
touch backend/agent/app/service/__init__.py
touch backend/agent/app/db/__init__.py
touch backend/agent/tests/__init__.py
```

- [ ] **Step 5: Commit**

```bash
git add backend/agent/requirements.txt backend/agent/.env.example backend/agent/app/ backend/agent/tests/
git commit -m "feat(agent): 搭建项目脚手架，添加配置和目录结构"
```

---

### Task 2: 数据模型层 — Pydantic Schemas

**Files:**
- Create: `backend/agent/app/db/models.py`
- Create: `backend/agent/app/schemas/auth.py`
- Create: `backend/agent/app/schemas/chat.py`
- Create: `backend/agent/app/schemas/session.py`

**Interfaces:**
- Consumes: (none — pure Pydantic)
- Produces: `Session`, `Message` (db models); `UserInfo`, `AuthResult` (auth schemas); `ChatRequest` (chat schema); `SessionInfo`, `MessageOut`, `DeleteResponse`, `SessionCreateRequest`, `SessionCreateResponse` (session schemas)

- [ ] **Step 1: Write the tests**

```python
# tests/test_schemas.py
import pytest
from datetime import datetime
from app.schemas.auth import UserInfo, AuthResult
from app.schemas.chat import ChatRequest
from app.schemas.session import SessionInfo, MessageOut, SessionCreateRequest, SessionCreateResponse, DeleteResponse
from app.db.models import Session, Message


class TestAuthSchemas:
    def test_user_info(self):
        u = UserInfo(user_id=1, username="test", role="USER")
        assert u.model_dump() == {"user_id": 1, "username": "test", "role": "USER"}

    def test_user_info_invalid_role(self):
        with pytest.raises(ValueError):
            UserInfo(user_id=1, username="test", role="INVALID")

    def test_auth_result_ok(self):
        u = UserInfo(user_id=1, username="test", role="USER")
        r = AuthResult(ok=True, user=u)
        assert r.ok is True
        assert r.user is not None

    def test_auth_result_fail(self):
        r = AuthResult(ok=False, error="bad token")
        assert r.ok is False
        assert r.user is None


class TestChatSchemas:
    def test_chat_request_valid(self):
        r = ChatRequest(session_id="s1", content="hello")
        assert r.session_id == "s1"
        assert r.content == "hello"

    def test_chat_request_empty_content(self):
        with pytest.raises(ValueError):
            ChatRequest(session_id="s1", content="")


class TestSessionSchemas:
    def test_session_info(self):
        dt = datetime(2026, 1, 1)
        s = SessionInfo(session_id="s1", title="test", message_count=5, created_at=dt)
        assert s.session_id == "s1"

    def test_message_out(self):
        dt = datetime(2026, 1, 1)
        m = MessageOut(role="user", content="hi", tool_calls=["search"], created_at=dt)
        assert m.role == "user"


class TestDbModels:
    def test_session_defaults(self):
        s = Session(session_id="s1", user_id=1)
        assert s.title == "新对话"
        assert s.message_count == 0

    def test_message_defaults(self):
        m = Message(session_id="s1", role="user", content="hi")
        assert m.id is None
        assert m.tool_calls is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend/agent && python -m pytest tests/test_schemas.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write the Pydantic models**

```python
# app/db/models.py — 数据层模型
from pydantic import BaseModel, Field
from datetime import datetime


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
    role: str  # "user" | "assistant"
    content: str
    tool_calls: str | None = None  # JSON string
    created_at: datetime = Field(default_factory=datetime.now)
```

```python
# app/schemas/auth.py
from pydantic import BaseModel
from typing import Literal


class UserInfo(BaseModel):
    user_id: int
    username: str
    role: Literal["USER", "ADMIN"]


class AuthResult(BaseModel):
    ok: bool
    user: UserInfo | None = None
    error: str | None = None
```

```python
# app/schemas/chat.py
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    content: str = Field(..., min_length=1, max_length=4096)
```

```python
# app/schemas/session.py
from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class SessionInfo(BaseModel):
    session_id: str
    title: str
    message_count: int
    created_at: datetime


class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[str] | None = None
    created_at: datetime


class SessionCreateRequest(BaseModel):
    session_id: str | None = None


class SessionCreateResponse(BaseModel):
    session_id: str


class DeleteResponse(BaseModel):
    message: str = "deleted"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend/agent && python -m pytest tests/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agent/app/db/models.py backend/agent/app/schemas/ backend/agent/tests/test_schemas.py
git commit -m "feat(agent): 添加 Pydantic 数据模型和 API Schema"
```

---

### Task 3: 数据库存储层 — ChatStore ABC + SQLiteStore

**Files:**
- Create: `backend/agent/app/db/base.py`
- Create: `backend/agent/app/db/sqlite_store.py`

**Interfaces:**
- Consumes: `ChatStore(ABC)`, `settings`
- Produces: `ChatStore(ABC)` 增加 `update_session_title()` 方法, `SQLiteStore(ChatStore)` 完整实现 — `init_db()`, `create_session()`, `get_user_sessions(user_id) -> list[Session]`, `get_messages(session_id) -> list[Message]`, `save_message(session_id, role, content, tool_calls)`, `delete_session(session_id, user_id)`, `update_session_title(session_id, title)`

- [ ] **Step 1: Write test for SQLiteStore**

```python
# tests/test_db.py
import os
import tempfile
import pytest
from datetime import datetime

from app.db.base import ChatStore
from app.db.sqlite_store import SQLiteStore
from app.db.models import Session, Message


@pytest.fixture
def store():
    db_path = os.path.join(tempfile.gettempdir(), f"test_agent_{datetime.now().timestamp()}.db")
    s = SQLiteStore(f"sqlite:///{db_path}")
    s.init_db()
    yield s
    if os.path.exists(db_path):
        os.remove(db_path)


class TestSQLiteStore:
    def test_init_creates_tables(self, store):
        conn = store._conn()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        names = [r["name"] for r in tables]
        assert "sessions" in names
        assert "messages" in names
        conn.close()

    def test_create_and_list_sessions(self, store):
        store.create_session(1, "sess-1", "测试会话")
        sessions = store.get_user_sessions(1)
        assert len(sessions) == 1
        assert sessions[0].session_id == "sess-1"
        assert sessions[0].title == "测试会话"
        assert sessions[0].message_count == 0

    def test_messages_belong_to_session(self, store):
        store.create_session(1, "sess-1")
        store.save_message("sess-1", "user", "Hello")
        store.save_message("sess-1", "assistant", "Hi!")
        msgs = store.get_messages("sess-1")
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[1].role == "assistant"

    def test_delete_session_cascades(self, store):
        store.create_session(1, "sess-1")
        store.save_message("sess-1", "user", "Hello")
        store.delete_session("sess-1", 1)
        assert store.get_messages("sess-1") == []
        assert store.get_user_sessions(1) == []

    def test_session_ordering(self, store):
        store.create_session(1, "sess-old", "旧的")
        store.create_session(1, "sess-new", "新的")
        sessions = store.get_user_sessions(1)
        assert sessions[0].session_id == "sess-new"

    def test_other_user_not_visible(self, store):
        store.create_session(1, "sess-1")
        store.create_session(2, "sess-2")
        assert len(store.get_user_sessions(1)) == 1

    def test_save_message_updates_count(self, store):
        store.create_session(1, "sess-1")
        store.save_message("sess-1", "user", "Hi")
        sessions = store.get_user_sessions(1)
        assert sessions[0].message_count == 1

    def test_inherits_abc(self, store):
        assert isinstance(store, ChatStore)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend/agent && python -m pytest tests/test_db.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write ChatStore ABC**

```python
# app/db/base.py
from abc import ABC, abstractmethod
from app.db.models import Session, Message


class ChatStore(ABC):
    """存储抽象接口 — 当前 SQLite 实现，后续可切换 MySQL"""

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

    @abstractmethod
    def update_session_title(self, session_id: str, title: str): ...
```

- [ ] **Step 4: Write SQLiteStore**

```python
# app/db/sqlite_store.py
import sqlite3
import re
from datetime import datetime

from app.db.base import ChatStore
from app.db.models import Session, Message


class SQLiteStore(ChatStore):
    def __init__(self, database_url: str):
        m = re.match(r"sqlite:///(.+)", database_url)
        self.db_path = m.group(1) if m else database_url

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT DEFAULT '新对话',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated_at);
            """)

    def create_session(self, user_id: int, session_id: str, title: str = "新对话"):
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, user_id, title, now, now),
            )

    def get_user_sessions(self, user_id: int) -> list[Session]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
            ).fetchall()
        return [Session(**dict(r)) for r in rows]

    def get_messages(self, session_id: str) -> list[Message]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at", (session_id,)
            ).fetchall()
        return [Message(**dict(r)) for r in rows]

    def save_message(self, session_id: str, role: str, content: str, tool_calls: str | None = None):
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, tool_calls, now),
            )
            if role == "user":
                conn.execute(
                    "UPDATE sessions SET message_count = message_count + 1, updated_at = ? WHERE session_id = ?",
                    (now, session_id),
                )
            else:
                conn.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    (now, session_id),
                )

    def delete_session(self, session_id: str, user_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, user_id))

    def update_session_title(self, session_id: str, title: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ?",
                (title, datetime.now().isoformat(), session_id),
            )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend/agent && python -m pytest tests/test_db.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add backend/agent/app/db/ backend/agent/tests/test_db.py
git commit -m "feat(agent): 添加 ChatStore 抽象接口和 SQLiteStore 实现"
```

---

### Task 4: LLM 层 — ChatTongyi 初始化 + monkey-patch

**Files:**
- Create: `backend/agent/app/llm/models.py`

**Interfaces:**
- Consumes: `settings` from `app.config`
- Produces: `create_llm(settings) -> BaseChatModel` (with monkey-patch applied)

- [ ] **Step 1: Write the test**

```python
# tests/test_llm.py
from unittest.mock import patch, MagicMock
from app.llm.models import create_llm
from app.config import Settings


def test_create_llm_returns_chat_model():
    s = Settings(dashscope_api_key="test-key")
    llm = create_llm(s)
    assert llm is not None


def test_monkey_patch_applied():
    """verify monkey-patch replaces subtract_client_response"""
    from langchain_community.chat_models.tongyi import ChatTongyi
    s = Settings(dashscope_api_key="test-key")
    _ = create_llm(s)
    assert "patched" in ChatTongyi.subtract_client_response.__name__
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend/agent && python -m pytest tests/test_llm.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write models.py**

```python
# app/llm/models.py
import json
import logging
from langchain_community.chat_models.tongyi import ChatTongyi

logger = logging.getLogger(__name__)


def _patch_chat_tongyi():
    """修复 langchain-community ChatTongyi 流式 delta 合并问题。
    如果上游修复可移除此 monkey-patch。"""
    _orig = ChatTongyi.subtract_client_response

    def _patched_subtract(self, resp, prev_resp):
        resp_copy = json.loads(json.dumps(resp))
        choice = resp_copy["output"]["choices"][0]
        message = choice["message"]
        prev_copy = json.loads(json.dumps(prev_resp))
        prev_message = prev_copy["output"]["choices"][0]["message"]
        message["content"] = message["content"].replace(prev_message["content"], "")
        if message.get("tool_calls") and prev_message.get("tool_calls"):
            for i, tc in enumerate(message["tool_calls"]):
                fn = tc["function"]
                prev_fn = prev_message["tool_calls"][i]["function"]
                if "name" in fn and "name" in prev_fn:
                    fn["name"] = fn["name"].replace(prev_fn["name"], "")
                if "arguments" in fn and "arguments" in prev_fn:
                    fn["arguments"] = fn["arguments"].replace(prev_fn["arguments"], "")
        return resp_copy

    _patched_subtract.__name__ = "patched_subtract_client_response"
    ChatTongyi.subtract_client_response = _patched_subtract
    logger.info("Applied ChatTongyi monkey-patch for streaming delta merge")


def create_llm(settings):
    """创建并返回 ChatTongyi 实例（已应用 monkey-patch）"""
    _patch_chat_tongyi()
    return ChatTongyi(
        model=settings.llm_model,
        api_key=settings.dashscope_api_key,
        streaming=True,
        model_kwargs={
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
        },
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend/agent && python -m pytest tests/test_llm.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agent/app/llm/ backend/agent/tests/test_llm.py
git commit -m "feat(agent): 添加 LLM 层，集成 ChatTongyi 和流式修复补丁"
```

---

### Task 5: 工具层 — 10 个用户侧工具函数

**Files:**
- Modify: `backend/agent/tools/__init__.py`
- Create: `backend/agent/app/tools/user_tools.py`
- Create: `backend/agent/app/tools/admin_tools.py`（预留空文件）

**Interfaces:**
- Consumes: `settings.backend_base_url`
- Produces: `tools` list 包含 10 个 `@tool` 装饰的函数，每个函数调用 Spring Boot API

- [ ] **Step 1: Write the tests**

```python
# tests/test_tools.py
import pytest
import respx
from httpx import Response
from app.tools.user_tools import (
    search_subjects, get_subject_detail, get_episodes,
    get_schedule, get_season_subjects, get_popular_subjects,
    get_top_rated, get_tags, get_subjects_by_tag, get_stats,
)
from app.config import settings

BASE = settings.backend_base_url


class TestUserTools:
    @respx.mock
    def test_search_subjects(self):
        route = respx.get(f"{BASE}/api/user/subjects/search").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1, "name": "Test"}], "total": 1}
        }))
        result = search_subjects.invoke({"query": "热血"})
        assert route.called
        assert result[0]["id"] == 1

    @respx.mock
    def test_get_subject_detail(self):
        respx.get(f"{BASE}/api/user/subjects/42").mock(Response(200, json={
            "code": 200, "data": {"id": 42, "name": "钢之炼金术师"}
        }))
        result = get_subject_detail.invoke({"subject_id": 42})
        assert result["name"] == "钢之炼金术师"

    @respx.mock
    def test_get_episodes(self):
        respx.get(f"{BASE}/api/user/subjects/1/episodes").mock(Response(200, json={
            "code": 200, "data": [{"id": 1, "sort": 1.0}]
        }))
        result = get_episodes.invoke({"subject_id": 1})
        assert len(result) == 1

    @respx.mock
    def test_get_schedule(self):
        respx.get(f"{BASE}/api/user/subjects/schedule").mock(Response(200, json={
            "code": 200, "data": {"content": [], "total": 0}
        }))
        result = get_schedule.invoke({"weekday": 1})
        assert "content" in result

    @respx.mock
    def test_get_tags(self):
        respx.get(f"{BASE}/api/user/tags").mock(Response(200, json={
            "code": 200, "data": [{"name": "热血", "count": 50}]
        }))
        result = get_tags.invoke({})
        assert result[0]["name"] == "热血"

    @respx.mock
    def test_get_stats(self):
        respx.get(f"{BASE}/api/user/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [], "total": 500, "page": 1, "size": 1}
        }))
        result = get_stats.invoke({})
        assert result["total"] == 500

    @respx.mock
    def test_tool_http_error(self):
        respx.get(f"{BASE}/api/user/subjects/search").mock(Response(500))
        result = search_subjects.invoke({"query": "error"})
        # 工具应返回错误 dict 而非抛异常
        assert isinstance(result, dict)
        assert result.get("error") is True

    @respx.mock
    def test_get_season_subjects(self):
        respx.get(f"{BASE}/api/user/subjects/season").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1}], "total": 1}
        }))
        result = get_season_subjects.invoke({"year": 2026, "quarter": "spring"})
        assert len(result) == 1

    @respx.mock
    def test_get_popular_subjects(self):
        respx.get(f"{BASE}/api/user/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1}], "total": 1}
        }))
        result = get_popular_subjects.invoke({"page": 1})
        assert result[0]["id"] == 1

    @respx.mock
    def test_get_top_rated(self):
        respx.get(f"{BASE}/api/user/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1}], "total": 1}
        }))
        result = get_top_rated.invoke({"page": 1})
        assert result[0]["id"] == 1

    @respx.mock
    def test_get_subjects_by_tag(self):
        respx.get(f"{BASE}/api/user/tags/热血/subjects").mock(Response(200, json={
            "code": 200, "data": {"content": [{"id": 1}], "total": 1}
        }))
        result = get_subjects_by_tag.invoke({"tag": "热血"})
        assert len(result) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend/agent && python -m pytest tests/test_tools.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write user_tools.py**

```python
# app/tools/user_tools.py
import httpx
from langchain_core.tools import tool
from app.config import settings

BASE = settings.backend_base_url


def _safe_call(func):
    """工具调用包装器：统一处理 HTTP 异常"""
    try:
        return func()
    except httpx.TimeoutException:
        return {"error": True, "message": "后端服务超时"}
    except httpx.HTTPStatusError as e:
        return {"error": True, "message": f"后端返回错误: {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"error": True, "message": f"后端服务不可用: {str(e)}"}


@tool
def search_subjects(query: str, page: int = 1, size: int = 20) -> list | dict:
    """按关键词搜索番剧。query: 搜索关键词"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/search", params={"q": query, "page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
def get_subject_detail(subject_id: int) -> dict:
    """获取番剧详细信息。subject_id: 番剧 ID"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/{subject_id}", timeout=10
    ).raise_for_status().json()["data"])


@tool
def get_episodes(subject_id: int) -> list:
    """获取番剧的剧集列表。subject_id: 番剧 ID"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/{subject_id}/episodes", timeout=10
    ).raise_for_status().json()["data"])


@tool
def get_schedule(weekday: int = -1, year: int = 0, quarter: str = "") -> dict:
    """按星期获取每周追番列表。weekday: 0=周日 1=周一 ... 6=周六，-1=全部；year: 年份；quarter: spring/summer/autumn/winter"""
    params = {"weekday": weekday, "page": 1, "size": 50}
    if year:
        params["year"] = year
    if quarter:
        params["quarter"] = quarter
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/schedule", params=params, timeout=10
    ).raise_for_status().json()["data"])


@tool
def get_season_subjects(year: int, quarter: str, page: int = 1, size: int = 20) -> list:
    """按季度获取新番。year: 年份；quarter: spring/summer/autumn/winter"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects/season",
        params={"year": year, "quarter": quarter, "page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
def get_popular_subjects(page: int = 1, size: int = 10) -> list:
    """获取热度榜（按收藏数降序）"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects", params={"sort": "collectionTotal", "order": "desc", "page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
def get_top_rated(page: int = 1, size: int = 10) -> list:
    """获取评分榜（按评分降序）"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects", params={"sort": "score", "order": "desc", "page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
def get_tags() -> list:
    """获取所有标签（按使用次数降序）"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/tags", timeout=10
    ).raise_for_status().json()["data"])


@tool
def get_subjects_by_tag(tag: str, page: int = 1, size: int = 20) -> list:
    """按标签获取番剧。tag: 标签名称"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/tags/{tag}/subjects", params={"page": page, "size": size}, timeout=10
    ).raise_for_status().json()["data"]["content"])


@tool
def get_stats() -> dict:
    """获取番剧统计数据（总数等）"""
    return _safe_call(lambda: httpx.get(
        f"{BASE}/api/user/subjects", params={"page": 1, "size": 1}, timeout=10
    ).raise_for_status().json()["data"] | {"total": 0})


tools = [
    search_subjects, get_subject_detail, get_episodes,
    get_schedule, get_season_subjects, get_popular_subjects,
    get_top_rated, get_tags, get_subjects_by_tag, get_stats,
]
```

- [ ] **Step 4: Write admin_tools.py**

```python
# app/tools/admin_tools.py
# 预留：管理侧工具 （Phase 2 实现）
tools: list = []
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend/agent && python -m pytest tests/test_tools.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add backend/agent/app/tools/ backend/agent/tests/test_tools.py
git commit -m "feat(agent): 添加 10 个用户侧工具函数和统一错误处理"
```

---

### Task 6: Graph 状态 + Sub-agent 工厂

**Files:**
- Create: `backend/agent/app/graph/state.py`
- Create: `backend/agent/app/graph/sub_agent.py`

**Interfaces:**
- Consumes: `BaseMessage`, `BaseChatModel`, `BaseTool`, `SystemMessage`, `AIMessage`, `HumanMessage`, `ToolMessage` from langchain_core
- Produces: `AgentState(BaseModel)`, `SubAgentState(BaseModel)`, `create_sub_agent(name, tools, system_prompt, llm, max_iterations) -> CompiledStateGraph`

- [ ] **Step 1: Write tests**

```python
# tests/test_graph.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel

from app.graph.state import AgentState, SubAgentState
from app.schemas.auth import UserInfo


class TestAgentState:
    def test_defaults(self):
        user = UserInfo(user_id=1, username="test", role="USER")
        state = AgentState(messages=[], user=user)
        assert state.next_agent is None
        assert state.final_output == ""
        assert state.used_tools == []


class TestSubAgentState:
    def test_defaults(self):
        state = SubAgentState(messages=[])
        assert state.is_done is False

    def test_with_messages(self):
        msgs = [HumanMessage(content="hi")]
        state = SubAgentState(messages=msgs)
        assert len(state.messages) == 1


class TestSubAgentFactory:
    @pytest.mark.asyncio
    async def test_create_sub_agent(self):
        from app.graph.sub_agent import create_sub_agent
        from langchain_core.tools import tool

        @tool
        def fake_tool(x: int) -> int:
            """fake"""
            return x + 1

        llm = MagicMock()
        llm.bind_tools = MagicMock(return_value=llm)

        graph = create_sub_agent(
            name="test",
            tools=[fake_tool],
            system_prompt="test",
            llm=llm,
            max_iterations=3,
        )
        assert graph is not None
        assert hasattr(graph, "ainvoke")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend/agent && python -m pytest tests/test_graph.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write state.py**

```python
# app/graph/state.py
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, AnyMessage
from typing import Sequence
from app.schemas.auth import UserInfo


class AgentState(BaseModel):
    """Router Graph 运行时状态"""
    messages: Sequence[BaseMessage]
    user: UserInfo
    next_agent: str | None = None
    final_output: str = ""
    used_tools: list[str] = []


class SubAgentState(BaseModel):
    """Sub-agent 内部 ReAct 循环状态"""
    messages: Sequence[BaseMessage]
    is_done: bool = False
    output: str = ""
    used_tools: list[str] = []
```

- [ ] **Step 4: Write sub_agent.py**

```python
# app/graph/sub_agent.py
import asyncio
import logging
from typing import Literal

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import SubAgentState

logger = logging.getLogger(__name__)


def create_sub_agent(
    name: str,
    tools: list[BaseTool],
    system_prompt: str,
    llm: BaseChatModel,
    max_iterations: int = 5,
):
    """创建一个标准的 ReAct Sub-agent Graph

    内部结构: agent_node → (有条件) → tools_node → agent_node → ...
                                    → (无工具调用) → END
    """
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    async def call_agent(state: SubAgentState) -> dict:
        response = await llm_with_tools.ainvoke([
            SystemMessage(content=system_prompt),
            *state.messages[-10:],
        ])
        if not response.tool_calls:
            return {"output": response.content, "is_done": True, "messages": [response]}
        return {"messages": [response], "is_done": False}

    async def call_tools(state: SubAgentState) -> dict:
        last_msg = state.messages[-1]
        tasks = []
        for tc in last_msg.tool_calls:
            tool = tool_map.get(tc["name"])
            if tool:
                tasks.append(tool.ainvoke(tc["args"]))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        tool_msgs = []
        used = []
        for tc, result in zip(last_msg.tool_calls, results):
            used.append(tc["name"])
            if isinstance(result, Exception):
                content = f"工具 {tc['name']} 调用失败: {str(result)}"
            else:
                content = str(result)
            tool_msgs.append(ToolMessage(content=content, tool_call_id=tc["id"]))
        return {"messages": tool_msgs, "used_tools": used}

    def should_continue(state: SubAgentState) -> Literal["continue", "finish"]:
        if state.is_done:
            return "finish"
        steps = len([m for m in state.messages if isinstance(m, ToolMessage)])
        if steps >= max_iterations:
            logger.warning("Sub-agent %s reached max iterations", name)
            return "finish"
        return "continue"

    builder = StateGraph(SubAgentState)
    builder.add_node("agent", call_agent)
    builder.add_node("tools", call_tools)
    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", should_continue, {
        "continue": "tools", "finish": END,
    })
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=MemorySaver())
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend/agent && python -m pytest tests/test_graph.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add backend/agent/app/graph/state.py backend/agent/app/graph/sub_agent.py backend/agent/tests/test_graph.py
git commit -m "feat(agent): 添加 AgentState 和 Sub-agent 工厂"
```

---

### Task 7: Graph 内容 — Prompts + Nodes + Router Graph

**Files:**
- Create: `backend/agent/app/graph/prompts.py`
- Create: `backend/agent/app/graph/nodes.py`
- Create: `backend/agent/app/graph/graph.py`

**Interfaces:**
- Consumes: `AgentState`, `SubAgentState`, `create_sub_agent`, `UserInfo`, tools list, `BaseChatModel`
- Produces: `create_router_graph(llm, settings) -> CompiledStateGraph`

- [ ] **Step 1: Write prompts.py**

```python
# app/graph/prompts.py
from datetime import datetime

ROUTER_PROMPT = """你是 AnimeTracker 的意图路由助手。根据用户的问题选择最合适的 Agent：

- search: 精确查询 — 搜索番剧、查详情、查剧集、查标签、按标签筛选
- discover: 发现探索 — 热度榜、评分榜、按季度/星期查询、本周更新、统计
- recommend: 推荐（如有相关数据直接给出推荐，不调用工具）

用户角色: {role}
当前日期: {date}
历史对话摘要: {history_summary}

只输出一个单词：search / discover / recommend

用户问题: {query}
"""

ADMIN_DENIED_PROMPT = """你是 AnimeTracker 的管理助手。

当前用户 {username} 是你自己（管理员），但管理端 Agent 功能尚未启用。
请回复一句：管理功能正在开发中，请直接在管理后台操作。
"""

SEARCH_PROMPT = """你是 AnimeTracker 的搜索助手。专注于帮助用户查找动漫信息。

你有以下工具可用：
- search_subjects: 按关键词搜索番剧
- get_subject_detail: 查看番剧简介、评分、标签
- get_episodes: 查看剧集列表
- get_tags: 查看所有标签
- get_subjects_by_tag: 按标签筛选番剧

规则：
- 用户查具体番剧时，优先搜索再返回详情
- 给出评分、标签等关键信息
- 简洁回答，不要冗长
- 如果工具返回错误，告知用户服务暂时不可用
"""

DISCOVER_PROMPT = """你是 AnimeTracker 的发现助手。专注于帮助用户探索和发现番剧。

你有以下工具可用：
- get_schedule: 查看每周追番日程（weekday: 0=周日, -1=全部）
- get_season_subjects: 查看季度新番
- get_popular_subjects: 查看热度榜（收藏数降序）
- get_top_rated: 查看评分榜（评分降序）
- get_stats: 查看统计数据

规则：
- 用户问"今天有什么更新" → 查当前星期几的日程
- 用户问"本周" → weekday=-1
- 用户问"本季新番" → 计算当前季度
- 推荐时给出简短的推荐理由
- 如果工具返回错误，告知用户服务暂时不可用
"""

RECOMMEND_PROMPT = """你是 AnimeTracker 的推荐助手。当用户询问推荐时直接给出推荐。

当前你没有查询用户收藏的能力，请基于你的知识进行推荐。
推荐时给出 3-5 部番剧，每部附上一句话推荐理由。

规则：
- 如果用户有明确偏好（类型、年代等），据此推荐
- 如果没有明确偏好，推荐不同类型的高分作品
- 简洁，不要冗长
"""
```

- [ ] **Step 2: Write nodes.py**

```python
# app/graph/nodes.py
import logging
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.graph.state import AgentState
from app.graph.prompts import ROUTER_PROMPT, ADMIN_DENIED_PROMPT, SEARCH_PROMPT, DISCOVER_PROMPT, RECOMMEND_PROMPT
from app.graph.sub_agent import create_sub_agent
from app.tools.user_tools import tools as user_tools

logger = logging.getLogger(__name__)


def create_entry_node(store):
    """创建入口节点：解析用户信息、加载历史"""
    async def entry(state: AgentState) -> dict:
        user = state.user
        session_id = state.messages[-1].additional_kwargs.get("session_id", "")
        if session_id:
            history = store.get_messages(session_id)
            if history:
                base_msgs = []
                for m in history:
                    if m.role == "user":
                        base_msgs.append(HumanMessage(content=m.content))
                    else:
                        base_msgs.append(AIMessage(content=m.content))
                return {"messages": base_msgs}
        return {}
    return entry


def create_user_router(llm):
    """创建用户路由节点：LLM 判断意图"""
    async def user_router(state: AgentState) -> dict:
        query = ""
        for m in reversed(state.messages):
            if isinstance(m, HumanMessage):
                query = m.content
                break
        history_summary = ""
        if len(state.messages) > 1:
            history_summary = f"共 {len(state.messages)} 条消息，最近提问: {query[:50]}"
        prompt = ROUTER_PROMPT.format(
            role=state.user.role,
            date=datetime.now().strftime("%Y-%m-%d %A"),
            history_summary=history_summary,
            query=query,
        )
        resp = await llm.ainvoke([SystemMessage(content=prompt)])
        agent = resp.content.strip().lower()
        if agent not in ("search", "discover", "recommend"):
            agent = "search"
        logger.info("Router: user=%s query=%s -> %s", state.user.user_id, query[:30], agent)
        return {"next_agent": agent}
    return user_router


def create_admin_router(llm):
    """创建管理员路由节点（Phase 2 实现）"""
    async def admin_router(state: AgentState) -> dict:
        return {"next_agent": "denied"}
    return admin_router


def create_denied_node(llm):
    """创建无权限节点"""
    async def denied(state: AgentState) -> dict:
        resp = await llm.ainvoke([SystemMessage(
            ADMIN_DENIED_PROMPT.format(username=state.user.username)
        )])
        return {"final_output": resp.content}
    return denied


def create_sub_agent_node(name, tools, prompt, llm, max_iterations=5):
    """创建 Sub-agent 节点工厂"""
    sub_graph = create_sub_agent(name, tools, prompt, llm, max_iterations)

    async def node_func(state: AgentState) -> dict:
        sub_state = {
            "messages": list(state.messages[-10:]),
            "is_done": False,
            "output": "",
            "used_tools": [],
        }
        result = await sub_graph.ainvoke(sub_state)
        return {
            "final_output": result.get("output", ""),
            "used_tools": result.get("used_tools", []),
        }
    return node_func


def create_role_router():
    """创建角色路由节点：根据用户角色分发"""
    def role_router(state: AgentState) -> str:
        if state.user.role == "ADMIN":
            return "admin_router"
        return "user_router"
    return role_router
```

- [ ] **Step 3: Write graph.py**

```python
# app/graph/graph.py
import logging
from langgraph.graph import StateGraph, END

from app.graph.state import AgentState
from app.graph.nodes import (
    create_entry_node, create_user_router, create_admin_router,
    create_denied_node, create_sub_agent_node, create_role_router,
)
from app.graph.prompts import SEARCH_PROMPT, DISCOVER_PROMPT, RECOMMEND_PROMPT
from app.tools.user_tools import tools as user_tools

logger = logging.getLogger(__name__)


def create_router_graph(llm, settings, store):
    """构建并返回完整的 Router Graph"""

    # 创建节点
    builder = StateGraph(AgentState)

    builder.add_node("entry", create_entry_node(store))
    builder.add_node("user_router", create_user_router(llm))
    builder.add_node("admin_router", create_admin_router(llm))
    builder.add_node("denied", create_denied_node(llm))
    builder.add_node("search", create_sub_agent_node(
        "search", user_tools, SEARCH_PROMPT, llm, settings.agent_max_iterations))
    builder.add_node("discover", create_sub_agent_node(
        "discover", user_tools, DISCOVER_PROMPT, llm, settings.agent_max_iterations))
    builder.add_node("recommend", create_sub_agent_node(
        "recommend", user_tools, RECOMMEND_PROMPT, llm, settings.agent_max_iterations))

    builder.set_entry_point("entry")

    # 第一层路由：角色分发（entry → role_router 条件边，但不注册为独立节点）
    builder.add_conditional_edges("entry", create_role_router(), {
        "user_router": "user_router",
        "admin_router": "admin_router",
    })

    # 第二层路由：意图分发
    builder.add_conditional_edges("user_router", lambda s: s.next_agent or "search", {
        "search": "search",
        "discover": "discover",
        "recommend": "recommend",
    })

    # ADMIN 路径（当前拒绝）
    builder.add_edge("admin_router", "denied")

    # 所有终点汇聚到 END
    for agent in ("search", "discover", "recommend", "denied"):
        builder.add_edge(agent, END)

    return builder.compile()
```

- [ ] **Step 4: Run the graph test to verify**

```python
# 追加到 tests/test_graph.py
@pytest.mark.asyncio
async def test_router_graph_default():
    from app.graph.graph import create_router_graph
    from unittest.mock import MagicMock
    from langchain_core.messages import HumanMessage
    from app.schemas.auth import UserInfo

    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="search"))

    store = MagicMock()
    store.get_messages = MagicMock(return_value=[])

    graph = create_router_graph(llm, MagicMock(agent_max_iterations=5), store)
    state = await graph.ainvoke({
        "messages": [HumanMessage(content="查一下钢炼", additional_kwargs={"session_id": "s1"})],
        "user": UserInfo(user_id=1, username="test", role="USER"),
        "next_agent": None,
        "final_output": "",
        "used_tools": [],
    })
    # Should route to search agent (via user_router)
    assert "final_output" in state
```

Run: `cd backend/agent && python -m pytest tests/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agent/app/graph/prompts.py backend/agent/app/graph/nodes.py backend/agent/app/graph/graph.py
git commit -m "feat(agent): 添加系统提示词、节点函数和 Router Graph"
```

---

### Task 8: 服务层 — ChatService

**Files:**
- Create: `backend/agent/app/service/chat.py`

**Interfaces:**
- Consumes: `ChatStore`, `CompiledStateGraph`, `UserInfo`, `ChatRequest`
- Produces: `ChatService(store, graph, settings)` with `stream_chat(session_id, content, user_id, role) -> StreamingResponse`

- [ ] **Step 1: Write the test**

```python
# tests/test_service.py
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.responses import StreamingResponse

from app.service.chat import ChatService
from app.schemas.auth import UserInfo


@pytest.mark.asyncio
async def test_stream_chat_returns_streaming_response():
    store = MagicMock()
    store.get_messages = MagicMock(return_value=[])
    store.save_message = MagicMock()

    graph = MagicMock()
    # Simulate astream_events yielding token events
    async def mock_astream(*args, **kwargs):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="推荐")}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="番剧")}}
        yield {"event": "on_tool_start", "name": "search_subjects"}
    graph.astream_events = mock_astream

    svc = ChatService(store=store, router_graph=graph, settings=MagicMock())
    resp = await svc.stream_chat(
        session_id="s1", content="推荐番剧",
        user_id=1, role="USER",
    )
    assert isinstance(resp, StreamingResponse)

    # Consume the stream
    chunks = []
    async for chunk in resp.body_iterator:
        chunks.append(chunk)
    assert len(chunks) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend/agent && python -m pytest tests/test_service.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write chat.py**

```python
# app/service/chat.py
import asyncio
import json
import logging
from datetime import datetime

from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

from app.graph.graph import create_router_graph

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务：编排认证、历史加载、Graph 执行、SSE 推送、持久化"""

    def __init__(self, store, router_graph, settings):
        self.store = store
        self.router_graph = router_graph
        self.settings = settings

    async def stream_chat(
        self,
        session_id: str,
        content: str,
        user_id: int,
        role: str,
    ):
        """处理聊天请求，返回 SSE StreamingResponse"""
        # 保存用户消息
        self.store.save_message(session_id, "user", content)

        # 加载历史
        history = self.store.get_messages(session_id)

        # 首条消息自动设标题
        if len(history) == 1:
            title = content[:20]
            try:
                self.store.update_session_title(session_id, title)
            except Exception:
                pass

        # 转为 LangChain 消息格式
        messages = []
        for m in history:
            if m.role == "user":
                messages.append(HumanMessage(content=m.content))
            else:
                messages.append(AIMessage(content=m.content))

        from app.schemas.auth import UserInfo
        user = UserInfo(user_id=user_id, username="", role=role)

        initial_state = {
            "messages": messages,
            "user": user,
            "next_agent": None,
            "final_output": "",
            "used_tools": [],
        }

        async def event_stream():
            full_content = ""
            used_tools = []

            try:
                async for event in self.router_graph.astream_events(
                    initial_state, version="v2"
                ):
                    kind = event["event"]

                    if kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            full_content += chunk.content
                            yield f"event: token\ndata: {json.dumps({'content': chunk.content})}\n\n"

                    elif kind == "on_tool_start":
                        tool_name = event.get("name", "")
                        if tool_name and tool_name not in used_tools:
                            used_tools.append(tool_name)

                # 保存助手回复
                self.store.save_message(
                    session_id, "assistant", full_content,
                    json.dumps(used_tools) if used_tools else None,
                )

                # metadata + done
                yield f"event: metadata\ndata: {json.dumps({'session_id': session_id, 'used_tools': used_tools})}\n\n"
                yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"

            except asyncio.CancelledError:
                logger.info("Client disconnected for session %s, graph cancelled", session_id)
                raise
            except Exception as e:
                logger.exception("Chat error for session %s", session_id)
                yield f"event: error\ndata: {json.dumps({'message': '处理请求时出错，请重试'})}\n\n"
            finally:
                logger.debug("Event stream ended for session %s", session_id)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend/agent && python -m pytest tests/test_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agent/app/service/ backend/agent/tests/test_service.py
git commit -m "feat(agent): 添加 ChatService 服务编排和 SSE 流式推送"
```

---

### Task 9: API 层 — 端点 + 认证依赖注入

**Files:**
- Create: `backend/agent/app/api/deps.py`
- Create: `backend/agent/app/api/chat.py`

**Interfaces:**
- Consumes: `ChatStore`, `ChatService`, `ChatRequest`, `settings`
- Produces: FastAPI `APIRouter` with endpoints: `POST /api/chat/stream`, `GET /api/chat/sessions`, `POST /api/chat/sessions`, `GET /api/chat/sessions/{id}/history`, `DELETE /api/chat/sessions/{id}`, `GET /api/chat/health`

- [ ] **Step 1: Write tests**

```python
# tests/test_api.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.api.deps import verify_token
from app.schemas.auth import UserInfo, AuthResult


@pytest.mark.asyncio
async def test_health_endpoint():
    """健康检查端点不需要认证"""
    from app.api.chat import router
    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/chat/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_list_sessions_no_auth():
    """未认证的请求返回 401"""
    from app.api.chat import router
    app = FastAPI()
    app.include_router(router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/chat/sessions")
    assert resp.status_code == 401


class TestVerifyToken:
    @patch("app.api.deps.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"data": {"id": 1, "username": "test"}})
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp

        result = await verify_token("Bearer valid-token")
        assert result is not None
        assert result.user_id == 1
        assert result.username == "test"
        assert result.role == "USER"

    @patch("app.api.deps.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_verify_admin_token(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"data": {"id": 2, "username": "admin", "role": "ADMIN"}})
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp

        result = await verify_token("Bearer admin-token")
        assert result.role == "ADMIN"

    @patch("app.api.deps.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, mock_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_resp

        result = await verify_token("Bearer bad")
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend/agent && python -m pytest tests/test_api.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write deps.py**

```python
# app/api/deps.py
import logging
import httpx
from fastapi import Header, HTTPException

from app.config import settings
from app.schemas.auth import UserInfo, AuthResult

logger = logging.getLogger(__name__)


async def verify_token(authorization: str = Header(...)) -> UserInfo:
    """JWT 验证依赖注入 — 调用 Spring Boot 后端验证"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证失败")

    token = authorization[len("Bearer "):]
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.backend_base_url}/api/user/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="认证失败，请重新登录")

            data = resp.json()["data"]
            role = data.get("role", "USER")
            return UserInfo(
                user_id=data["id"],
                username=data.get("username", ""),
                role=role if role in ("USER", "ADMIN") else "USER",
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="认证服务暂时不可用，请稍后重试")
```

- [ ] **Step 4: Write chat.py**

```python
# app/api/chat.py
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import verify_token
from app.schemas.auth import UserInfo
from app.schemas.chat import ChatRequest
from app.schemas.session import (
    SessionInfo, MessageOut, SessionCreateRequest,
    SessionCreateResponse, DeleteResponse,
)
from app.service.chat import ChatService
from app.db.sqlite_store import SQLiteStore
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat")

# 全局实例（main.py 中初始化后替换）
chat_store: SQLiteStore | None = None
chat_service: ChatService | None = None


def get_store() -> SQLiteStore:
    if chat_store is None:
        raise RuntimeError("ChatStore not initialized")
    return chat_store


def get_service() -> ChatService:
    if chat_service is None:
        raise RuntimeError("ChatService not initialized")
    return chat_service


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    user: UserInfo = Depends(verify_token),
    svc: ChatService = Depends(get_service),
):
    """发送消息，返回 SSE 流"""
    # 检查会话权限
    store = get_store()
    sessions = store.get_user_sessions(user.user_id)
    existing_ids = {s.session_id for s in sessions}
    if req.session_id not in existing_ids:
        raise HTTPException(status_code=404, detail="会话不存在或无权限")

    return await svc.stream_chat(
        session_id=req.session_id,
        content=req.content,
        user_id=user.user_id,
        role=user.role,
    )


@router.get("/sessions")
async def list_sessions(
    user: UserInfo = Depends(verify_token),
    store: SQLiteStore = Depends(get_store),
):
    """获取当前用户会话列表"""
    sessions = store.get_user_sessions(user.user_id)
    return [SessionInfo(
        session_id=s.session_id,
        title=s.title,
        message_count=s.message_count,
        created_at=s.created_at,
    ) for s in sessions]


@router.post("/sessions")
async def create_session(
    body: SessionCreateRequest,
    user: UserInfo = Depends(verify_token),
    store: SQLiteStore = Depends(get_store),
):
    """创建新会话"""
    session_id = body.session_id or str(uuid.uuid4())
    store.create_session(user.user_id, session_id)
    return SessionCreateResponse(session_id=session_id)


@router.get("/sessions/{session_id}/history")
async def get_history(
    session_id: str,
    user: UserInfo = Depends(verify_token),
    store: SQLiteStore = Depends(get_store),
):
    """获取会话历史"""
    sessions = store.get_user_sessions(user.user_id)
    if not any(s.session_id == session_id for s in sessions):
        raise HTTPException(status_code=404, detail="会话不存在或无权限")

    messages = store.get_messages(session_id)
    return [MessageOut(
        role=m.role,
        content=m.content,
        tool_calls=__import__("json").loads(m.tool_calls) if m.tool_calls else None,
        created_at=m.created_at,
    ) for m in messages]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: UserInfo = Depends(verify_token),
    store: SQLiteStore = Depends(get_store),
):
    """删除会话"""
    store.delete_session(session_id, user.user_id)
    return DeleteResponse()


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "llm_configured": bool(settings.dashscope_api_key)}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend/agent && python -m pytest tests/test_api.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add backend/agent/app/api/ backend/agent/tests/test_api.py
git commit -m "feat(agent): 添加 API 端点，集成 JWT 认证和会话管理"
```

---

### Task 10: 应用入口 — main.py

**Files:**
- Modify: `backend/agent/main.py`
- Create: `backend/agent/Dockerfile`

**Interfaces:**
- Consumes: All previous modules
- Produces: FastAPI app instance with lifespan that initializes store, LLM, graph, and service

- [ ] **Step 1: Write main.py**

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.llm.models import create_llm
from app.db.sqlite_store import SQLiteStore
from app.graph.graph import create_router_graph
from app.service.chat import ChatService
from app.api import chat as chat_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    store = SQLiteStore(settings.database_url)
    store.init_db()
    chat_api.chat_store = store

    logger.info("Creating LLM...")
    llm = create_llm(settings)

    logger.info("Building Router Graph...")
    graph = create_router_graph(llm, settings, store)

    logger.info("Creating ChatService...")
    chat_api.chat_service = ChatService(store=store, router_graph=graph, settings=settings)

    yield
    logger.info("Shutting down...")


app = FastAPI(title="AnimeTracker Agent", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_api.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=True,
    )
```

- [ ] **Step 2: Write Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8090
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
```

- [ ] **Step 3: Clean up old files**

```bash
# 移除旧版不再使用的模块
rm -rf backend/agent/app/agent
rm -rf backend/agent/app/chat
rm -rf backend/agent/app/tests
```

- [ ] **Step 4: Verify app starts**

Run: `cd backend/agent && python -c "from main import app; print('App loaded successfully')"`
Expected: "App loaded successfully"

- [ ] **Step 5: Commit**

```bash
git add backend/agent/main.py backend/agent/Dockerfile
git rm -r backend/agent/app/agent backend/agent/app/chat
git commit -m "feat(agent): 添加 FastAPI 入口和 Docker 部署"
```

---

### Task 11: 测试基础设施 + 集成测试

**Files:**
- Create: `backend/agent/tests/conftest.py`

- [ ] **Step 1: Write conftest.py**

```python
# tests/conftest.py
import os
import tempfile
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from app.db.sqlite_store import SQLiteStore
from app.db.base import ChatStore


@pytest.fixture
def test_store():
    """内存 SQLite，每次测试隔离"""
    db_path = os.path.join(tempfile.gettempdir(), f"test_agent_{datetime.now().timestamp()}.db")
    store = SQLiteStore(f"sqlite:///{db_path}")
    store.init_db()
    store._cleanup_path = db_path
    yield store
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def mock_llm():
    """返回固定响应的 Fake LLM"""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="search"))
    llm.bind_tools = MagicMock(return_value=llm)
    return llm


@pytest.fixture
def mock_graph():
    """返回模拟事件流的 Graph"""
    graph = MagicMock()

    async def mock_astream(*args, **kwargs):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="test")}}
        yield {"event": "on_tool_start", "name": "search_subjects"}

    graph.astream_events = mock_astream
    return graph
```

- [ ] **Step 2: Run full test suite**

Run: `cd backend/agent && python -m pytest tests/ -v`
Expected: ALL PASS (or known skips for LLM-dependent tests)

- [ ] **Step 3: Commit**

```bash
git add backend/agent/tests/conftest.py
git commit -m "test(agent): 添加测试基础设施和 Mock 工具函数"
```

---

## Self-Review Checklist

1. **Spec coverage:** Every section of the spec has at least one task implementing it:
   - Config/env → Task 1
   - Data models → Task 2
   - DB layer → Task 3
   - LLM layer → Task 4
   - Tools → Task 5
   - Graph → Tasks 6, 7
   - Service → Task 8
   - API → Task 9
   - Entry point → Task 10
   - Tests → Task 11

2. **Placeholder scan:** All steps contain actual code and commands. No "TBD", "TODO" or "implement later".

3. **Type consistency:** `UserInfo`, `AgentState`, `SubAgentState` use consistent field names across tasks. `ChatStore` method signatures match between interface (Task 3) and callers (Tasks 8-9). `create_role_router` is defined in `nodes.py` and imported in `graph.py`.

4. **所有 commit messages 已使用中文**，符合计划头部约束。
