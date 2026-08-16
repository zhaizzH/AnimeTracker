"""Agent 可观测性: trace 上下文、结构化 JSON 事件与计时辅助。

隐私红线: 事件日志绝不记录用户输入、JWT/API key、工具参数、完整回答或 Business 响应体。
所有字段必须经过 _ALLOWED_FIELDS 白名单过滤,None 值省略。
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from contextvars import ContextVar, Token

logger = logging.getLogger(__name__)

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_session_hash: ContextVar[str | None] = ContextVar("session_hash", default=None)
_user_hash: ContextVar[str | None] = ContextVar("user_hash", default=None)

# 事件字段白名单(隐私红线)。P1: token 字段来自 spec usage;Task3 请求事件要求
# sessionHash/userHash/toolCount。
_ALLOWED_FIELDS = {
    "provider", "model", "slot", "durationMs", "firstTokenMs",
    "success", "errorType", "toolName", "routeTarget", "businessStatus",
    "inputTokens", "outputTokens", "totalTokens",
    "sessionHash", "userHash", "toolCount",
}

# 服务端固定 salt(不可逆摘要;无 salt 配置时上层省略 sessionHash/userHash 字段)
_HASH_SALT = "animetracker-agent-observability-salt-v1"


def set_trace_context(trace_id: str | None, session_id: str | None = None, user_id: str | None = None) -> Token:
    """建立请求级 trace 上下文;返回传给 reset_trace_context 的 token。

    session_id/user_id 仅记录匿名哈希(服务端固定 salt 的不可逆摘要),绝不记录原文。
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


def hash_value(value: str | None) -> str | None:
    """服务端固定 salt 的不可逆摘要(sha256 截断);值为空时返回 None,调用方省略字段。"""
    if not value:
        return None
    return hashlib.sha256(f"{_HASH_SALT}:{value}".encode("utf-8")).hexdigest()[:16]


def provider_from_model(model: str | None) -> str | None:
    """生产约定: 模型名以 deepseek/ 开头 → deepseek,否则 dashscope。

    注: ChatDeepSeek 在创建时被剥掉 `deepseek/` 前缀,故同时识别 `deepseek-` 前缀。
    """
    if not model:
        return None
    m = str(model).strip().lower()
    if m.startswith("deepseek/") or m.startswith("deepseek-"):
        return "deepseek"
    return "dashscope"


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
    """spec 固定错误类别映射(在日志边界归一化,不建立异常继承树)。"""
    if isinstance(exc, asyncio.CancelledError):
        return "CLIENT_DISCONNECTED"
    if isinstance(exc, TimeoutError):
        return "MODEL_TIMEOUT"
    if isinstance(exc, (ValueError, TypeError)):
        return "MODEL_RESPONSE_INVALID"
    return "INTERNAL_ERROR"


def log_event(event: str, **fields) -> None:
    """输出单行结构化 JSON 事件;仅白名单字段被写入,None 值省略。"""
    payload = {"service": "agent", "event": event, "traceId": _trace_id.get()}
    payload.update({k: v for k, v in fields.items() if k in _ALLOWED_FIELDS})
    payload = {k: v for k, v in payload.items() if v is not None}
    logger.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


async def trace_context_middleware(request, call_next):
    """FastAPI http 中间件: 读取/生成 X-Request-ID 写入 ContextVar,响应头回写同值。"""
    request_id = (request.headers.get("X-Request-ID") or "").strip()
    if not request_id:
        request_id = str(uuid.uuid4())
    token = set_trace_context(request_id)
    try:
        response = await call_next(request)
    finally:
        reset_trace_context(token)
    response.headers["X-Request-ID"] = request_id
    return response
