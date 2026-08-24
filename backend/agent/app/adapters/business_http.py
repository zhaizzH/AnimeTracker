from __future__ import annotations

import httpx

from app.agent.ports import BusinessGateway
from app.shared.observability import get_trace_id


def _build_headers(token: str | None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    trace_id = get_trace_id()
    if trace_id:
        headers["X-Request-ID"] = trace_id
    return headers


class HttpBusinessGateway(BusinessGateway):
    def __init__(self, base_url: str, timeout_seconds: float = 10.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        token: str | None = None,
        json_body: dict | None = None,
    ) -> dict | list:
        headers = _build_headers(token)
        try:
            resp = httpx.request(
                method,
                f"{self._base_url}{path}",
                params=params,
                json=json_body,
                headers=headers,
                timeout=self._timeout,
            )
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

    def batch_subjects(self, subject_ids: list[int], *, token: str | None, exclude_collected: bool) -> dict | list:
        return self.request(
            "POST",
            "/api/client/subjects/batch",
            token=token,
            json_body={"subjectIds": subject_ids, "excludeCollected": exclude_collected},
        )

    def search_subjects(self, query: str, *, token: str | None, size: int = 15) -> dict | list:
        return self.request(
            "GET",
            "/api/client/subjects/search",
            params={"q": query, "page": 1, "size": size},
            token=token,
        )
