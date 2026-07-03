"""
会话管理 API 路由

POST /api/sessions — 创建会话
GET  /api/sessions — 会话列表
DELETE /api/sessions/{session_id} — 删除会话
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/api/sessions")
async def create_session():
    """创建新会话"""
    pass  # Phase 3 实现


@router.get("/api/sessions")
async def list_sessions():
    """获取所有会话列表"""
    pass  # Phase 3 实现


@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    pass  # Phase 3 实现
