# Task 4 Report

## Status

DONE_WITH_CONCERNS

RAG orchestration now sits behind explicit use case/ports/adapters, and the client graph receives `AgentDependencies` from `main.py`.

## Changed Files

- Created:
  - `backend/agent/app/adapters/business_http.py`
  - `backend/agent/app/adapters/llm/__init__.py`
  - `backend/agent/app/adapters/redis/subject_index.py`
  - `backend/agent/app/adapters/redis/user_preference.py`
  - `backend/agent/app/agent/dependencies.py`
  - `backend/agent/app/rag/use_case.py`
  - `backend/agent/tests/test_rag_use_case.py`
- Moved/deleted old locations:
  - `backend/agent/app/rag/embeddings.py` -> `backend/agent/app/adapters/llm/embeddings.py`
  - `backend/agent/app/rag/redis_index.py` -> `backend/agent/app/adapters/redis/subject_index.py`
- Modified:
  - `backend/agent/app/adapters/redis/__init__.py`
  - `backend/agent/app/agent/client/discover.py`
  - `backend/agent/app/agent/client/rag_tools.py`
  - `backend/agent/app/agent/client/recommend.py`
  - `backend/agent/app/agent/client/search.py`
  - `backend/agent/app/agent/graph.py`
  - `backend/agent/app/rag/retrieval.py`
  - `backend/agent/app/rag/user_profile.py`
  - `backend/agent/importer/quality.py`
  - `backend/agent/indexer/main.py`
  - `backend/agent/main.py`
  - `backend/agent/tests/indexer/test_worker.py`
  - `backend/agent/tests/integration/test_rag_pipeline_integration.py`
  - `backend/agent/tests/integration/test_redis_index_integration.py`
  - `backend/agent/tests/rag/test_embeddings.py`
  - `backend/agent/tests/rag/test_hybrid_retrieval.py`
  - `backend/agent/tests/rag/test_redis_index.py`
  - `backend/agent/tests/rag/test_user_profile.py`
  - `backend/agent/tests/test_domain_tool_registration.py`
  - `backend/agent/tests/test_rag_tools.py`

## Implementation Notes

- Added `HttpBusinessGateway`, `RedisSubjectIndex`, `DashScopeEmbeddingClient`, and `RedisUserPreferenceProvider` adapters.
- Added `RetrieveSubjectsUseCase.execute(query, mode, user)`.
- `RagRetrievalService` now requires explicit `authority_lookup` and `business_search`, and no longer imports `app.agent.http.call_api`.
- `build_rag_tools(use_case)` now returns thin LangChain tools and does not construct Redis, embeddings, or Business clients.
- `build_graph(dependencies)` now explicitly injects client node closures.
- `main.py` is the agent RAG composition root for Business/RAG Redis/index/embedding/preference/use-case/graph wiring.
- Search/discover/recommend Business fallback behavior is preserved at use-case level via mode-specific fallback callables.
- Admin static tool registry still receives non-RAG `search_tools`/`discover_tools`; RAG tools are only created through dependency injection.

## TDD Evidence

RED:

```text
uv run pytest tests/test_rag_use_case.py tests/test_rag_tools.py -v
ERROR tests/test_rag_tools.py
ImportError: cannot import name 'build_rag_tools' from 'app.agent.client.rag_tools'
```

```text
uv run pytest tests/test_rag_use_case.py -v
2 failed
ModuleNotFoundError: No module named 'app.rag.use_case'
```

GREEN:

```text
uv run pytest tests/test_rag_use_case.py tests/test_rag_tools.py -v
7 passed in 0.31s
```

## Targeted RAG/Graph Tests

```text
uv run pytest tests/test_rag_use_case.py tests/test_rag_tools.py tests/test_domain_tool_registration.py tests/rag -v
61 passed, 1 warning in 1.06s
```

Warning:

```text
DeprecationWarning: langchain-community is being sunset
```

## Full Python Suite

Default environment:

```text
uv run pytest -v
2 failed, 193 passed, 2 skipped, 2 warnings in 2.13s
```

Failures:

```text
tests/test_provider_resolve.py::test_default_provider_empty
AssertionError: assert 'dashscope' == ''

tests/test_provider_resolve.py::test_no_provider_no_key_raises
assert False
```

Observed cause: the pytest process can load `.env` before these tests, so `Settings(_env_file=None)` still sees LLM provider/key values from process environment. This is outside the RAG layering change.

Clean LLM environment:

```text
LLM_PROVIDER= DASHSCOPE_API_KEY= DEEPSEEK_API_KEY= uv run pytest -v
195 passed, 2 skipped, 2 warnings in 2.16s
```

Explicit skips:

```text
tests/integration/test_rag_pipeline_integration.py::test_rag_pipeline_writes_three_bundles_then_cleans_all_test_resources SKIPPED
tests/integration/test_redis_index_integration.py::test_redisearch_knn_fulltext_filter_and_alias_cleanup SKIPPED
```

Warnings:

```text
DeprecationWarning: langchain-community is being sunset
DeprecationWarning: dashscope.assistants is deprecated
```

## Self Review

- Verified no source imports remain for `app.rag.embeddings`, `app.rag.redis_index`, `UserProfileService`, `get_retrieval_service`, or direct RAG tool globals.
- Verified `app/agent/client/rag_tools.py` source does not contain `Redis.from_url` or `DashScopeEmbeddingClient(`.
- Verified moved Redis index tests still cover alias, vector bytes, safety filters, TAG separator, and no session key deletion.
- Verified preference tests cover Redis cache TTL, natural version expiry, invalid cache rebuild, cache outage fallback, vector validation, and pure weighting.

## Concerns

- Default `uv run pytest -v` fails two provider tests in this workspace when `.env` values are present in-process. Clean LLM env full suite passes.
- `app.agent.http.call_api` remains for existing non-RAG client/admin action tools; this task only moved RAG orchestration and Graph RAG dependencies.
