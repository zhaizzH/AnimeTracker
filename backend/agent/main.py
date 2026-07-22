import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.llm.models import create_llm
from app.db.sqlite_store import SQLiteStore
from app.graph.graph import create_router_graph
from app.service.chat import ChatService
from app.api import chat as chat_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    store = SQLiteStore(settings.database_url)
    store.init_db()
    chat_api.chat_store = store

    logger.info("Creating LLM...")
    llm = create_llm(settings)

    logger.info("Building Router Graph...")
    graph = create_router_graph(llm, settings, store)

    logger.info("Creating ChatService...")
    chat_api.chat_service = ChatService(store=store, router_graph=graph, settings=settings)

    yield
    logger.info("Shutting down...")


app = FastAPI(title="AnimeTracker Agent", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_api.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=True,
    )
