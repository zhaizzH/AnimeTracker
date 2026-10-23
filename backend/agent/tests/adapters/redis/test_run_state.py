"""run 状态的持久化端口与 Redis 适配器契约。

run 的执行不跨进程重启（design §6），但状态要落 Redis，让重启后的进程
能把「上次状态为 running、内存里却没有」的 run 收敛为 failed（D9）。
"""

from __future__ import annotations

import fakeredis
import pytest

from app.adapters.redis.run_state import RUN_STATE_TTL_SECONDS, RedisRunStateStore
from app.chat.run_state import RunState


@pytest.fixture
def store():
    return RedisRunStateStore(fakeredis.FakeAsyncRedis(decode_responses=True))


@pytest.mark.asyncio
async def test_save_and_get_roundtrip(store) -> None:
    await store.save_run_state(
        RunState(run_id="r1", session_id="s1", user_id=7, status="running", event_count=3)
    )
    got = await store.get_run_state("r1")
    assert got == RunState(
        run_id="r1", session_id="s1", user_id=7, status="running", event_count=3
    )


@pytest.mark.asyncio
async def test_get_unknown_run_returns_none(store) -> None:
    assert await store.get_run_state("nope") is None


@pytest.mark.asyncio
async def test_state_carries_ttl(store) -> None:
    await store.save_run_state(
        RunState(run_id="r1", session_id="s1", user_id=7, status="running")
    )
    ttl = await store._r.ttl("agent:run:r1")
    assert 0 < ttl <= RUN_STATE_TTL_SECONDS


@pytest.mark.asyncio
async def test_session_pointer_roundtrip_and_ttl(store) -> None:
    await store.save_session_run("s1", "r1")
    assert await store.get_session_run("s1") == "r1"
    assert 0 < await store._r.ttl("agent:session_runs:s1") <= RUN_STATE_TTL_SECONDS


@pytest.mark.asyncio
async def test_session_pointer_unknown_returns_none(store) -> None:
    assert await store.get_session_run("nope") is None
