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
