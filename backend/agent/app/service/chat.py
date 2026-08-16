import json
import logging

from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

from app.core.pending_action import PendingActionEvent
from app.core.streaming import StreamConfig, create_streaming_response
from app.schemas.auth import UserInfo

logger = logging.getLogger(__name__)


class ChatService:
    """编排 store + graph + 流式引擎,负责历史加载、落库回调、SSE 组装。"""

    def __init__(self, store, graph, settings):
        self.store = store
        self.graph = graph
        self.settings = settings

    async def stream_chat(self, session_id: str, content: str, user_id: int, role: str, token: str = "") -> StreamingResponse:
        await self.store.save_message(session_id, "user", content)
        history = await self.store.get_messages(session_id)

        if len(history) == 1:
            try:
                await self.store.update_session_title(session_id, content[:20])
            except Exception:
                pass

        history_messages = []
        for m in history:
            if m.role == "user":
                history_messages.append(HumanMessage(content=m.content))
            else:
                history_messages.append(AIMessage(content=m.content))

        user = UserInfo(user_id=user_id, username="", role=role, token=token)

        pending_action = await self.store.get_pending_action(session_id, user_id)

        def build_initial_state() -> dict:
            state = {
                "user": user,
                "history_messages": history_messages,
                "current_question": content,
                "routing": None,
                "result": "",
                "session_id": session_id,
                "pending_action": pending_action,
                "pending_preview_id": getattr(pending_action, "preview_id", None),
            }
            return state

        async def on_answer_completed(answer_text: str, used_tools: list[str]) -> None:
            await self.store.save_message(
                session_id,
                "assistant",
                answer_text,
                json.dumps(used_tools) if used_tools else None,
            )

        async def on_pending_action(event: PendingActionEvent) -> None:
            if event.operation == "CLEAR":
                await self.store.delete_pending_action(session_id, user_id)
            elif event.action is not None:
                await self.store.save_pending_action(session_id, event.action, ttl_seconds=600)

        config = StreamConfig(
            workflow=self.graph,
            build_initial_state=build_initial_state,
            extract_final_content=lambda s: str(s.get("result") or ""),
            map_exception=lambda exc: "处理请求时出错，请重试",
            on_answer_completed=on_answer_completed,
            on_pending_action=on_pending_action,
        )
        return create_streaming_response(config)
