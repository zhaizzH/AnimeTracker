"""Agent 可观测性: 请求级 trace 上下文、结构化 JSON 事件与计时辅助。

隐私红线: 事件日志绝不记录用户输入、JWT/API key、工具参数、完整回答或 Business 响应体。
所有字段必须经过 _ALLOWED_FIELDS 白名单过滤，None 值省略。日志输出为单行 JSON，
外层含时间、级别、服务名、traceId、logger 与 message。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import sys
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar, Token

from starlette.requests import Request
from starlette.responses import Response

HEADER_X_REQUEST_ID = "X-Request-ID"
SERVICE_NAME = "animetracker-agent"
_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

logger = logging.getLogger(__name__)

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_session_hash: ContextVar[str | None] = ContextVar("session_hash", default=None)
_user_hash: ContextVar[str | None] = ContextVar("user_hash", default=None)

# 事件字段白名单(隐私红线)。token 字段来自 usage_metadata；请求事件要求
# sessionHash/userHash/toolCount/routeTarget。
_ALLOWED_FIELDS = {
    "provider", "model", "slot", "durationMs", "firstTokenMs",
    "success", "errorType", "toolName", "routeTarget", "businessStatus",
    "inputTokens", "outputTokens", "totalTokens",
    "sessionHash", "userHash", "toolCount",
}

# 服务端固定 salt(不可逆摘要；无配置时上层省略 sessionHash/userHash 字段)
_HASH_SALT = "animetracker-agent-observability-salt-v1"


def set_trace_context(trace_id: str | None, session_id: str | None = None, user_id: str | None = None) -> Token:
    """建立请求级 trace 上下文；返回传给 reset_trace_context 的 token。

    session_id/user_id 仅记录匿名哈希(服务端固定 salt 的不可逆摘要)，绝不记录原文。
    """
    token = _trace_id.set(trace_id)
    if session_id is not None:
        _session_hash.set(hash_value(session_id))
    if user_id is not None:
        _user_hash.set(hash_value(str(user_id)))
    return token


def get_trace_id() -> str | None:
    return _trace_id.get()


def get_session_hash() -> str | None:
    return _session_hash.get()


def get_user_hash() -> str | None:
    return _user_hash.get()


def reset_trace_context(token: Token) -> None:
    _trace_id.reset(token)
    _session_hash.set(None)
    _user_hash.set(None)


def sanitize_trace_id(value: str | None) -> str:
    """接受合法 X-Request-ID(与 Business 同字符集)或生成 UUID；缺失/非法时生成新 UUID。"""
    if value and _VALID_ID.match(value.strip()):
        return value.strip()
    return str(uuid.uuid4())


async def trace_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """校验/生成 traceId，注入 ContextVar 与响应头，请求结束在 finally 中清理 ContextVar。"""
    trace_id = sanitize_trace_id(request.headers.get(HEADER_X_REQUEST_ID))
    token = set_trace_context(trace_id)
    try:
        response = await call_next(request)
        response.headers[HEADER_X_REQUEST_ID] = trace_id
        return response
    finally:
        reset_trace_context(token)


def hash_value(value: str | None) -> str | None:
    """服务端固定 salt 的不可逆摘要(sha256 截断)；值为空时返回 None，调用方省略字段。"""
    if not value:
        return None
    return hashlib.sha256(f"{_HASH_SALT}:{value}".encode("utf-8")).hexdigest()[:16]


def llm_model_name(llm) -> str | None:
    """从 LangChain chat model 对象提取实际模型名(deepseek 模型不带前缀)。"""
    if llm is None:
        return None
    name = getattr(llm, "model_name", None)
    if name:
        return str(name)
    return getattr(llm, "model", None)


def elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def classify_error(exc: BaseException) -> str:
    """统一错误类别映射(在日志边界归一化，不建立异常继承树)。"""
    if isinstance(exc, asyncio.CancelledError):
        return "CLIENT_DISCONNECTED"
    if isinstance(exc, TimeoutError):
        return "MODEL_TIMEOUT"
    if isinstance(exc, (ValueError, TypeError)):
        return "MODEL_RESPONSE_INVALID"
    return "INTERNAL_ERROR"


def log_event(event: str, **fields) -> None:
    """输出单行结构化 JSON 事件；仅白名单字段被写入，None 值省略。"""
    payload = {"service": SERVICE_NAME, "event": event, "traceId": _trace_id.get()}
    payload.update({k: v for k, v in fields.items() if k in _ALLOWED_FIELDS})
    payload = {k: v for k, v in payload.items() if v is not None}
    logger.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


class JsonFormatter(logging.Formatter):
    """单行 JSON 日志外层: timestamp、level、service、traceId、logger、message。"""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "traceId": _trace_id.get(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging() -> None:
    """把 root 与 uvicorn 日志统一为输出单行 JSON 到 stdout。"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        target = logging.getLogger(name)
        target.handlers = [handler]
        target.setLevel(logging.INFO)
        target.propagate = False
