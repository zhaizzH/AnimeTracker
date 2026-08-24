# Task 3 Implementation Report

## Status

DONE

## TDD Red Evidence

1. Added `backend/agent/tests/test_chat_stream_boundary.py`.
2. Ran `uv run pytest tests/test_chat_stream_boundary.py -v`.
3. Observed expected RED: 3 failed.
   - `ModuleNotFoundError: No module named 'app.chat.service'`
   - `FileNotFoundError: app/chat/service.py`
   - `ModuleNotFoundError: No module named 'app.api.sse'`

## Green Evidence

1. Ran `uv run pytest tests/test_chat_stream_boundary.py -v`.
2. Observed GREEN: 3 passed in 0.18s.

## Created

1. `backend/agent/app/chat/service.py`
2. `backend/agent/app/chat/streaming.py`
3. `backend/agent/app/chat/event_sink.py`
4. `backend/agent/app/api/sse.py`
5. `backend/agent/app/api/schemas/__init__.py`
6. `backend/agent/tests/test_chat_stream_boundary.py`

## Moved

1. `backend/agent/app/core/agent_runtime.py` -> `backend/agent/app/agent/runtime.py`
2. `backend/agent/app/core/observability.py` -> `backend/agent/app/shared/observability.py`
3. `backend/agent/app/core/pending_action.py` -> `backend/agent/app/chat/pending_events.py`
4. `backend/agent/app/service/chat.py` -> `backend/agent/app/chat/service.py`
5. `backend/agent/app/core/streaming.py` -> `backend/agent/app/chat/streaming.py`
6. `backend/agent/app/core/event_bus.py` -> `backend/agent/app/chat/event_sink.py`
7. `backend/agent/app/schemas/chat.py` -> `backend/agent/app/api/schemas/chat.py`
8. `backend/agent/app/schemas/session.py` -> `backend/agent/app/api/schemas/session.py`
9. `backend/agent/app/schemas/admin_config.py` -> `backend/agent/app/api/schemas/admin_config.py`
10. `backend/agent/app/schemas/sse_response.py` -> `backend/agent/app/api/schemas/sse.py`
11. `backend/agent/app/schemas/auth.py` -> `backend/agent/app/chat/user.py`
12. `backend/agent/app/schemas/pending_action.py` -> `backend/agent/app/chat/pending_action.py`

## Modified

1. `backend/agent/app/chat/events.py`: extended `AgentEvent` with existing SSE content fields needed to preserve wire payloads.
2. `backend/agent/app/api/chat.py`: wraps `ChatService.stream_chat(...)` with `create_sse_response(...)`; routes unchanged.
3. `backend/agent/main.py`: imports `ChatService` and observability from final paths; removed import-time `load_dotenv()` global environment mutation.
4. Agent/client/RAG/importer/indexer/test imports updated from old schema/core paths to final `app.chat`, `app.api.schemas`, `app.agent`, and `app.shared` paths.
5. `backend/agent/tests/test_provider_resolve.py`: clears LLM env per test to avoid importer CLI dotenv pollution inside the same pytest process.

## Deleted

1. `backend/agent/app/service/chat.py`
2. `backend/agent/app/core/streaming.py`
3. `backend/agent/app/core/event_bus.py`
4. `backend/agent/app/core/agent_runtime.py`
5. `backend/agent/app/core/observability.py`
6. `backend/agent/app/core/pending_action.py`
7. `backend/agent/app/schemas/admin_config.py`
8. `backend/agent/app/schemas/auth.py`
9. `backend/agent/app/schemas/chat.py`
10. `backend/agent/app/schemas/pending_action.py`
11. `backend/agent/app/schemas/session.py`
12. `backend/agent/app/schemas/sse_response.py`
13. `backend/agent/app/schemas/`
14. `backend/agent/app/service/`

## Behavior Preserved

1. SSE serialization remains in FastAPI/API layer via `app.api.sse`.
2. Existing SSE byte shape remains produced by `AssistantResponse`, `Content`, `MessageType`, and `serialize_sse`.
3. Internal Chat stream yields `AgentEvent` in original queue order.
4. `used_tools` de-duplication still records first `function_call` start per display name.
5. Exception mapping, PendingAction callbacks, producer cancellation, ContextVar resets, and observability fields remain in the streaming finally path.

## Verification

1. `uv run pytest tests/test_chat_stream_boundary.py tests/test_sse_contract.py tests/test_agent_graph_contract.py -v`
   - Result: 7 passed, 1 warning in 0.96s.
   - Warning: existing `langchain-community` deprecation warning from `app/llm/models.py`.
2. `uv run pytest tests/test_provider_resolve.py -v`
   - Result: 8 passed, 1 warning in 0.67s.
   - Warning: existing `langchain-community` deprecation warning from `app/llm/models.py`.
3. `uv run pytest -v`
   - Result: 197 passed, 2 skipped, 2 warnings in 1.68s.
   - Skips: Redis/RAG integration tests skipped by existing environment gating.
   - Warnings: existing `langchain-community` deprecation and DashScope Assistants API deprecation.

## Earlier Full-Suite Failure and Fix

1. Before fixing test isolation, `uv run pytest -v` collected 199 tests and failed 2 provider tests.
2. Root cause: importer/indexer CLI tests call `load_dotenv()`, leaving `.env` LLM values in process env before `tests/test_provider_resolve.py`.
3. Fix: provider tests now clear `LLM_PROVIDER`, `DEEPSEEK_API_KEY`, and `DASHSCOPE_API_KEY` with an autouse fixture.

## Self-Review

1. `grep -R "fastapi" backend/agent/app/chat --exclude-dir='__pycache__'` returned no matches.
2. Old path grep for `app.schemas`, `app.service.chat`, `app.core.streaming`, `app.core.event_bus`, `app.core.pending_action`, and `app.core.agent_runtime` returned no matches.
3. No Java, README, API route, Redis key, or Redis JSON shape changes were made.
4. No compatibility modules were left behind.

## Concerns

1. The full suite still emits two unrelated deprecation warnings from LangChain/DashScope dependencies.
