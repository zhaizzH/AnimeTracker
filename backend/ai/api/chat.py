"""
聊天 API 路由

POST /api/chat — SSE 流式聊天
GET  /api/chat/{session_id}/messages — 获取会话历史
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/chat/{session_id}/messages")
async def get_chat_messages(session_id: str):
    """获取会话历史消息"""
    pass  # Phase 3 实现


@router.post("/api/chat")
async def chat():
    """发送聊天消息（SSE 流式返回）"""
    pass  # Phase 3 实现
