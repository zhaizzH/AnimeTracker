import httpx
import respx

from app.agent import http
from app.core.observability import reset_trace_context, set_trace_context


@respx.mock
def test_call_api_preserves_result_error_code_and_message():
    respx.post(f"{http.BASE}/api/client/collections/progress-preview/p1/execute").mock(
        return_value=httpx.Response(
            409,
            json={"code": 409, "message": "预览已过期，请重新生成"},
        )
    )

    result = http.call_api(
        "POST", "/api/client/collections/progress-preview/p1/execute", token="tok"
    )

    assert result == {
        "error": True,
        "code": 409,
        "message": "预览已过期，请重新生成",
    }


@respx.mock
def test_call_api_sends_trace_request_id_header():
    respx.get(f"{http.BASE}/api/client/collections/counts").mock(
        return_value=httpx.Response(200, json={"data": {}})
    )
    token = set_trace_context("trace-header-1")
    try:
        http.call_api("GET", "/api/client/collections/counts")
    finally:
        reset_trace_context(token)
    assert respx.calls.last.request.headers["X-Request-ID"] == "trace-header-1"
