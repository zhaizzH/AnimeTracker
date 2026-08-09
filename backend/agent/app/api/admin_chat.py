import json
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.admin_config import require_admin
from app.api.chat import get_service, get_store
from app.schemas.auth import UserInfo
from app.schemas.chat import ChatRequest
from app.schemas.session import (
    DeleteResponse,
    MessageOut,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionInfo,
)
from app.service.chat import ChatService

router = APIRouter(prefix="/api/admin/agent/chat")


@router.post("/stream")
async def admin_chat_stream(
        req: ChatRequest,
        user: UserInfo = Depends(require_admin),
        svc: ChatService = Depends(get_service),
):
    store = get_store()
    sessions = await store.get_user_sessions(user.user_id)
    if not any(s.session_id == req.session_id for s in sessions):
        raise HTTPException(status_code=404, detail="会话不存在或无权限")
    return await svc.stream_chat(
        session_id=req.session_id,
        content=req.content,
        user_id=user.user_id,
        role=user.role,
        token=user.token,
    )


@router.get("/sessions")
async def list_sessions(user: UserInfo = Depends(require_admin)):
    store = get_store()
    sessions = await store.get_user_sessions(user.user_id)
    return [SessionInfo(
        session_id=s.session_id,
        title=s.title,
        message_count=s.message_count,
        created_at=s.created_at,
    ) for s in sessions]


@router.post("/sessions")
async def create_session(body: SessionCreateRequest, user: UserInfo = Depends(require_admin)):
    store = get_store()
    session_id = body.session_id or str(uuid.uuid4())
    await store.create_session(user.user_id, session_id)
    return SessionCreateResponse(session_id=session_id)


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str, user: UserInfo = Depends(require_admin)):
    store = get_store()
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
async def delete_session(session_id: str, user: UserInfo = Depends(require_admin)):
    store = get_store()
    await store.delete_session(session_id, user.user_id)
    return DeleteResponse()
