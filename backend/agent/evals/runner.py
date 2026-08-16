"""确定性离线 Eval 执行器与 CLI。

用法：
    python -m evals.runner --mode offline            # CI 门禁
    ALLOW_LIVE_AGENT_EVAL=true python -m evals.runner --mode live --sample 10

离线模式完全复用生产 build_graph()/gateway/domain agent/PendingAction 边界，
仅替换 LLM 与 call_api 为确定性替身，零网络零副作用。
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Coroutine
from unittest import mock

from pydantic import SecretStr, TypeAdapter, ValidationError

from app.agent import run as agent_run
from app.agent.client import gateway as client_gateway
from app.agent.graph import build_graph
from app.config import ResolvedLlmProviderConfig, resolve_llm_provider, settings
from app.core.event_bus import reset_status_emitter, set_status_emitter
from app.core.observability import classify_error
from app.core.pending_action import (
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.schemas.auth import UserInfo
from app.schemas.pending_action import PendingAction

from evals.adapters import (
    CALL_API_MODULES,
    EvalFakeChatModel,
    build_domain_responses,
    build_route_responses,
    make_fake_call_api,
)
from evals.assertions import BehaviorSnapshot, evaluate
from evals.schema import EvalCase, load_cases

_EVALS_DIR = Path(__file__).resolve().parent
DEFAULT_CASE_PATHS = sorted(str(p) for p in (_EVALS_DIR / "cases").glob("*.yaml"))

_pending_adapter = TypeAdapter(PendingAction)

# 评测假 Key: 仅用于让 resolve_llm_provider 走通真实图路径, 不出现在任何报告/日志中
_EVAL_FAKE_KEY = "eval-key"


def _run_coro(coro: Coroutine) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import contextvars
        from concurrent.futures import ThreadPoolExecutor

        ctx = contextvars.copy_context()
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(ctx.run, asyncio.run, coro).result()
    return asyncio.run(coro)


async def _astream_values(graph: Any, state: dict) -> dict:
    final: dict = {}
    async for mode, chunk in graph.astream(state, stream_mode=["values"]):
        if mode == "values" and isinstance(chunk, dict):
            final = chunk
    return final


def _build_state(case: EvalCase) -> dict:
    raw = case.state or {}
    if "user" in raw and raw.get("user") is None:
        user = None
    else:
        u = raw.get("user") or {}
        user = UserInfo(
            user_id=int(u.get("user_id", 1)),
            username=str(u.get("username", "")),
            role=u.get("role", "USER"),
            token=str(u.get("token", "tok")),
        )
    pending = None
    if raw.get("pending_action"):
        pending = _pending_adapter.validate_python(raw["pending_action"])
    state = {
        "user": user,
        "history_messages": [],
        "current_question": case.input,
        "routing": None,
        "result": "",
        "session_id": "eval",
        "pending_action": pending,
        "pending_preview_id": None,
    }
    if pending is not None and getattr(pending, "type", None) == "COLLECTION_PROGRESS_UPDATE":
        state["pending_preview_id"] = getattr(pending, "preview_id", None)
    return state


def _make_fake_llm(case: EvalCase) -> Any:
    route_responses = build_route_responses(case.expect)
    domain_responses = build_domain_responses(case.expect)

    def fake_llm(slot, **kwargs):
        if slot == "client_route" or getattr(slot, "value", None) == "client_route":
            return EvalFakeChatModel(responses=route_responses)
        return EvalFakeChatModel(responses=domain_responses)

    return fake_llm


def _run_case(case: EvalCase) -> BehaviorSnapshot:
    called_tools: list[str] = []
    tool_arguments: dict[str, dict[str, Any]] = {}
    business_calls: list[tuple[str, str]] = []
    route_target: str | None = None
    answer = ""
    error_category: str | None = None
    pending_event = None

    orig_key = settings.deepseek_api_key
    settings.deepseek_api_key = _EVAL_FAKE_KEY
    emitter_token = set_status_emitter(_make_capture_emitter(called_tools, tool_arguments))
    pending_token = set_pending_action_collector()
    try:
        fake_llm = _make_fake_llm(case)
        fake_call_api = make_fake_call_api(case.fixtures or {}, business_calls.append)
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(client_gateway, "create_agent_chat_llm", fake_llm))
            stack.enter_context(mock.patch.object(agent_run, "create_agent_chat_llm", fake_llm))
            for module_path in CALL_API_MODULES:
                stack.enter_context(mock.patch(f"{module_path}.call_api", fake_call_api))
            graph = build_graph()
            state = _build_state(case)
            try:
                final = _run_coro(_astream_values(graph, state))
                routing = final.get("routing") or {}
                route_target = routing.get("route_target")
                answer = final.get("result") or ""
            except Exception as exc:
                error_category = classify_error(exc)
            pending_event = get_pending_action_event()
    finally:
        reset_pending_action_collector(pending_token)
        reset_status_emitter(emitter_token)
        settings.deepseek_api_key = orig_key

    return BehaviorSnapshot(
        routeTarget=route_target,
        calledTools=called_tools,
        toolArguments=tool_arguments,
        pendingAction=pending_event,
        businessCalls=business_calls,
        answer=answer,
        errorCategory=error_category,
    )


def _make_capture_emitter(called_tools: list, tool_arguments: dict) -> Any:
    def capture_emitter(payload: dict) -> None:
        if payload.get("type") != "function_call":
            return
        content = payload.get("content") or {}
        if content.get("state") != "start":
            return
        node = content.get("node") or ""
        if not node.startswith("tool:"):
            return
        name = node[len("tool:"):]
        called_tools.append(name)
        args_raw = content.get("arguments")
        if isinstance(args_raw, str):
            try:
                args = json.loads(args_raw)
            except (ValueError, TypeError):
                args = {}
        else:
            args = args_raw or {}
        tool_arguments[name] = args

    return capture_emitter


@dataclass
class CaseResult:
    case: EvalCase
    actual: BehaviorSnapshot
    failures: list[str]
    durationMs: float = 0.0


@dataclass
class EvalReport:
    results: list[CaseResult] = field(default_factory=list)
    failed: int = 0
    total: int = 0
    extras: dict[str, Any] = field(default_factory=dict)

    def render(self) -> str:
        lines = [f"eval {self.extras.get('mode', 'offline')}: {self.total - self.failed}/{self.total} passed"]
        for extra_key, value in self.extras.items():
            if extra_key == "mode":
                continue
            lines.append(f"  {extra_key}: {value}")
        for r in self.results:
            status = "PASS" if not r.failures else "FAIL"
            lines.append(f"  [{status}] {r.case.id} ({r.case.category})")
            for failure in r.failures:
                lines.append(f"      - {failure}")
        return "\n".join(lines)


def run_offline(cases: list[EvalCase]) -> EvalReport:
    """对每个 case 跑一次真实图(替身 LLM/call_api), 聚合确定性断言结果。"""
    results: list[CaseResult] = []
    for case in cases:
        started = time.perf_counter()
        actual = _run_case(case)
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        failures = evaluate(case, actual)
        results.append(CaseResult(case=case, actual=actual, failures=failures, durationMs=duration_ms))
    failed = sum(1 for r in results if r.failures)
    return EvalReport(results=results, failed=failed, total=len(results), extras={"mode": "offline"})


# ---------- live 模式 ----------

def resolve_eval_provider(provider_override: str | None) -> ResolvedLlmProviderConfig:
    """live 供应商解析：显式覆盖优先；否则复用生产 resolve_llm_provider(settings)。

    显式指定但对应 Key 缺失 → 立即失败，不回退。
    """
    if provider_override == "deepseek":
        if not settings.deepseek_api_key:
            raise ValueError("DeepSeek API Key 未配置，无法执行 --provider deepseek")
        return ResolvedLlmProviderConfig(
            provider="deepseek",
            api_key=SecretStr(settings.deepseek_api_key),
            model=settings.deepseek_model,
            route_model=settings.deepseek_model_route,
            base_url=settings.deepseek_base_url,
        )
    if provider_override == "dashscope":
        if not settings.dashscope_api_key:
            raise ValueError("DashScope API Key 未配置，无法执行 --provider dashscope")
        return ResolvedLlmProviderConfig(
            provider="dashscope",
            api_key=SecretStr(settings.dashscope_api_key),
            model=settings.dashscope_model,
            route_model=settings.dashscope_model_route,
        )
    return resolve_llm_provider(settings)


def run_live(cases: list[EvalCase], *, sample: int = 10, provider_override: str | None = None) -> EvalReport:
    """live 模式：真实 LLM + dry-run Business adapter（写接口零副作用）。

    必须显式 ALLOW_LIVE_AGENT_EVAL=true 且至少一个供应商 Key。
    """
    if os.environ.get("ALLOW_LIVE_AGENT_EVAL", "").strip().lower() != "true":
        raise ValueError("live eval 需要显式设置 ALLOW_LIVE_AGENT_EVAL=true")
    resolved = resolve_eval_provider(provider_override)
    selected = cases if sample is None or sample >= len(cases) else cases[:sample]

    # 真实 LLM 会调用真实工具 → 用 dry-run adapter 拦截写接口, 只读返回空数据
    results: list[CaseResult] = []
    for case in selected:
        started = time.perf_counter()
        business_calls: list[tuple[str, str]] = []
        fake_call_api = make_fake_call_api({}, business_calls.append)
        emitter_token = set_status_emitter(_make_capture_emitter([], {}))
        pending_token = set_pending_action_collector()
        try:
            with ExitStack() as stack:
                for module_path in CALL_API_MODULES:
                    stack.enter_context(mock.patch(f"{module_path}.call_api", fake_call_api))
                graph = build_graph()
                state = _build_state(case)
                try:
                    final = _run_coro(_astream_values(graph, state))
                    routing = final.get("routing") or {}
                    actual = BehaviorSnapshot(
                        routeTarget=routing.get("route_target"),
                        businessCalls=business_calls,
                        answer=final.get("result") or "",
                    )
                except Exception as exc:
                    actual = BehaviorSnapshot(errorCategory=classify_error(exc))
                failures = evaluate(case, actual)
                results.append(CaseResult(case=case, actual=actual, failures=failures,
                                          durationMs=round((time.perf_counter() - started) * 1000, 1)))
        finally:
            reset_pending_action_collector(pending_token)
            reset_status_emitter(emitter_token)

    durations = [r.durationMs for r in results] or [0.0]
    failed = sum(1 for r in results if r.failures)
    return EvalReport(
        results=results,
        failed=failed,
        total=len(results),
        extras={
            "mode": "live",
            "provider": resolved.provider,
            "model": resolved.route_model,
            "configVersion": "live-default",
            "p50Ms": round(statistics.median(durations), 1),
            # ponytail: 简单近似 p95（index = 95% 分位），仅诊断用途
            "p95Ms": round(sorted(durations)[min(len(durations) - 1, int(len(durations) * 0.95))], 1),
        },
    )


# ---------- CLI ----------

def _parse_args(argv):
    parser = argparse.ArgumentParser(prog="evals.runner", description="确定性 agent 评测执行器")
    parser.add_argument("--mode", choices=["offline", "live"], default="offline")
    parser.add_argument("--sample", type=int, default=10)
    parser.add_argument("--provider", choices=["deepseek", "dashscope"], default=None)
    parser.add_argument("--cases", nargs="*", default=None, help="case YAML 路径(默认 evals/cases/*.yaml)")
    return parser.parse_args(argv)


def resolve_case_paths(argv=None) -> list[str]:
    args = _parse_args(argv)
    if args.cases:
        return args.cases
    return DEFAULT_CASE_PATHS


def main(argv=None) -> int:
    args = _parse_args(argv)
    try:
        cases = load_cases(resolve_case_paths(argv))
    except (ValidationError, ValueError) as exc:
        print(f"dataset error: {exc}")
        return 2
    try:
        if args.mode == "live":
            report = run_live(cases, sample=args.sample, provider_override=args.provider)
        else:
            report = run_offline(cases)
    except ValueError as exc:
        print(f"live error: {exc}")
        return 1
    print(report.render())
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
