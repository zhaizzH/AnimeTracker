"""离线评测替身：fake chat model + fake call_api。

fake chat model 基于 FakeMessagesListChatModel（按列表顺序返回预置消息，
无视 bind_tools）；补丁 bind_tools 使 create_agent 可接受。
fake call_api 按 (method, path) 返回 case fixtures 合并默认值，并记录每次调用
供 businessCalls 断言。零网络、零副作用。
"""

import json
from typing import Any, Callable

from langchain_core.messages import AIMessage
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

from evals.schema import EvalExpectation

# 持有 call_api 引用的全部模块：patch 这些引用点才生效（patch app.config 无效）
CALL_API_MODULES = (
    "app.agent.http",
    "app.agent.client.search",
    "app.agent.client.discover",
    "app.agent.client.collections",
    "app.agent.client.actions.wishlist",
    "app.agent.client.actions.collection_progress",
)

# 写操作替身响应: 关键路径返回确定结果, 保证执行工具走完真实分支且零副作用
_DEFAULT_EXECUTE_STATE = {"state": "COMPLETED"}
_DEFAULT_PROGRESS_PREVIEW = {
    "previewId": "p1",
    "expiresAt": "2026-08-16T10:00:00+08:00",
    "items": [{"subjectId": 101, "subjectName": "测试番", "currentEpStatus": 5, "targetEpStatus": 6}],
}
_DEFAULT_WISHLIST_ADDED = {"state": "ADDED"}


class EvalFakeChatModel(FakeMessagesListChatModel):
    """create_agent 会对模型调用 bind_tools；fake 按序返回预置消息即可。"""

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        return self


def build_route_responses(expect: EvalExpectation) -> list[AIMessage]:
    """gateway 节点（CLIENT_ROUTE slot）返回确定性路由 JSON。"""
    target = expect.routeTarget or "search_agent"
    return [AIMessage(content=json.dumps({"route_target": target}))]


def build_domain_responses(expect: EvalExpectation) -> list[AIMessage]:
    """domain 节点：按 expect.calledTools 发工具调用消息，再发无害答案。

    禁止工具（forbiddenTools）永远不发出——由断言验证其未出现在 calledTools。
    """
    responses: list[AIMessage] = []
    if expect.calledTools:
        tool_calls = []
        for i, name in enumerate(expect.calledTools, start=1):
            args = (expect.toolArguments or {}).get(name, {})
            tool_calls.append({"name": name, "args": args, "id": f"call_{i}", "type": "tool_call"})
        responses.append(AIMessage(content="", tool_calls=tool_calls))
    responses.append(AIMessage(content="处理完成"))
    return responses


def _default_response(method: str, path: str) -> Any:
    if path == "/api/client/collections/counts":
        return {}
    if path == "/api/client/collections":
        return {"content": []}
    if method == "GET" and path.startswith("/api/client/collections/"):
        # 单部收藏状态默认视为未收藏(404)
        return {"error": True, "code": 404}
    if path == "/api/client/collections/progress-preview":
        return _DEFAULT_PROGRESS_PREVIEW
    if method == "POST" and "/progress-preview/" in path and path.endswith("/execute"):
        return _DEFAULT_EXECUTE_STATE
    if method == "POST" and path.endswith("/wishlist"):
        return _DEFAULT_WISHLIST_ADDED
    if path == "/api/client/subjects/search":
        return {"content": []}
    if path == "/api/client/tags":
        return []
    if method == "GET" and path.startswith("/api/client/tags/"):
        return {"content": []}
    if method == "GET" and path.startswith("/api/client/subjects/"):
        return {"content": []}
    if method == "GET":
        return {"content": []}
    return {}


def make_fake_call_api(case_fixtures: dict, record: Callable[[tuple[str, str]], None]) -> Callable:
    """构造记录每次调用并返回 fixture 响应的 fake call_api。

    case fixtures 优先：键为 "METHOD path" 或裸 path；未命中走默认值。
    """

    def _lookup(method: str, path: str) -> Any:
        key = f"{method} {path}"
        if key in case_fixtures:
            return case_fixtures[key]
        if path in case_fixtures:
            return case_fixtures[path]
        return _default_response(method, path)

    def fake_call_api(method: str, path: str, params: dict | None = None, token: str | None = None) -> Any:
        record((method, path))
        return _lookup(method, path)

    return fake_call_api
