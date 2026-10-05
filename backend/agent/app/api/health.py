"""``GET /api/client/agent/health`` 的依赖感知健康报告。

该接口始终返回 HTTP 200，并在响应体中表达降级。这是对
"HTTP 状态码必须与错误码一致"规则的有意例外：它是诊断接口而非业务响应，
且没有常驻调用方依赖其状态码（参见 ``error-handling.md`` 与任务笔记）。

探测语义：每个探测都发起真实的依赖调用，受超时约束，并
对任何异常、超时或错误信封报告 ``down``。
``checks`` 只包含有限枚举 ``ok``/``down``/``disabled``，
绝不含异常文本，以免泄漏上游响应体与连接串。
被禁用的功能开关是 ``disabled``，绝不是 ``down``。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Mapping

from app.adapters.redis.vector_set import probe_vector_set_commands
from app.config import resolve_llm_provider

logger = logging.getLogger(__name__)

# 业务侧存活检查只回答"业务 HTTP 进程是否可达"，不聚合业务自身的
# MySQL/Redis 就绪状态。探测默认的 ``/actuator/health`` 会把业务内部
# 的 DB 抖动误报成 Agent 依赖故障。该路径在业务 SecurityConfig 中为
# permitAll，因此匿名 Agent 探测无需令牌。
BUSINESS_LIVENESS_PATH = "/actuator/health/liveness"

# 单个探测的上限。Redis 的连接已在 2s 处封顶（``RedisChatStore``）；
# 仅健康检查把业务侧收窄到同一值（业务调用仍保持 10s 默认）。
PROBE_TIMEOUT_SECONDS = 2.0
# 整体上限，保证即使某个探测忽略自身超时，接口也不会挂住。
# 覆盖 Redis 预算并留有余量，且远低于业务侧 10s 默认值。
TOTAL_TIMEOUT_SECONDS = 3.0

_PROBE_NAMES = ("redis", "business", "rag")
_DOWN = "down"


async def build_health_report(
    *,
    settings_obj: Any,
    store: Any,
    business: Any,
    rag_redis: Any,
) -> dict[str, Any]:
    """探测所有依赖并构造稳定的响应载荷。

    依赖对象缺失时按 ``down`` 上报（失败即闭合），而不是让
    ``AttributeError`` 泄漏出去。各探测并发执行且不会短路：
    一个依赖失败不得掩盖其他依赖的状态。
    """
    llm = _probe_llm(settings_obj)
    # 默认失败即闭合；未完成的探测（总预算耗尽或被取消）
    # 其条目保持 ``down``。
    checks: dict[str, str] = {name: _DOWN for name in _PROBE_NAMES}

    async def guarded(name: str, probe: Any) -> None:
        try:
            checks[name] = await asyncio.wait_for(probe, timeout=PROBE_TIMEOUT_SECONDS)
        except Exception:
            # 任何失败——异常、超时、响应格式错误——都记为 ``down``。
            # 只记录类型化枚举，绝不记录异常本身。
            checks[name] = _DOWN

    try:
        await asyncio.wait_for(
            asyncio.gather(
                guarded("redis", _probe_redis(store)),
                guarded("business", _probe_business(business)),
                guarded("rag", _probe_rag(settings_obj, rag_redis)),
            ),
            timeout=TOTAL_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("health 探测超出总预算，未完成分项按 down 报告")

    checks["llm"] = llm
    return {
        "status": "degraded" if any(value == _DOWN for value in checks.values()) else "ok",
        "llm_configured": llm == "ok",
        "checks": checks,
    }


def _probe_llm(settings_obj: Any) -> str:
    """仅配置检查：LLM 没有可探测的网络端点。"""
    try:
        resolve_llm_provider(settings_obj)
    except Exception:
        return _DOWN
    return "ok"


async def _probe_redis(store: Any) -> str:
    """真实 PING。仅构造存储对象不能说明问题：它只解析 URL。"""
    if store is None:
        return _DOWN
    await store.init_db()
    return "ok"


async def _probe_business(business: Any) -> str:
    """真实 HTTP 调用。``request`` 会把失败归一化为错误信封。"""
    if business is None:
        return _DOWN
    response = await asyncio.to_thread(
        business.request,
        "GET",
        BUSINESS_LIVENESS_PATH,
        timeout_seconds=PROBE_TIMEOUT_SECONDS,
    )
    if isinstance(response, Mapping) and response.get("error"):
        return _DOWN
    return "ok"


async def _probe_rag(settings_obj: Any, rag_redis: Any) -> str:
    """条件探测：开关关闭时记为 ``disabled``，不算故障。"""
    if not getattr(settings_obj, "rag_enabled", False):
        return "disabled"
    if rag_redis is None:
        # 开关声称 RAG 已启用，但未装配客户端：这是真实的不一致，
        # 而非功能被禁用。
        return _DOWN
    await asyncio.to_thread(probe_vector_set_commands, rag_redis)
    return "ok"
