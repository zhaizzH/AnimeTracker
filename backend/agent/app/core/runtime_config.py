import json
import time

import redis

MODEL_CONFIG_KEY = "agent:config:model"
_REFRESH_SECONDS = 5.0
_cache: dict = {"ts": 0.0, "data": None}


def _redis() -> redis.Redis:
    from app.config import settings

    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_runtime_model_config() -> dict | None:
    """读取运行时模型配置(Redis); 短 TTL 缓存, 未设置/不可用返回 None。"""
    now = time.monotonic()
    if now - _cache["ts"] < _REFRESH_SECONDS:
        return _cache["data"]
    try:
        raw = _redis().get(MODEL_CONFIG_KEY)
        data = json.loads(raw) if raw else None
    except Exception:
        data = None
    _cache.update(ts=now, data=data)
    return data


def set_runtime_model_config(config: dict) -> None:
    _redis().set(MODEL_CONFIG_KEY, json.dumps(config))
    _cache.update(ts=0.0, data=config)
