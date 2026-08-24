import json
import logging

import redis

from app.adapters.prompts.file_prompt import load_prompt

logger = logging.getLogger(__name__)

MANAGED_PROMPT_KEYS = (
    "client_gateway_prompt",
    "client_search_agent_prompt",
    "client_discover_agent_prompt",
    "client_recommend_agent_prompt",
    "admin_agent_prompt",
)
PROMPT_REDIS_KEY_TEMPLATE = "agent:prompt:{}"

LOCAL_PROMPT_PATHS = {
    "client_gateway_prompt": "client/gateway_prompt.md",
    "client_search_agent_prompt": "client/search_agent_prompt.md",
    "client_discover_agent_prompt": "client/discover_agent_prompt.md",
    "client_recommend_agent_prompt": "client/recommend_agent_prompt.md",
    "admin_agent_prompt": "admin/admin_agent_prompt.md",
}


class RedisPromptRepository:
    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._snapshot: dict[str, str] = {}

    def initialize_snapshot(self) -> None:
        """从 Redis 批量加载托管提示词;任一失败仅告警,不中断启动。"""
        try:
            r = self._redis()
        except Exception as exc:
            logger.warning("Redis 不可用,托管提示词回退本地: %s", repr(exc))
            return
        for key in MANAGED_PROMPT_KEYS:
            try:
                raw = r.get(PROMPT_REDIS_KEY_TEMPLATE.format(key))
                content = (json.loads(raw) or {}).get("promptContent") if raw else None
                if content:
                    self._snapshot[key] = content
            except Exception as exc:
                logger.warning("Redis 提示词加载失败: key=%s error=%s", key, repr(exc))

    def list_keys(self) -> tuple[str, ...]:
        return MANAGED_PROMPT_KEYS

    def get(self, key: str, fallback_path: str | None = None) -> str:
        if key in MANAGED_PROMPT_KEYS:
            content = self._snapshot.get(key)
            if content:
                return content
        local_path = fallback_path or LOCAL_PROMPT_PATHS.get(key)
        if local_path:
            return load_prompt(local_path)
        return ""

    def set(self, key: str, content: str) -> None:
        self._redis().set(
            PROMPT_REDIS_KEY_TEMPLATE.format(key),
            json.dumps({"promptKey": key, "promptContent": content}),
        )
        self.refresh_snapshot(key)

    def reset(self, key: str) -> str:
        self._redis().delete(PROMPT_REDIS_KEY_TEMPLATE.format(key))
        self.refresh_snapshot(key)
        return self.get(key)

    def refresh_snapshot(self, key: str) -> None:
        """刷新单条托管提示词;key 不存在或非法则从快照移除。"""
        if key not in MANAGED_PROMPT_KEYS:
            return
        try:
            raw = self._redis().get(PROMPT_REDIS_KEY_TEMPLATE.format(key))
            content = (json.loads(raw) or {}).get("promptContent") if raw else None
        except Exception as exc:
            logger.warning("Redis 提示词刷新失败: key=%s error=%s", key, repr(exc))
            return
        if content:
            self._snapshot[key] = content
        else:
            self._snapshot.pop(key, None)

    def _redis(self) -> redis.Redis:
        return redis.Redis.from_url(self._redis_url, decode_responses=True)
