import logging
from array import array
from contextlib import asynccontextmanager
import math
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
import redis

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat as chat_api
from app.api import admin_config as admin_config_api
from app.api import import_api as import_api_api
from app.admin.config_service import AdminConfigService
from app.adapters.business_http import HttpBusinessGateway
from app.adapters.llm.agent_factory import AgentLlmFactory
from app.adapters.llm.embeddings import DashScopeEmbeddingClient
from app.adapters.redis import RedisChatStore
from app.adapters.redis.entity_name_lookup import RedisEntityNameLookup
from app.adapters.redis.model_config_repository import RedisModelConfigRepository
from app.adapters.redis.prompt_repository import RedisPromptRepository
from app.adapters.redis.subject_index import RedisSubjectIndex
from app.adapters.redis.user_preference import RedisUserPreferenceProvider
from app.api.admin_config import require_admin
from app.api.deps import verify_token
from app.admin.import_service import ImportService
from app.agent.dependencies import AgentDependencies
from app.agent.graph import build_graph
from app.adapters.subprocess.import_job import SubprocessImportJobLauncher
from app.config import resolve_llm_provider, settings
from app.rag.retrieval import RagRetrievalService
from app.rag.schemas import RetrievalQuery
from app.rag.use_case import RetrieveSubjectsUseCase
from app.shared.observability import configure_logging, trace_context_middleware
from app.chat.service import ChatService

configure_logging()
logger = logging.getLogger(__name__)
_MAX_CANDIDATES = 15
_VECTOR_BYTES = 1024 * 4


class _UnavailableIndex:
    @staticmethod
    def lexical_search(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("RAG index disabled")

    @staticmethod
    def semantic_search(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("RAG index disabled")


class _UnavailableEmbeddings:
    @staticmethod
    def embed_documents(*_args: Any, **_kwargs: Any) -> list[list[float]]:
        raise RuntimeError("RAG embeddings disabled")


class _NoPreferenceProvider:
    @staticmethod
    def load(_user_id: int, _token: str | None):
        return None, False


def _business_fallbacks(business):
    def search(query: RetrievalQuery, *, token: str | None) -> dict | list:
        text = query.semantic_query or " ".join(query.keywords)
        return business.search_subjects(text, token=token, size=_MAX_CANDIDATES)

    def discover(query: RetrievalQuery, *, token: str | None) -> dict | list:
        if query.year_from == query.year_to and query.year_from and query.quarter:
            return business.request(
                "GET",
                "/api/client/subjects/season",
                params={"year": query.year_from, "quarter": query.quarter, "page": 1, "size": _MAX_CANDIDATES},
                token=token,
            )
        return business.request(
            "GET",
            "/api/client/subjects",
            params={"sort": "collectionTotal", "order": "desc", "page": 1, "size": _MAX_CANDIDATES},
            token=token,
        )

    def recommend(_query: RetrievalQuery, *, token: str | None) -> dict | list:
        return business.request(
            "GET",
            "/api/client/subjects",
            params={"sort": "collectionTotal", "order": "desc", "page": 1, "size": _MAX_CANDIDATES},
            token=token,
        )

    return {"search": search, "discover": discover, "recommend": recommend}


def _build_agent_dependencies(model_configs, prompts, import_service) -> AgentDependencies:
    business = HttpBusinessGateway(settings.backend_base_url)
    fallbacks = _business_fallbacks(business)
    if settings.rag_enabled:
        rag_redis = redis.Redis.from_url(settings.effective_rag_redis_url)
        index = RedisSubjectIndex(rag_redis, active_alias=settings.rag_index_alias)
        entity_name_lookup = RedisEntityNameLookup(
            rag_redis,
            index_version=settings.rag_index_version,
        ).lookup
        embeddings = DashScopeEmbeddingClient(settings.dashscope_api_key)
        preference_provider = RedisUserPreferenceProvider(
            rag_redis,
            business=business,
            vector_lookup=_subject_vector_lookup(rag_redis),
        )
    else:
        index = _UnavailableIndex()
        entity_name_lookup = None
        embeddings = _UnavailableEmbeddings()
        preference_provider = _NoPreferenceProvider()
    retrieval = RagRetrievalService(
        index,
        embeddings,
        authority_lookup=business.batch_subjects,
        business_search=fallbacks["search"],
        evidence_lookup=business.batch_evidence,
        resolve_evidence_lookup=business.resolve_evidence,
        entity_name_lookup=entity_name_lookup,
    )
    return AgentDependencies(
        business=business,
        retrieval=RetrieveSubjectsUseCase(
            retrieval=retrieval,
            preference_provider=preference_provider,
            business_searches=fallbacks,
        ),
        llm_factory=AgentLlmFactory(settings, model_configs),
        prompt_repository=prompts,
        import_service=import_service,
    )


def _subject_vector_lookup(rag_redis):
    def lookup(subject_id: int):
        try:
            raw = rag_redis.hget(f"rag:subject:{settings.rag_index_version}:{subject_id}", "vector")
        except Exception:
            return None
        if not isinstance(raw, bytes) or len(raw) != _VECTOR_BYTES:
            return None
        vector = array("f")
        vector.frombytes(raw)
        return list(vector) if all(math.isfinite(value) for value in vector) else None

    return lookup


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动即校验 LLM 配置；只记录供应商与模型名，绝不记录密钥
    resolved = resolve_llm_provider(settings)
    logger.info("LLM 供应商: %s, 模型: %s, 路由模型: %s", resolved.provider, resolved.model, resolved.route_model)

    logger.info("初始化 Redis 存储...")
    store = RedisChatStore(settings.redis_url)
    try:
        await store.init_db()
    except Exception as exc:
        logger.warning("Redis 连接失败,启动继续(会话功能将不可用): %s", repr(exc))
    app.state.store = store

    logger.info("初始化托管提示词快照...")
    model_configs = RedisModelConfigRepository(settings.redis_url)
    prompts = RedisPromptRepository(settings.redis_url)
    prompts.initialize_snapshot()
    app.state.admin_config_service = AdminConfigService(model_configs, prompts)
    app.state.import_service = ImportService(SubprocessImportJobLauncher())

    logger.info("构建 client agent 图...")
    graph = build_graph(_build_agent_dependencies(model_configs, prompts, app.state.import_service))

    logger.info("创建聊天服务...")
    app.state.chat_service = ChatService(store=store, graph=graph, settings=settings)

    yield
    logger.info("正在关闭应用...")


app = FastAPI(title="AnimeTracker Agent", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(trace_context_middleware)

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
