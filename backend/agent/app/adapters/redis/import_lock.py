"""Redis 单飞导入锁：SET NX EX 获取，compare-and-del 释放，防误删他人锁。

ponytail: 释放/续期用 WATCH+MULTI 而非 Lua——语义与 compare-and-del 等价，
且不需要额外 lupa 依赖（fakeredis 无 Lua 时也能测）。若将来 Redis 端脚本化，
可换回 EVAL；升级路径只在 release/renew 两处。
"""

from __future__ import annotations

from typing import Any

IMPORT_LOCK_KEY = "animetracker:import:lock"
IMPORT_LOCK_TTL_SECONDS = 3600

def _matches(value: Any, token: str) -> bool:
    """兼容 decode_responses 关闭时返回 bytes 的 GET 结果。"""
    if isinstance(value, bytes):
        try:
            value = value.decode()
        except UnicodeDecodeError:
            return False
    return value == token

def acquire(redis_client: Any, token: str) -> bool:
    """取得导入锁；锁已被占用时返回 False。"""
    return bool(redis_client.set(IMPORT_LOCK_KEY, token, nx=True, ex=IMPORT_LOCK_TTL_SECONDS))

def release(redis_client: Any, token: str) -> bool:
    """释放锁；token 不匹配（锁已过期或已被他人持有）时不删除。"""
    pipe = redis_client.pipeline()
    try:
        pipe.watch(IMPORT_LOCK_KEY)
        if not _matches(pipe.get(IMPORT_LOCK_KEY), token):
            return False
        pipe.multi()
        pipe.delete(IMPORT_LOCK_KEY)
        result = pipe.execute()
    except Exception:
        return False
    finally:
        pipe.reset()
    return bool(result)

def renew(redis_client: Any, token: str, ttl_seconds: int = IMPORT_LOCK_TTL_SECONDS) -> bool:
    """续期锁；token 不匹配时返回 False，由调用方决定是否停止续期。"""
    pipe = redis_client.pipeline()
    try:
        pipe.watch(IMPORT_LOCK_KEY)
        if not _matches(pipe.get(IMPORT_LOCK_KEY), token):
            return False
        pipe.multi()
        pipe.pexpire(IMPORT_LOCK_KEY, int(ttl_seconds * 1000))
        result = pipe.execute()
    except Exception:
        return False
    finally:
        pipe.reset()
    return bool(result)
