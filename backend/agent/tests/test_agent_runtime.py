from langchain_core.messages import AIMessage, AIMessageChunk

from app.core.agent.agent_runtime import agent_invoke, agent_stream


class FakeStreamAgent:
    async def astream(self, payload, stream_mode=None):
        yield ("messages", (AIMessageChunk(content="你"), {"langgraph_node": "model"}))
        yield ("messages", (AIMessageChunk(content="好"), {"langgraph_node": "model"}))
        yield ("values", {"messages": [AIMessage(content="你好")]})


class FakeInvokeAgent:
    async def ainvoke(self, payload):
        return {"messages": [AIMessage(content="回答")]}


def test_agent_stream_collects_text():
    result = agent_stream(FakeStreamAgent(), [])
    assert result["streamed_text"] == "你好"
    assert result["final_messages"][0].content == "你好"


def test_agent_stream_callback():
    deltas = []
    agent_stream(FakeStreamAgent(), [], on_model_delta=deltas.append)
    assert "".join(deltas) == "你好"


def test_agent_invoke_extracts_content():
    result = agent_invoke(FakeInvokeAgent(), [])
    assert result.content == "回答"


def test_extract_text_multimodal_ignored():
    from app.core.agent.agent_runtime import extract_text
    chunk = AIMessageChunk(content=[{"type": "text", "text": "hi"}])
    assert extract_text(chunk) == "hi"
