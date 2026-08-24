import json
import logging
import threading
from datetime import datetime, timedelta

import redis
from pydantic import ValidationError

from app.chat.models import Message, Session
from app.chat.ports import ChatStore
from app.chat.pending_action import PendingAction, parse_pending_action_json
from app.shared.observability import hash_value

logger = logging.getLogger(__name__)

# ponytail: datetime.now() has microsecond resolution; back-to-back writes can share
# a timestamp and break "most recent first" session ordering. Guard makes updated_at
# strictly increasing within this process (not part of the plan's original code).
_now_lock = threading.Lock()
_last_now: str | None = None


def _now_iso() -> str:
    global _last_now
    with _now_lock:
        now = datetime.now().isoformat()
        if _last_now is not None and now <= _last_now:
            now = (datetime.fromisoformat(_last_now) + timedelta(microseconds=1)).isoformat()
        _last_now = now
        return now


class RedisChatStore(ChatStore):
    def __init__(self, redis_url: str):
        self._r: redis.asyncio.Redis = redis.asyncio.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)

    def _session_key(self, session_id: str) -> str:
        return f"agent:session:{session_id}"

    def _messages_key(self, session_id: str) -> str:
        return f"agent:messages:{session_id}"

    def _user_sessions_key(self, user_id: int) -> str:
        return f"agent:user_sessions:{user_id}"

    def _pending_action_key(self, session_id: str) -> str:
        return f"agent:pending-action:{session_id}"

    async def init_db(self):
        await self._r.ping()

    async def create_session(self, user_id: int, session_id: str, title: str = "新对话"):
        now = _now_iso()
        await self._r.hset(
            self._session_key(session_id),
            mapping={
                "user_id": user_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "message_count": 0,
            },
        )
        await self._r.sadd(self._user_sessions_key(user_id), session_id)

    async def get_user_sessions(self, user_id: int) -> list[Session]:
        session_ids = await self._r.smembers(self._user_sessions_key(user_id))
        sessions = []
        for session_id in session_ids:
            data = await self._r.hgetall(self._session_key(session_id))
            if not data:
                continue
            sessions.append(Session(
                session_id=session_id,
                user_id=int(data["user_id"]),
                title=data["title"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                message_count=int(data.get("message_count") or 0),
            ))
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    async def get_messages(self, session_id: str) -> list[Message]:
        rows = await self._r.lrange(self._messages_key(session_id), 0, -1)
        messages = []
        for row in rows:
            data = json.loads(row)
            messages.append(Message(session_id=session_id, **data))
        return messages

    async def save_message(self, session_id: str, role: str, content: str, tool_calls: str | None = None):
        message = {
            "role": role,
            "content": content,
            "tool_calls": tool_calls,
            "created_at": datetime.now().isoformat(),
        }
        await self._r.rpush(self._messages_key(session_id), json.dumps(message, ensure_ascii=False))
        now = _now_iso()
        async with self._r.pipeline() as pipe:
            pipe.hset(self._session_key(session_id), "updated_at", now)
            if role == "user":
                pipe.hincrby(self._session_key(session_id), "message_count", 1)
            await pipe.execute()

    async def delete_session(self, session_id: str, user_id: int):
        await self._r.delete(self._messages_key(session_id))
        await self._r.delete(self._pending_action_key(session_id))
        await self._r.srem(self._user_sessions_key(user_id), session_id)
        await self._r.delete(self._session_key(session_id))

    async def _parse_pending_action(self, session_id: str, raw: str | None) -> PendingAction | None:
        """解析待确认动作；未知类型/损坏数据按设计规范记录错误并清除，返回 None，不向上抛。"""
        if not raw:
            return None
        try:
            return parse_pending_action_json(raw)
        except (ValidationError, json.JSONDecodeError):
            logger.warning(
                "待确认动作数据损坏或类型未知，已清除: sessionHash=%s rawLength=%d",
                hash_value(session_id),
                len(raw),
            )
            await self._r.delete(self._pending_action_key(session_id))
            return None

    async def get_pending_action(self, session_id: str, user_id: int) -> PendingAction | None:
        raw = await self._r.get(self._pending_action_key(session_id))
        action = await self._parse_pending_action(session_id, raw)
        if action is None or action.user_id != user_id:
            return None
        return action

    async def save_pending_action(self, session_id: str, action: PendingAction, ttl_seconds: int = 600):
        await self._r.set(
            self._pending_action_key(session_id),
            action.model_dump_json(by_alias=True),
            ex=ttl_seconds,
        )

    async def delete_pending_action(self, session_id: str, user_id: int):
        raw = await self._r.get(self._pending_action_key(session_id))
        action = await self._parse_pending_action(session_id, raw)
        if action is not None and action.user_id == user_id:
            await self._r.delete(self._pending_action_key(session_id))

    async def update_session_title(self, session_id: str, title: str):
        await self._r.hset(self._session_key(session_id), "title", title)
