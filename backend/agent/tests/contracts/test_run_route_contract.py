"""Java 对外 chat run 路由契约：六条代理路由及其 SSE/冲突响应不得回退。"""

from __future__ import annotations

import pytest

from tests.contracts import _contract

RUN_STREAM_PATHS = (
    "/api/client/agent/runs/{runId}/stream",
    "/api/admin/agent/chat/runs/{runId}/stream",
)
SESSION_RUN_PATHS = (
    "/api/client/agent/sessions/{sessionId}/run",
    "/api/admin/agent/chat/sessions/{sessionId}/run",
)
STOP_PATHS = (
    "/api/client/agent/runs/{runId}/stop",
    "/api/admin/agent/chat/runs/{runId}/stop",
)
STREAM_PATHS = ("/api/client/agent/stream", "/api/admin/agent/chat/stream")


def _operation(path: str, method: str) -> dict:
    """按契约中的字面路径取 operation，避免通配匹配掩盖缺失路由。"""
    item = _contract.contract_paths().get(path)
    assert isinstance(item, dict), f"缺少 run 路由：{path}"
    operation = item.get(method.lower())
    assert isinstance(operation, dict), f"缺少 {method.upper()} {path}"
    return operation


def _response_schema(operation: dict, status: str, content_type: str) -> dict:
    """取指定状态和媒体类型的响应 schema。"""
    content = operation["responses"][status]["content"]
    return content[content_type]["schema"]


@pytest.mark.parametrize("path", RUN_STREAM_PATHS)
def test_run_stream_declares_after_query_and_sse(path: str) -> None:
    operation = _operation(path, "get")
    parameters = operation.get("parameters") or []
    after = next((p for p in parameters if p.get("name") == "after"), None)
    assert after is not None, f"{path} 未声明 after 查询参数"
    assert after["in"] == "query"
    assert after["schema"]["type"] == "integer"
    schema = _response_schema(operation, "200", "text/event-stream")
    assert schema.get("$ref") == "#/components/schemas/SSEFrame"


@pytest.mark.parametrize("path", SESSION_RUN_PATHS)
def test_session_run_declares_state_response(path: str) -> None:
    operation = _operation(path, "get")
    schema = _response_schema(operation, "200", "application/json")
    data = schema["properties"]["data"]
    resolved = _contract.resolve_ref(data["$ref"]) if "$ref" in data else data
    assert {"run_id", "status"}.issubset(resolved["properties"])
    assert set(resolved["properties"]["status"]["enum"]) == {
        "running", "done", "failed", "cancelled"
    }


@pytest.mark.parametrize("path", STOP_PATHS)
def test_stop_declares_cancelled_response(path: str) -> None:
    operation = _operation(path, "post")
    schema = _response_schema(operation, "200", "application/json")
    data = schema["properties"]["data"]
    resolved = _contract.resolve_ref(data["$ref"]) if "$ref" in data else data
    assert {"run_id", "status"}.issubset(resolved["properties"])
    assert resolved["properties"]["status"].get("enum") == ["cancelled"]


@pytest.mark.parametrize("path", STREAM_PATHS)
def test_stream_declares_structured_conflict_response(path: str) -> None:
    operation = _operation(path, "post")
    schema = _response_schema(operation, "409", "application/json")
    resolved = _contract.resolve_ref(schema["$ref"]) if "$ref" in schema else schema
    assert {"code", "message", "data"}.issubset(resolved["properties"])
    data = resolved["properties"]["data"]
    data = _contract.resolve_ref(data["$ref"]) if "$ref" in data else data
    assert {"active_run_id", "status", "capabilities"}.issubset(data["properties"])
    assert data["properties"]["capabilities"]["items"].get("enum") == ["interrupt"]
