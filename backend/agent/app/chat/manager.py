import json
import asyncio
import logging

import httpx
from fastapi import WebSocket

from app.config import settings
from app.chat.protocol import (
    ClientMessage, ServerToken, ServerDone, ServerError,
    ServerSessionList, ServerHistory, ServerPing,
)
from app.db import models as db

logger = logging.getLogger(__name__)


async def verify_token(token: str) -> int | None:
    """Call Spring Boot /api/user/me to validate JWT, return userId or None."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{settings.backend_base_url}/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json()["data"]["id"]
    except Exception as e:
        logger.warning("Token verify failed: %s", e)
    return None


class ConnectionManager:
    """Manages WebSocket connections, authentication, heartbeat, and message dispatch."""

    def __init__(self, agent_executor):
        self.agent_executor = agent_executor
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}

    async def handle(self, ws: WebSocket):
        token = ws.query_params.get("token", "")
        user_id = await verify_token(token)
        if user_id is None:
            await ws.send_json(ServerError(message="认证失败，请重新登录").to_dict())
            await ws.close(code=4001)
            return

        await ws.accept()
        user_key = f"user_{user_id}"
        logger.info("User %s connected", user_id)

        heartbeat_task = asyncio.create_task(self._heartbeat(ws))
        self._heartbeat_tasks[user_key] = heartbeat_task

        try:
            await self._message_loop(ws, user_id)
        except Exception:
            logger.exception("Connection error for user %s", user_id)
        finally:
            heartbeat_task.cancel()
            self._heartbeat_tasks.pop(user_key, None)
            logger.info("User %s disconnected", user_id)

    async def _heartbeat(self, ws: WebSocket):
        interval = settings.ws_heartbeat_interval
        try:
            while True:
                await asyncio.sleep(interval)
                await ws.send_json(ServerPing().to_dict())
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def _message_loop(self, ws: WebSocket, user_id: int):
        while True:
            raw = await ws.receive_json()
            msg = ClientMessage(**raw)

            if msg.type == "pong":
                continue

            if msg.type == "list_sessions":
                sessions = db.get_user_sessions(user_id)
                await ws.send_json(ServerSessionList(sessions=sessions).to_dict())
                continue

            if msg.type == "new_session":
                import uuid
                session_id = str(uuid.uuid4())
                db.create_session(user_id, session_id, "新对话")
                await ws.send_json(ServerDone(session_id=session_id, full_content="").to_dict())
                continue

            if msg.type == "load_history" and msg.session_id:
                messages = db.get_session_messages(msg.session_id)
                await ws.send_json(ServerHistory(session_id=msg.session_id, messages=messages).to_dict())
                continue

            if msg.type == "delete_session" and msg.session_id:
                db.delete_session(msg.session_id, user_id)
                await ws.send_json(ServerDone(session_id=msg.session_id, full_content="").to_dict())
                continue

            if msg.type == "message" and msg.session_id and msg.content:
                await self._handle_message(ws, user_id, msg.session_id, msg.content)

    async def _handle_message(self, ws: WebSocket, user_id: int, session_id: str, content: str):
        # Save user message first so it's persisted even if streaming fails
        db.save_message(session_id, "user", content)

        # Auto-title for new sessions
        messages = db.get_session_messages(session_id)
        if len(messages) == 1:
            title = content[:20]
            db.update_session_title(session_id, title)

        db.update_session_time(session_id)

        # Build message list for langgraph (agent expects {"messages": [...]})
        agent_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

        used_tools: list[str] = []
        full_content = ""

        try:
            async for event in self.agent_executor.astream_events(
                {"messages": agent_messages},
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        full_content += chunk.content
                        await ws.send_json(ServerToken(
                            session_id=session_id, content=chunk.content,
                        ).to_dict())

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    if tool_name and tool_name not in used_tools:
                        used_tools.append(tool_name)

        except Exception:
            logger.exception("Agent error for session %s", session_id)
            await ws.send_json(ServerError(
                session_id=session_id, message="处理请求时出错，请重试",
            ).to_dict())
            return

        # Save assistant response
        db.save_message(
            session_id, "assistant", full_content,
            json.dumps(used_tools) if used_tools else None,
        )

        await ws.send_json(ServerDone(
            session_id=session_id, full_content=full_content, tool_calls=used_tools,
        ).to_dict())
