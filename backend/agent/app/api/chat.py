import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.chat.ports import ChatStore
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


def create_chat_router(*, prefix: str, auth_dep, include_health: bool = False) -> APIRouter:
    router = APIRouter(prefix=prefix)

    @router.post("/stream")
    async def chat_stream(
            req: ChatRequest,
            user: UserInfo = Depends(auth_dep),
            svc: ChatService = Depends(get_service),
            store: ChatStore = Depends(get_store),
    ):
        sessions = await store.get_user_sessions(user.user_id)
        if not any(s.session_id == req.session_id for s in sessions):
            raise HTTPException(status_code=404, detail="会话不存在或无权限")
        return create_sse_response(svc.stream_chat(
            session_id=req.session_id,
            content=req.content,
            user_id=user.user_id,
            role=user.role,
            token=user.token,
        ))

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
