import httpx
import respx

from app.agent import http


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
