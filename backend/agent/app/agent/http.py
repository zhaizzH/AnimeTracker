import httpx

from app.config import settings

BASE = settings.backend_base_url


def call_api(method: str, path: str, params: dict | None = None, token: str | None = None) -> dict | list:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = httpx.request(method, f"{BASE}{path}", params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        body = resp.json()
    except httpx.TimeoutException:
        return {"error": True, "message": "后端服务超时"}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return {"error": True, "code": 401, "message": "登录已过期，请重新登录"}
        try:
            error_body = e.response.json()
        except ValueError:
            error_body = {}
        return {
            "error": True,
            "code": error_body.get("code", e.response.status_code),
            "message": error_body.get("message", f"后端返回错误: {e.response.status_code}"),
        }
    except httpx.RequestError as e:
        return {"error": True, "message": f"后端服务不可用: {str(e)}"}
    return body.get("data", body)
