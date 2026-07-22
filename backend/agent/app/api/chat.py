import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import verify_token
from app.schemas.auth import UserInfo
from app.schemas.chat import ChatRequest
from app.schemas.session import (
    SessionInfo, MessageOut, SessionCreateRequest,
    SessionCreateResponse, DeleteResponse,
)
from app.service.chat import ChatService
from app.db.sqlite_store import SQLiteStore
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat")

# 全局实例（main.py 中初始化后替换）
chat_store: SQLiteStore | None = None
chat_service: ChatService | None = None


def get_store() -> SQLiteStore:
    if chat_store is None:
        raise RuntimeError("ChatStore not initialized")
    return chat_store


def get_service() -> ChatService:
    if chat_service is None:
        raise RuntimeError("ChatService not initialized")
    return chat_service


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    user: UserInfo = Depends(verify_token),
    svc: ChatService = Depends(get_service),
):
    """发送消息，返回 SSE 流"""
    # 检查会话权限
    store = get_store()
    sessions = store.get_user_sessions(user.user_id)
    existing_ids = {s.session_id for s in sessions}
    if req.session_id not in existing_ids:
        raise HTTPException(status_code=404, detail="会话不存在或无权限")

    return await svc.stream_chat(
        session_id=req.session_id,
        content=req.content,
        user_id=user.user_id,
        role=user.role,
    )


@router.get("/sessions")
async def list_sessions(
    user: UserInfo = Depends(verify_token),
):
    """获取当前用户会话列表"""
    store = get_store()
    sessions = store.get_user_sessions(user.user_id)
    return [SessionInfo(
        session_id=s.session_id,
        title=s.title,
        message_count=s.message_count,
        created_at=s.created_at,
    ) for s in sessions]


@router.post("/sessions")
async def create_session(
    body: SessionCreateRequest,
    user: UserInfo = Depends(verify_token),
):
    """创建新会话"""
    store = get_store()
    session_id = body.session_id or str(uuid.uuid4())
    store.create_session(user.user_id, session_id)
    return SessionCreateResponse(session_id=session_id)


@router.get("/sessions/{session_id}/history")
async def get_history(
    session_id: str,
    user: UserInfo = Depends(verify_token),
):
    """获取会话历史"""
    store = get_store()
    sessions = store.get_user_sessions(user.user_id)
    if not any(s.session_id == session_id for s in sessions):
        raise HTTPException(status_code=404, detail="会话不存在或无权限")

    messages = store.get_messages(session_id)
    return [MessageOut(
        role=m.role,
        content=m.content,
        tool_calls=__import__("json").loads(m.tool_calls) if m.tool_calls else None,
        created_at=m.created_at,
    ) for m in messages]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: UserInfo = Depends(verify_token),
):
    """删除会话"""
    store = get_store()
    store.delete_session(session_id, user.user_id)
    return DeleteResponse()


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "llm_configured": bool(settings.dashscope_api_key)}
