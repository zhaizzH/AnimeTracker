import app.core.agent.agent_event_bus as bus
from app.core.agent.middleware.tool_status import build_tool_status_middleware, tool_call_status
from langchain.agents.middleware import AgentMiddleware


def test_decorator_registers_display_name():
    @tool_call_status(display_name="搜索番剧")
    def search_subjects(query: str):
        return query

    assert search_subjects.__name__ == "search_subjects"


def test_middleware_is_buildable():
    mw = build_tool_status_middleware()
    assert isinstance(mw, AgentMiddleware)


def test_emit_function_call_shape():
    captured = []
    token = bus.set_status_emitter(captured.append)
    try:
        bus.emit_function_call(node="tool:search_subjects", state="start", name="search_subjects", arguments="{}")
    finally:
        bus.reset_status_emitter(token)
    assert captured[0]["content"]["name"] == "search_subjects"
    assert captured[0]["content"]["state"] == "start"
