import asyncio
import json
import logging

from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务：编排认证、历史加载、Graph 执行、SSE 推送、持久化"""

    def __init__(self, store, router_graph, settings):
        self.store = store
        self.router_graph = router_graph
        self.settings = settings

    async def stream_chat(
        self,
        session_id: str,
        content: str,
        user_id: int,
        role: str,
    ):
        """处理聊天请求，返回 SSE StreamingResponse"""
        # 保存用户消息
        self.store.save_message(session_id, "user", content)

        # 加载历史
        history = self.store.get_messages(session_id)

        # 首条消息自动设标题
        if len(history) == 1:
            title = content[:20]
            try:
                self.store.update_session_title(session_id, title)
            except Exception:
                pass

        # 转为 LangChain 消息格式
        messages = []
        for m in history:
            if m.role == "user":
                messages.append(HumanMessage(content=m.content))
            else:
                messages.append(AIMessage(content=m.content))

        from app.schemas.auth import UserInfo
        user = UserInfo(user_id=user_id, username="", role=role)

        initial_state = {
            "messages": messages,
            "user": user,
            "next_agent": None,
            "final_output": "",
            "used_tools": [],
        }

        async def event_stream():
            full_content = ""
            used_tools = []

            try:
                async for event in self.router_graph.astream_events(
                    initial_state, version="v2"
                ):
                    kind = event["event"]

                    if kind == "on_chat_model_stream":
                        # 跳过 Router 节点的意图分类输出，只保留 sub-agent 的回复
                        if event.get("metadata", {}).get("langgraph_node", "") == "user_router":
                            continue
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            full_content += chunk.content
                            yield f"event: token\ndata: {json.dumps({'content': chunk.content})}\n\n"

                    elif kind == "on_tool_start":
                        tool_name = event.get("name", "")
                        if tool_name and tool_name not in used_tools:
                            used_tools.append(tool_name)

                # 保存助手回复
                self.store.save_message(
                    session_id, "assistant", full_content,
                    json.dumps(used_tools) if used_tools else None,
                )

                # metadata + done
                yield f"event: metadata\ndata: {json.dumps({'session_id': session_id, 'used_tools': used_tools})}\n\n"
                yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"

            except asyncio.CancelledError:
                logger.info("Client disconnected for session %s, graph cancelled", session_id)
                raise
            except Exception as e:
                logger.exception("Chat error for session %s", session_id)
                yield f"event: error\ndata: {json.dumps({'message': '处理请求时出错，请重试'})}\n\n"
            finally:
                logger.debug("Event stream ended for session %s", session_id)

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
