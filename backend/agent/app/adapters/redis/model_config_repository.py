import json
import time

import redis

MODEL_CONFIG_KEY = "agent:config:model"
_REFRESH_SECONDS = 5.0


class RedisModelConfigRepository:
    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._cache: dict = {"ts": 0.0, "data": None}

    def get(self) -> dict | None:
        """读取运行时模型配置(Redis); 短 TTL 缓存, 未设置/不可用返回 None。"""
        now = time.monotonic()
        if now - self._cache["ts"] < _REFRESH_SECONDS:
            return self._cache["data"]
        try:
            raw = self._redis().get(MODEL_CONFIG_KEY)
            data = json.loads(raw) if raw else None
        except Exception:
            data = None
        self._cache.update(ts=now, data=data)
        return data

    def set(self, config: dict) -> None:
        self._redis().set(MODEL_CONFIG_KEY, json.dumps(config))
        self._cache.update(ts=0.0, data=config)

    def _redis(self) -> redis.Redis:
        return redis.Redis.from_url(self._redis_url, decode_responses=True)
