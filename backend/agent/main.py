import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat as chat_api
from app.api import admin_config as admin_config_api
from app.api import import_api as import_api_api
from app.api.admin_config import require_admin
from app.api.deps import verify_token
from app.agent.graph import build_graph
from app.config import resolve_llm_provider, settings
from app.core.observability import TraceContextMiddleware, configure_logging
from app.core.prompt_sync import initialize_agent_prompt_snapshot
from app.db.redis_store import RedisStore
from app.service.chat import ChatService

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动即校验 LLM 配置；只记录供应商与模型名，绝不记录密钥
    resolved = resolve_llm_provider(settings)
    logger.info("LLM 供应商: %s, 模型: %s, 路由模型: %s", resolved.provider, resolved.model, resolved.route_model)

    logger.info("初始化 Redis 存储...")
    store = RedisStore(settings.redis_url)
    try:
        await store.init_db()
    except Exception as exc:
        logger.warning("Redis 连接失败,启动继续(会话功能将不可用): %s", repr(exc))
    app.state.store = store

    logger.info("初始化托管提示词快照...")
    initialize_agent_prompt_snapshot()

    logger.info("构建 client agent 图...")
    graph = build_graph()

    logger.info("创建聊天服务...")
    app.state.chat_service = ChatService(store=store, graph=graph, settings=settings)

    yield
    logger.info("正在关闭应用...")


app = FastAPI(title="AnimeTracker Agent", version="3.0.0", lifespan=lifespan)

app.add_middleware(TraceContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_api.create_chat_router(
    prefix="/api/client/agent",
    auth_dep=verify_token,
    include_health=True,
))
app.include_router(chat_api.create_chat_router(
    prefix="/api/admin/agent/chat",
    auth_dep=require_admin,
))
app.include_router(admin_config_api.router)
app.include_router(import_api_api.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.agent_host, port=settings.agent_port, reload=True)
