"""Agent 侧请求链路与结构化日志。

- `TraceContextMiddleware`: 接受合法 X-Request-ID 或生成 UUID,存入 ContextVar 与响应头,
  请求结束在 finally 中清理,避免协程复用污染。
- `configure_logging`: 单行结构化 JSON 输出到 stdout/stderr,绝不包含 JWT、LLM Key、
  提示词或请求体。
"""
import json
import logging
import re
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Callable

SERVICE = "animetracker-agent"
HEADER_X_REQUEST_ID = "X-Request-ID"
_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_SECRET_KEYS = re.compile(r"(?i)(api[_-]?key|secret|password|token|authorization|jwt)")

_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    return _trace_id_var.get()


def _resolve_trace_id(incoming: str | None) -> str:
    if incoming:
        trimmed = incoming.strip()
        if _VALID_ID.match(trimmed):
            return trimmed
    return str(uuid.uuid4())


class TraceContextMiddleware:
    """纯 ASGI 中间件,为每个 HTTP 请求注入 traceId 并回写响应头。

    Streaming/SSE 场景下 BaseHTTPMiddleware 存在缓冲与上下文问题,故采用纯 ASGI 实现。
    """

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        raw_header = next(
            (v for k, v in scope.get("headers", []) if k == b"x-request-id"), None
        )
        trace_id = _resolve_trace_id(raw_header.decode("utf-8", "replace") if raw_header else None)
        token = _trace_id_var.set(trace_id)

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", trace_id.encode("utf-8")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            _trace_id_var.reset(token)


def _scrub_secrets(value: Any) -> Any:
    """结构化消息中掩码已知密钥字段,防止 JWT / LLM Key 进入日志。"""
    if isinstance(value, dict):
        return {k: ("***" if isinstance(k, str) and _SECRET_KEYS.search(k) else _scrub_secrets(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_secrets(item) for item in value]
    return value


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.msg
        if not isinstance(message, (dict, list)):
            text = record.getMessage()
            try:
                message = json.loads(text)
            except (ValueError, TypeError):
                message = text
        payload = {
            "ts": logging.Formatter.formatTime(self, record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "service": SERVICE,
            "traceId": _trace_id_var.get(),
            "logger": record.name,
            "message": _scrub_secrets(message),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(*, stream: Any = None) -> None:
    """安装单行 JSON 日志处理器;stream 默认 stderr,uvicorn 日志透传到 root。"""
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "uvicorn.asgi"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True
