import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.db.database import init_db
from app.agent.core import create_agent_executor
from app.chat.manager import ConnectionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

agent_executor = None
connection_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_executor, connection_manager
    logger.info("Initializing database...")
    init_db()
    logger.info("Creating agent executor...")
    agent_executor = create_agent_executor()
    connection_manager = ConnectionManager(agent_executor)
    yield
    logger.info("Shutting down...")


app = FastAPI(title="AnimeTracker Agent", version="1.0.0", lifespan=lifespan)


@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    try:
        await connection_manager.handle(ws)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run(
        "main:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=True,
    )
