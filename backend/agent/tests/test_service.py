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
