import json
import logging

import redis

from app.utils.prompt_utils import load_prompt

logger = logging.getLogger(__name__)

MANAGED_PROMPT_KEYS = (
    "client_gateway_prompt",
    "client_search_agent_prompt",
    "client_discover_agent_prompt",
    "client_recommend_agent_prompt",
    "admin_agent_prompt",
)
PROMPT_REDIS_KEY_TEMPLATE = "agent:prompt:{}"

# 进程内托管提示词快照: managed_key -> content
_PROMPT_SNAPSHOT: dict[str, str] = {}


def _get_redis() -> redis.Redis:
    from app.config import settings
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def initialize_agent_prompt_snapshot() -> None:
    """从 Redis 批量加载托管提示词;任一失败仅告警,不中断启动。"""
    global _PROMPT_SNAPSHOT
    try:
        r = _get_redis()
    except Exception as exc:
        logger.warning("Redis 不可用,托管提示词回退本地: %s", repr(exc))
        return
    for key in MANAGED_PROMPT_KEYS:
        try:
            raw = r.get(PROMPT_REDIS_KEY_TEMPLATE.format(key))
            if not raw:
                continue
            content = (json.loads(raw) or {}).get("promptContent")
            if content:
                _PROMPT_SNAPSHOT[key] = content
        except Exception as exc:
            logger.warning("Redis 提示词加载失败: key=%s error=%s", key, repr(exc))


def refresh_agent_prompt_snapshot(prompt_key: str) -> None:
    """刷新单条托管提示词;key 不存在或非法则从快照移除。"""
    global _PROMPT_SNAPSHOT
    if prompt_key not in MANAGED_PROMPT_KEYS:
        return
    try:
        r = _get_redis()
        raw = r.get(PROMPT_REDIS_KEY_TEMPLATE.format(prompt_key))
        content = (json.loads(raw) or {}).get("promptContent") if raw else None
    except Exception as exc:
        logger.warning("Redis 提示词刷新失败: key=%s error=%s", prompt_key, repr(exc))
        return
    if content:
        _PROMPT_SNAPSHOT[prompt_key] = content
    else:
        _PROMPT_SNAPSHOT.pop(prompt_key, None)


def load_managed_prompt(prompt_key: str, local_prompt_path: str | None = None) -> str:
    """托管键优先读 Redis 快照;未命中/非托管键回退本地 md。"""
    if prompt_key in MANAGED_PROMPT_KEYS:
        content = _PROMPT_SNAPSHOT.get(prompt_key)
        if content:
            return content
    if local_prompt_path:
        return load_prompt(local_prompt_path)
    return ""
