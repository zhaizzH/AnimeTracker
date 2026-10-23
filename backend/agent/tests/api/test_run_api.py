"""run 化 API 契约：run_id 注入、409 冲突、归属校验、重连订阅。

对应任务 ``10-22-fix-agent-stream-disconnect`` 步骤 2 与决策 D2/D8/Q10/Q13。
测试边界是 HTTP 接口本身（``create_chat_router``），用替身填充 service/store。

全部在**同一个事件循环**里跑：ChatRunManager 的 run task 绑定创建它的事件循环，
用 ``TestClient``（会另起 loop）会让 task 悬空。
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from fastapi import FastAPI

from app.api.chat import create_chat_router
from app.chat.events import AgentEvent, AgentEventType
from app.chat.runs import ChatRunManager, RunStatus
from app.chat.user import UserInfo

USER = UserInfo(user_id=7, username="u", role="USER", token="t")


class _Session:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.title = "t"
        self.message_count = 0
        self.created_at = None


class FakeStore:
    def __init__(self) -> None:
        self.sessions = [_Session("s1")]

    async def get_user_sessions(self, _user_id: int):
        return self.sessions

    async def get_messages(self, _session_id: str):
        return []


class FakeService:
    def __init__(self, manager: ChatRunManager) -> None:
        self.runs = manager
        self.started: list[str] = []

    async def start_run(self, *, session_id, content, user_id, role, token=""):
        self.started.append(content)

        async def events():
            yield AgentEvent(type=AgentEventType.ANSWER, text="hi")
            yield AgentEvent(type=AgentEventType.END)

        return await self.runs.start(session_id=session_id, user_id=user_id, events=events())


def _auth() -> UserInfo:
    return USER


@pytest.fixture
async def ctx():
    manager = ChatRunManager(store=None)
    service = FakeService(manager)
    app = FastAPI()
    app.state.store = FakeStore()
    app.state.chat_service = service
    app.state.chat_runs = manager
    app.include_router(
        create_chat_router(prefix="/api/client/agent", auth_dep=_auth)
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        yield client, service, manager
    await manager.shutdown()


def _frames(text: str) -> list[dict]:
    return [
        json.loads(line[len("data: "):])
        for line in text.splitlines()
        if line.startswith("data: ")
    ]


async def _stuck_run(manager: ChatRunManager, *, user_id: int = USER.user_id):
    async def stuck():
        yield AgentEvent(type=AgentEventType.ANSWER, text="x")
        await asyncio.Event().wait()

    return await manager.start(session_id="s1", user_id=user_id, events=stuck())


@pytest.mark.asyncio
async def test_post_stream_injects_run_id_in_first_frame(ctx) -> None:
    """Q10：第一帧 meta 带 run_id，客户端据此重连。"""
    client, _, manager = ctx
    resp = await client.post(
        "/api/client/agent/stream", json={"session_id": "s1", "content": "hi"}
    )
    assert resp.status_code == 200
    frames = _frames(resp.text)
    run_id = frames[0]["meta"]["run_id"]
    assert manager.get(run_id) is not None
    assert sum(1 for f in frames if f["is_end"]) == 1
    assert frames[-1]["is_end"] is True


@pytest.mark.asyncio
async def test_post_stream_conflicts_when_session_has_active_run(ctx) -> None:
    """D2：同会话已有 RUNNING run → 409，并给出 active_run_id 与 capabilities。"""
    client, _, manager = ctx
    run = await _stuck_run(manager)
    resp = await client.post(
        "/api/client/agent/stream", json={"session_id": "s1", "content": "again"}
    )
    assert resp.status_code == 409
    body = resp.json()
    assert body["detail"]["active_run_id"] == run.run_id
    assert body["detail"]["capabilities"] == ["interrupt"]


@pytest.mark.asyncio
async def test_cancelled_run_does_not_block_new_stream(ctx) -> None:
    """D8：cancelled 不算 active，新请求直接放行。"""
    client, _, manager = ctx
    run = await _stuck_run(manager)
    await manager.stop(run.run_id)
    resp = await client.post(
        "/api/client/agent/stream", json={"session_id": "s1", "content": "again"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_session_run_endpoint_reports_status(ctx) -> None:
    """Q13：GET /sessions/{id}/run 返回 run_id + status，且校验会话归属。"""
    client, _, manager = ctx
    run = await _stuck_run(manager)
    resp = await client.get("/api/client/agent/sessions/s1/run")
    assert resp.status_code == 200
    assert resp.json() == {"run_id": run.run_id, "status": RunStatus.RUNNING.value}

    other = await client.get("/api/client/agent/sessions/nope/run")
    assert other.status_code == 404


@pytest.mark.asyncio
async def test_run_stream_rejects_foreign_run(ctx) -> None:
    """归属校验：他人 run 一律 404，不暴露存在性。"""
    client, _, manager = ctx
    run = await _stuck_run(manager, user_id=999)
    resp = await client.get(f"/api/client/agent/runs/{run.run_id}/stream")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_stream_replays_buffered_events(ctx) -> None:
    """重连：GET /runs/{id}/stream 回放缓冲，且仍只有一个 is_end。"""
    client, _, _ = ctx
    resp = await client.post(
        "/api/client/agent/stream", json={"session_id": "s1", "content": "hi"}
    )
    run_id = _frames(resp.text)[0]["meta"]["run_id"]

    replay = await client.get(f"/api/client/agent/runs/{run_id}/stream")
    assert replay.status_code == 200
    frames = _frames(replay.text)
    answers = [
        f["content"]["text"]
        for f in frames
        if f["type"] == "answer" and f["content"].get("text") and not f["is_end"]
    ]
    assert answers == ["hi"]
    assert sum(1 for f in frames if f["is_end"]) == 1
    assert frames[-1]["is_end"] is True


@pytest.mark.asyncio
async def test_stop_endpoint_returns_200_and_marks_cancelled(ctx) -> None:
    """D3：POST /runs/{id}/stop 标记 cancelled，立即返回且幂等。"""
    client, _, manager = ctx
    run = await _stuck_run(manager)
    resp = await client.post(f"/api/client/agent/runs/{run.run_id}/stop")
    assert resp.status_code == 200
    assert run.status is RunStatus.CANCELLED
    assert (await client.post(f"/api/client/agent/runs/{run.run_id}/stop")).status_code == 200
