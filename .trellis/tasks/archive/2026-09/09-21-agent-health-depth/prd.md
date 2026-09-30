# Agent 健康检查深度

## Goal

`GET /api/client/agent/health` 当前只反映 LLM 配置是否可解析，且 `status` 恒为 `"ok"`、HTTP 恒为 200——它不触及任何真实依赖，因此无法回答「Redis / Business / RAG 是否真的可用」。本任务把它扩展为分项依赖探测，并明确规定各项不可用时的语义、字段与授权行为，配齐授权与故障测试。

## Background（本会话已核实）

| 事实 | 证据 |
|---|---|
| 端点位置与现状 | `app/api/chat.py:99-107`，在 `create_chat_router` 内由 `include_health` 开关注册；`GET`，路径前缀 `/api/client/agent`（`chat.py:29`、`main.py:230-234`）。返回裸 dict `{status, llm_configured}`，无 Pydantic 模型 |
| `status` 是硬编码常量 | `chat.py:107` `"ok"` 与依赖无关；即使 `llm_configured=False` 仍为 `"ok"` 且 HTTP 200 |
| 探测性质 | 仅调纯函数 `resolve_llm_provider(settings)`（`config.py:113-139`）读配置，无任何网络调用 |
| 异常处理 | 只捕 `ValueError`（`chat.py:105`），其他异常冒泡为 500 |
| 当前无鉴权 | handler 无参数、router 无 `dependencies=`；`auth_dep` 只注入各 handler（`chat.py:35,52,66,76,93`），`include_health` 分支绕过它 |
| 管理员侧无 health | `main.py:235-238` 建 admin chat 路由未传 `include_health`，故仅 client 侧一个 health 端点 |
| Redis 探针现成 | `app/adapters/redis/chat_store.py:49-50` `init_db()` 即 `await self._r.ping()`；`:35` 客户端带 `socket_connect_timeout=2`。注意 `__init__` 只 `from_url` 不连接，故必须每次真 ping |
| Vector Set 探针现成 | `app/adapters/redis/vector_set.py:126-135` `ensure_version()` 对 `VADD/VSIM/VREM` 逐个 `COMMAND INFO`，缺任一抛 `VectorSetUnavailable`（`:26`）；`_command_info_present`（`:236-244`）判定 `[None]`/`{"VADD": None}` 为不支持。契约：不建 key、不写数据、幂等 |
| Vector Set 探针缺口 | `ensure_version` **需要 `index_version` 参数**（`:128` 会 `validate_version`），而 health 未必知道当前 active 版本（在线版本由 Business lexical 响应逐请求决定，`retrieval.py:168-170`）。当前没有「不依赖具体版本」的能力探测入口 |
| `_command_info_present` 有两份副本 | `vector_set.py:236-244` 与 `subject_index.py:295-303`，已被 `tests/rag/test_lexical_contract.py:97-101` 同时覆盖。**在线** RAG 用的是 `subject_index.RedisSubjectIndex`（`main.py:129`） |
| Business 无健康探针 | `business_http.py:17-141` 共 7 个方法全是业务查询，无 ping/health。失败在 `request()` 内归一为 `{"error": true, ...}`（`:44-59`）；`timeout_seconds=10.0`（`:18`） |
| Business 网关未暴露到 `app.state` | `main.py:125` 构造后仅传入 `AgentDependencies`（`:154-164`），未挂 `app.state` |
| 既有失败矩阵测试可作范本 | `tests/rag/test_fault_matrix.py` 按层组织 `TestRedisFailure`/`TestEmbeddingFailure`/`TestBusinessFailure`/`TestEvidenceFailure`，全用 mock 适配器 |
| **测试层缺口** | `tests/` 下 grep `health` 零命中；grep `TestClient`/`testclient` 零命中——**没有任何 API 层测试**；无 `conftest.py`；无 `respx` 使用（HTTP mock 统一 `unittest.mock.patch("httpx.request", ...)`，范本 `tests/adapters/test_business_http.py:16-24`） |
| **MinIO 不是在线依赖** | `app/` 全目录 grep `minio` 仅命中 `app/config.py:64-74` 的字段声明（无客户端、无网络调用）；MinIO SDK 只在 `jobs/importer/storage.py:17`。`config.py:53` 注释原文说明这些字段「仅为容身共享 .env…业务读取仍走 os.getenv」。Business readiness 亦明确排除（`business/app/.../application.yml:112`「Agent/MinIO 不作为 readiness 强制条件」） |
| spec 要求的五要素 | `agent-guidelines.md:353`：变更健康检查时必须明确**检查项、HTTP 状态、依赖不可用时的响应、公开字段、是否允许匿名访问**。`:351` 已把当前现状记为已知缺口。`:352` 要求**修改健康探针时必须补授权测试** |
| spec 反向约束 | `error-handling.md:89` 把「Controller 返回 HTTP 200，但 body 中塞非 200 错误码」列为**常见错误**——与本任务的「恒 200」决策直接抵触，需显式裁定并记录例外理由 |
| 日志字段白名单 | `error-handling.md:166-172`：结构化事件走 `log_event`，字段必须在 `_ALLOWED_FIELDS`（`app/shared/observability.py:37-43`）中，否则被静默过滤 |
| 信息泄露红线 | `error-handling.md:80-83`：不返回 SQL、堆栈、文件路径、对象存储详情、上游响应体、JWT 或密钥 |

## 已定决策（本会话确认）

1. **不含 MinIO 探测。** 见 Background 末段：MinIO 是在线进程零引用的 importer 离线依赖，纳入会因 importer 依赖抖动而误报 Agent 不健康。若需 MinIO 可见性，应归 importer/quality 或运维探针。
2. **HTTP 恒 200，降级在 body 表达。** 顶层 `status ∈ {ok, degraded}`，分项明细放 `checks`。理由：仓库无常驻宿主/容器部署与 k8s probe 配置（`agent-guidelines.md:355-359`），无自动摘流消费方；且 Business 不可用会经 `AgentServiceImpl.java:147-156` 被 Spring 映射为 503，若 Python 自身也返 503 会把「Business 抖了一下」级联放大为「Agent 被摘除」。
   - **这是对 `error-handling.md:89` 的有意例外**：健康检查是诊断端点，不承载业务响应。必须在 spec 中显式登记该例外与理由，否则文档与实现再次背离。

## Requirements

### R1 分项探测

`GET /api/client/agent/health` 必须报告分项依赖状态，至少覆盖：

- `llm`：LLM 配置可解析性（维持现有 `resolve_llm_provider` 纯配置判定——其本质就是配置校验，无网络端点可探）。
- `redis`：会话存储可用性。必须**真实执行** PING（复用 `RedisChatStore.init_db`，`chat_store.py:49-50`），不得以「store 构造成功」代替。
- `business`：Business HTTP 网关可用性。必须**真实发起**请求。
- `rag`：**条件分项**。`RAG_ENABLED=false`（`config.py:48` 默认）时报 `disabled`（非 `down`），且**不发起** Vector Set 探测；`=true` 时探测 Vector Set 命令能力。

### R2 分项取值与语义

- 每分项取值为有限枚举：`ok` / `down` / `disabled`。不得用异常文本、布尔混合或裸字符串表达。
- 「功能开关关闭」必须表达为 `disabled`，**不得**当成故障。
- 顶层 `status`：全部分项为 `ok` 或 `disabled` 时 → `ok`；任一为 `down` 时 → `degraded`。
- 探测**不得短路**：某一分项失败后其余分项仍须被探测并如实报告。

### R3 fail-closed 与超时

- 任何探测抛异常、超时或返回 `{"error": true}`（`business_http.py:44-59`）必须判为 `down`，不得因捕获异常而误报 `ok`；禁止 `except Exception: pass`（`error-handling.md:90`）。
- 超时预算：Redis 复用 `socket_connect_timeout=2`（`chat_store.py:35`）；Business 复用 `timeout_seconds=10.0`（`business_http.py:18`）或为 health 收窄为独立更短值。
- 探测总耗时有明确上界，不得挂死。是否并发探测与总预算取值在 `design.md` 决定。

### R4 RAG 能力探测不依赖具体版本

- 需新增「不依赖 `index_version`」的 Vector Set 能力探测入口（当前 `ensure_version` 强制 `validate_version`，health 无从得知 active 版本）。
- 由于本任务会新增**第三个** `COMMAND INFO` 消费方，须同时消除 `vector_set.py:236-244` 与 `subject_index.py:295-303` 的 `_command_info_present` 重复实现，抽为单一定义。既有测试 `tests/rag/test_lexical_contract.py:97-101` 需相应更新。

### R5 授权

- health 端点的可访问性必须被明确决定并**测试**（`agent-guidelines.md:352`）。
- 决策：**维持 Python 侧匿名现状，并补授权测试钉住该行为**。理由：浏览器只访问 `/api/**`、不直连 `:8090`（`backend/index.md:26`），直连 `:8090` 仅内部调用方；经 Spring 代理的公开路径已由 `ClientAgentController` 的必填 `Authorization` + `SecurityConfig.java:74` 的 `.authenticated()` 强制登录。改 Python 为强制鉴权会使内部编排探针需要 token，收益不抵成本。
- 该两层不一致（Python 匿名 / Java 必填）须在 spec 与 README 中记录为**有意设计**，不得留作未解释的矛盾。

### R6 字段与信息泄露

- 响应体禁止包含上游错误正文、堆栈、文件路径、连接串、桶名、JWT 或密钥（`error-handling.md:80-83`）；Business 的 `{"error": true, "message": ...}` 原文不得直接透出。
- 若新增 `log_event` 事件，其字段须同步 `app/shared/observability.py:37-43` 白名单（`error-handling.md:166-172`），否则字段被静默过滤。

### R7 文档同步

- 响应字段或状态码变化时同步 `backend/agent/README.md:434` 的端点表与 `docs/spec/openapi.yaml:2887-2913`（后者现声明响应为通用透传 `{code,message,data:string}`，与 Agent 实际返回不符，属既有漂移——本任务至少登记为已知债务）。
- 在 spec 中登记 R2 对 `error-handling.md:89` 的有意例外。

## Acceptance Criteria

- [ ] **AC1** 新增 `tests/api/test_health.py`（需自建 API 层测试脚手架，当前 `tests/` 无 `TestClient`、无 `conftest.py`）用 `fastapi.testclient.TestClient` 对 `/api/client/agent/health` 发起 GET，断言 HTTP 状态码与响应键集合稳定。
- [ ] **AC2** 全部依赖可用（mock 全绿）时各分项均为 `ok` 或 `disabled`，顶层 `status == "ok"`，HTTP 200。
- [ ] **AC3** mock `store.init_db` 抛 `redis.ConnectionError` 时 `redis` 分项为 `down`、顶层 `status == "degraded"`，且**其余分项仍被探测并如实报告**（验证不短路）。
- [ ] **AC4** mock `httpx.request` 抛 `httpx.ConnectError`（范本 `tests/adapters/test_business_http.py:57-65`）时 `business` 分项为 `down`；Business 返回 `{"error": true, ...}` 时同判 `down`。
- [ ] **AC5** `RAG_ENABLED=false` 时 `rag` 分项为 `disabled`（**非** `down`），且断言**未发起**任何 Vector Set 探测调用。
- [ ] **AC6** `RAG_ENABLED=true` 且 `COMMAND INFO VADD` 返回 `[None]`（桩法复用 `tests/rag/test_lexical_contract.py:97-101`）时 `rag` 为 `down`；三条命令均存在时为 `ok`。断言探测入口**不需要** `index_version` 参数。
- [ ] **AC7** `resolve_llm_provider` 抛 `ValueError`（无任何 Key）时 `llm` 分项为 `down`，且**不触发**任何网络或 Redis 调用。
- [ ] **AC8** 授权测试：无 `Authorization` header 的 GET 断言当前选定策略（匿名 → 200）；经 Spring 代理需登录这一事实在 spec/README 中已记录。
- [ ] **AC9** 响应体不含敏感信息：断言序列化后不匹配 `redis://`、`Bearer `、`minioadmin`、`Traceback`、`.py", line` 等模式。
- [ ] **AC10** 探测总耗时有界：注入「永不返回」的 Redis/Business 桩，断言请求在预设超时内返回，不挂死。
- [ ] **AC11** `_command_info_present` 重复实现已消除：`tests/rag/test_lexical_contract.py:97-101` 更新后仍绿，且全仓仅剩一处定义。
- [ ] **AC12** `uv run pytest`（`backend/agent`）全绿；基线为 `backend/index.md:50` 记录的 413 passed。
- [ ] **AC13** MinIO 不在响应字段中，且 `app/` 下无新增 MinIO 导入（grep 断言，防范围蔓延）。

## Out of Scope

- **MinIO 探测**（已定决策 1）。
- **修改 Spring/Business 侧**：`ClientAgentController`、`SecurityConfig`、`AgentServiceImpl` 的错误映射属 Java 层。本任务须在 PRD/spec 显式声明外部事实：Spring 代理仍会把上游 5xx 归一为 503（`AgentServiceImpl.java:147-156`）。
- **新增 k8s/容器健康探针配置**（仓库无常驻宿主部署假设，`agent-guidelines.md:355-359`）。
- **Embedding 服务（DashScope）探测**：需外网与 Key 校验，会把 health 变成外网依赖。
- **MySQL 探测**：在线 Agent 不直连 MySQL（词法能力走 Business HTTP）。
- **把 `{code,message,data}` 内联响应重构为 `components.schemas` 复用**（全文 68 路径规模，独立工程）。

## Notes

- 复杂任务：`task.py start` 前需 `design.md`（探测编排与并发、超时总预算、Business 探针形态（复用什么请求 vs 专用方法）、能力探测入口放置点、API 测试脚手架形态）与 `implement.md`。
- 调研报告：`.trellis/tasks/09-21-agent-health-depth/research/health-endpoint-facts.md`（本任务的事实来源，含全部 file:line）。
- spec 里已有一处对本任务的既有描述需在实现后更新：`agent-guidelines.md:351`。
