import json
from typing import Any, Awaitable, Callable

from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest

from app.core.agent.agent_event_bus import emit_function_call

_REGISTERED: dict[str, str] = {}  # tool_name -> display_name


def get_tool_name(tool_obj: Any) -> str:
    name = getattr(tool_obj, "name", None)
    if isinstance(name, str) and name.strip():
        return name.strip()
    callable_name = getattr(tool_obj, "__name__", None)
    if isinstance(callable_name, str) and callable_name.strip():
        return callable_name.strip()
    return "UNKNOWN_TOOL_NAME"


def tool_call_status(*, display_name: str | None = None) -> Callable:
    def _decorate(tool_obj):
        resolved_name = get_tool_name(tool_obj)
        _REGISTERED[resolved_name] = display_name or resolved_name
        return tool_obj

    return _decorate


def _format_arguments(tool_args: Any) -> str:
    if isinstance(tool_args, (dict, list)):
        return json.dumps(tool_args, ensure_ascii=False, default=str)
    return str(tool_args)


def build_tool_status_middleware():
    """对被 @tool_call_status 标注的工具发送 function_call start/end/error 事件。"""

    @wrap_tool_call
    async def _tool_status_middleware(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | None]],
    ) -> ToolMessage | None:
        tool_call = request.tool_call if isinstance(request.tool_call, dict) else {}
        tool_name = str(tool_call.get("name") or "").strip()
        tool_call_id = str(tool_call.get("id") or "tool_call").strip() or "tool_call"
        if not tool_name or tool_name not in _REGISTERED:
            return await handler(request)

        display_name = _REGISTERED[tool_name]
        emit_function_call(
            node=f"tool:{tool_name}",
            state="start",
            message=f"正在调用 {display_name}",
            name=display_name,
            arguments=_format_arguments(tool_call.get("args")),
        )
        try:
            result = await handler(request)
        except Exception as exc:
            emit_function_call(
                node=f"tool:{tool_name}",
                state="end",
                result="error",
                message=f"{display_name} 调用失败",
                name=display_name,
            )
            return ToolMessage(content=json.dumps({"error": str(exc)}, ensure_ascii=False), tool_call_id=tool_call_id)
        emit_function_call(
            node=f"tool:{tool_name}",
            state="end",
            result="success",
            message=f"{display_name} 调用成功",
            name=display_name,
        )
        return result

    return _tool_status_middleware
