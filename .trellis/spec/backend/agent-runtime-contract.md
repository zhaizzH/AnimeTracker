# Agent 角色、提示词与流式输出契约

源码核对：2026-09-10。适用于能力自述、中文输出、日期工具、Prompt 热更新及聊天 SSE 排障。

## 角色与工具是能力判断的依据

入口由 `backend/agent/app/agent/graph.py::_route_from_entry` 读取 `state.user.role` 决定。`ADMIN` 直接进入 `admin_agent`，普通用户经过 `gateway_router` 进入三个客户端节点。页面名称不决定节点；必须核对 JWT 角色、服务端 state 和实际注册工具。

| 节点 | 当前注册的主要能力 | 源码（相对 backend/agent） |
|---|---|---|
| search_agent | rag_search_subjects、详情、剧集、收藏读取、当前时间 | `app/agent/client/search.py` |
| discover_agent | rag_discover_subjects、日程、收藏读取、当前时间 | `app/agent/client/discover.py` |
| recommend_agent | rag_recommend_subjects、收藏读取、待确认收藏/进度动作、当前时间 | `app/agent/client/recommend.py` |
| admin_agent | 目录只读工具、recent 导入、当前时间；未注册 rag_* | `app/agent/admin/tools.py` |

客户端始终注册对应 `rag_*` 工具；`main.py::_build_agent_dependencies` 在 `RAG_ENABLED=false` 时注入不可用索引/Embedding 与 Business fallback。工具名称、功能开关、索引 ACTIVE 和本次实际召回路径是四种不同事实。

当前图没有 `capability_agent` 或对 RAG 能力问题的确定性响应。客户端提示词规定依据工具回答能力问题，但管理员提示词只描述目录查询与导入，不能把客户端 RAG 自述规则当成所有角色的已实现功能。新增工具应在对应节点显式注册，禁止仅改提示词宣称具备能力。

## Prompt 与模型配置的加载时序

1. `app/adapters/redis/prompt_repository.py::initialize_snapshot` 启动时读取 `agent:prompt:{key}` 的 JSON `promptContent`，建立进程内快照。
2. `get` 优先读快照，缺失时读本地文件。直接修改 Redis 不会自动更新已运行进程；`set/reset` 会刷新当前仓储实例，其他 worker 仍需刷新或重启。
3. `app/adapters/prompts/file_prompt.py::load_prompt` 有 `_PROMPT_CACHE`。本地 Markdown 修改也不保证已运行实例立即生效；`reset` 删除托管项不等于清空文件缓存。
4. `app/agent/run.py::run_domain_agent` 取 Prompt 并按需追加 PendingAction，再传入 `SystemMessage`；没有统一语言过滤层。
5. 模型配置使用另一套 `app/adapters/redis/model_config_repository.py` 短缓存，不能套用 Prompt 快照规则。供应商与模型参数装配见 `app/adapters/llm/agent_factory.py`。

排障依次核对实际服务地址/进程、用户角色、节点、Prompt 来源、进程内快照与模型配置。只检查磁盘文件或当前 shell 环境，不能证明另一运行进程加载了同样配置。不得把连接检查未返回结果直接判定为服务不存在。

## 中文与 thinking 的实际边界

客户端三个领域 Prompt 明确要求简体中文思考与回答；gateway 也有中文指令。`resources/prompt/admin/admin_agent_prompt.md` 只要求简体中文回答风格，没有同样的内部 reasoning 指令。Prompt 属于模型指令，不是确定性语言校验。

当前链路：`agent_factory.py` 捕获供应商 reasoning → `runtime.py::_extract_reasoning_content_from_chunk` → `run.py` 回调 → `app/chat/event_sink.py` → `app/chat/streaming.py` → 前端。

已知限制：

- `runtime.py` 对每个 reasoning chunk 调用 `strip()` 后拼接，英文分词块的首尾空格会丢失，可能出现连续单词；不能据此断定模型原始输出没有空格。
- 没有英文检测、中文翻译或中文状态替换；不得宣称 SSE 保证只输出中文。
- `agent_stream` 一旦收到正文就置 `is_answering=true`，后续 reasoning 不再输出；多个模型轮次的正文会串接，可能同时包含工具前说明和最终回答。
- `ChatService` 保存回答与工具名；前端加载历史仅恢复 role/content，不恢复 thinking。
- 若未来用固定状态替代原始 reasoning，应标为处理状态，不得伪称模型已经用中文思考。

## 日期、日程与状态

`app/agent/time_tool.py` 返回 Asia/Shanghai 当前时间；缺少系统时区库时回退固定 UTC+8。Gateway Prompt 注入当日日期，领域节点依赖 `get_current_time` 工具，当前没有代码强制“先取时间再查日程”。历史回答日期不能作为今天的事实。

推荐契约：今天/本周/本季请求使用当前时间工具结果生成条件；日程约定 `weekday=0` 为周日、`-1` 为全部。不要直接把 Python `weekday()`（周一为 0）作为 Business 参数。

季度与播出状态存在跨层偏差，详见 [RAG 检索契约](./rag-retrieval-contract.md)。日程、评分和主创描述必须来自本次权威工具结果；工具可调用并不能证明模型已使用正确日期。

## 验证与当前测试缺口

- `tests/agent/test_client_prompt_contract.py` 仅验证三个本地 Prompt 包含指定文字；不验证管理员、Redis 覆盖、模型遵循程度或 SSE 展示。
- `tests/agent/test_capability_route.py` 引用了当前缺失的 `_capability_agent`、`_is_rag_capability_question`、`_NON_CHINESE_THINKING_FALLBACK`，完整 pytest 在收集阶段失败。该文件不能作为功能已实现的证据。
- 后续修复需覆盖角色路由、Prompt 缓存更新、reasoning 空格保留、跨工具轮次事件、日期先后依赖及真实模型回放；mock/静态测试和真实模型行为必须分别报告。
- SSE 兜底最终回答目前未加入 `aggregated_answer`，可能显示成功但保存为空；回调异常还会被捕获。新增确定性节点必须同时验证展示与历史保存，见 `app/chat/streaming.py::stream_agent_events`。
