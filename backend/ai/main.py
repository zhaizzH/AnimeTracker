"""
AnimeTracker AI Agent — FastAPI 应用入口

FastAPI + LangChain 集成，提供 SSE 流式聊天服务。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat import router as chat_router
from api.sessions import router as sessions_router
from api.config_api import router as config_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    from config import settings
    # 初始化会话存储
    from storage.session_store import create_session_store
    app.state.session_store = await create_session_store()
    yield
    # 关闭时
    await app.state.session_store.close()


app = FastAPI(
    title="AnimeTracker AI Agent",
    description="AI Assistant for AnimeTracker — LangChain + DashScope",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(config_router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
