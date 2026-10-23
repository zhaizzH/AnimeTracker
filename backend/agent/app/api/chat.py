import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.chat.ports import ChatStore
from app.chat.runs import ChatRunManager
from app.config import settings
from app.api.health import build_health_report
from app.api.sse import create_sse_response
from app.chat.user import UserInfo
from app.api.schemas.chat import ChatRequest
from app.api.schemas.session import (
    DeleteResponse,
    MessageOut,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionInfo,
)
from app.chat.service import ChatService


def get_store(request: Request) -> ChatStore:
    return request.app.state.store


def get_service(request: Request) -> ChatService:
    return request.app.state.chat_service


def get_runs(request: Request) -> ChatRunManager:
    return request.app.state.chat_runs


async def _assert_session_owner(store: ChatStore, session_id: str, user_id: int) -> None:
    """会话归属校验（Q13）：不属于当前用户一律 404，不暴露存在性。"""
    sessions = await store.get_user_sessions(user_id)
    if not any(s.session_id == session_id for s in sessions):
        raise HTTPException(status_code=404, detail="会话不存在或无权限")


def create_chat_router(*, prefix: str, auth_dep, include_health: bool = False) -> APIRouter:
    router = APIRouter(prefix=prefix)

    @router.post("/stream")
    async def chat_stream(
            req: ChatRequest,
            user: UserInfo = Depends(auth_dep),
            svc: ChatService = Depends(get_service),
            store: ChatStore = Depends(get_store),
            runs: ChatRunManager = Depends(get_runs),
    ):
        await _assert_session_owner(store, req.session_id, user.user_id)
        # D2：同会话已有 RUNNING run 时不让静默并存，交由前端让用户显式选择。
        active = runs.active_for_session(req.session_id)
        if active is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "active_run_id": active.run_id,
                    "status": active.status.value,
                    "capabilities": ["interrupt"],
                },
            )
        run = await svc.start_run(
            session_id=req.session_id,
            content=req.content,
            user_id=user.user_id,
            role=user.role,
            token=user.token,
        )
        return create_sse_response(runs.subscribe(run.run_id))

    @router.get("/runs/{run_id}/stream")
    async def run_stream(
            run_id: str,
            after: int = 0,
            user: UserInfo = Depends(auth_dep),
            runs: ChatRunManager = Depends(get_runs),
    ):
        """重连订阅同一 run，从第 ``after`` 个事件起回放（Q10/Q14）。"""
        run = runs.get(run_id)
        if run is None or run.user_id != user.user_id:
            raise HTTPException(status_code=404, detail="run 不存在或无权限")
        return create_sse_response(runs.subscribe(run_id, after=after))

    @router.post("/runs/{run_id}/stop")
    async def run_stop(
            run_id: str,
            user: UserInfo = Depends(auth_dep),
            runs: ChatRunManager = Depends(get_runs),
    ):
        """逻辑停止（D3）：标记 cancelled 并立即返回，底层 task 自然跑完。"""
        run = runs.get(run_id)
        if run is None or run.user_id != user.user_id:
            raise HTTPException(status_code=404, detail="run 不存在或无权限")
        await runs.stop(run_id)
        return {"run_id": run_id, "status": run.status.value}

    @router.get("/sessions/{session_id}/run")
    async def session_run(
            session_id: str,
            user: UserInfo = Depends(auth_dep),
            store: ChatStore = Depends(get_store),
            runs: ChatRunManager = Depends(get_runs),
    ):
        """刷新后恢复通道（Q10）：返回当前/最近一条 run 的 id 与状态。"""
        await _assert_session_owner(store, session_id, user.user_id)
        state = await runs.resolve_session_run(session_id)
        if state is None:
            raise HTTPException(status_code=404, detail="该会话暂无 run")
        return {"run_id": state.run_id, "status": state.status}

    @router.get("/sessions")
    async def list_sessions(
            user: UserInfo = Depends(auth_dep),
            store: ChatStore = Depends(get_store),
    ):
        sessions = await store.get_user_sessions(user.user_id)
        return [SessionInfo(
            session_id=s.session_id,
            title=s.title,
            message_count=s.message_count,
            created_at=s.created_at,
        ) for s in sessions]

    @router.post("/sessions")
    async def create_session(
            body: SessionCreateRequest,
            user: UserInfo = Depends(auth_dep),
            store: ChatStore = Depends(get_store),
    ):
        session_id = body.session_id or str(uuid.uuid4())
        await store.create_session(user.user_id, session_id)
        return SessionCreateResponse(session_id=session_id)

    @router.get("/sessions/{session_id}/history")
    async def get_history(
            session_id: str,
            user: UserInfo = Depends(auth_dep),
            store: ChatStore = Depends(get_store),
    ):
        sessions = await store.get_user_sessions(user.user_id)
        if not any(s.session_id == session_id for s in sessions):
            raise HTTPException(status_code=404, detail="会话不存在或无权限")
        messages = await store.get_messages(session_id)
        return [MessageOut(
            role=m.role,
            content=m.content,
            tool_calls=json.loads(m.tool_calls) if m.tool_calls else None,
            created_at=m.created_at,
        ) for m in messages]

    @router.post("/sessions/{session_id}")
    async def delete_session(
            session_id: str,
            user: UserInfo = Depends(auth_dep),
            store: ChatStore = Depends(get_store),
    ):
        await store.delete_session(session_id, user.user_id)
        return DeleteResponse()

    if include_health:
        @router.get("/health")
        async def health(request: Request):
            # 刻意保持匿名：浏览器流量只会经 Spring 代理到达此路径，
            # 而该代理要求 JWT（ClientAgentController + SecurityConfig）。
            # 直连 :8090 的调用方属于内部编排探测。
            # 参见 spec agent-guidelines.md。
            state = request.app.state
            return await build_health_report(
                settings_obj=getattr(state, "settings", settings),
                store=getattr(state, "store", None),
                business=getattr(state, "business_gateway", None),
                rag_redis=getattr(state, "rag_redis", None),
            )

    return router
