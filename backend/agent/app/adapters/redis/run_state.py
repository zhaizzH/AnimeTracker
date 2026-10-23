"""Redis run 状态投影（design §2.2）。

两个键，都带 TTL 900s：

- ``agent:run:{run_id}`` hash：session_id / user_id / status / event_count
- ``agent:session_runs:{session_id}`` string：该会话最近的 run_id

投影**可以丢**：丢了最多让重连端拿不到 run 状态，落到「从历史读」的降级路径；
写失败也只记日志，绝不影响 run 本身。
"""

from __future__ import annotations

import logging
from typing import Any

from app.chat.run_state import RUN_STATE_TTL_SECONDS, RunState

logger = logging.getLogger(__name__)

class RedisRunStateStore:
    def __init__(self, redis_client: Any, ttl_seconds: int = RUN_STATE_TTL_SECONDS) -> None:
        self._r = redis_client
        self._ttl = ttl_seconds

    async def save_run_state(self, state: RunState) -> None:
        key = f"agent:run:{state.run_id}"
        try:
            pipe = self._r.pipeline()
            pipe.hset(
                key,
                mapping={
                    "session_id": state.session_id,
                    "user_id": state.user_id,
                    "status": state.status,
                    "event_count": state.event_count,
                },
            )
            pipe.expire(key, self._ttl)
            await pipe.execute()
        except Exception:
            # 投影失败不阻塞主流程（design §8）
            logger.warning("run 状态写入失败 run_id=%s", state.run_id, exc_info=True)

    async def get_run_state(self, run_id: str) -> RunState | None:
        try:
            data = await self._r.hgetall(f"agent:run:{run_id}")
        except Exception:
            logger.warning("run 状态读取失败 run_id=%s", run_id, exc_info=True)
            return None
        if not data:
            return None
        return RunState(
            run_id=run_id,
            session_id=data.get("session_id", ""),
            user_id=int(data.get("user_id") or 0),
            status=data.get("status", ""),
            event_count=int(data.get("event_count") or 0),
        )

    async def save_session_run(self, session_id: str, run_id: str) -> None:
        key = f"agent:session_runs:{session_id}"
        try:
            await self._r.set(key, run_id, ex=self._ttl)
        except Exception:
            logger.warning("会话 run 指针写入失败 session=%s", session_id, exc_info=True)

    async def get_session_run(self, session_id: str) -> str | None:
        try:
            value = await self._r.get(f"agent:session_runs:{session_id}")
        except Exception:
            logger.warning("会话 run 指针读取失败 session=%s", session_id, exc_info=True)
            return None
        if isinstance(value, bytes):
            value = value.decode()
        return value or None
