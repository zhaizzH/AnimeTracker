# Research: Agent 健康检查深度 — health 端点现状与依赖探测可复用模式

- **Query**: health 端点只反映 LLM 配置且恒返回 200；补充 Redis/Business/RAG(Vector Set)/MinIO 探测与依赖不可用时的语义、字段和授权测试。
- **Scope**: internal（backend/agent 为主，含 backend/business 代理层与 .trellis/spec 约束）
- **Date**: 2026-09-21

---

## 1. health 端点确切位置与现状

**位置**：`backend/agent/app/api/chat.py:99-107`（在 `create_chat_router` 工厂内部，由 `include_health` 开关控制注册）

```python
99   if include_health:
100      @router.get("/health")
101      async def health():
102          try:
103              resolve_llm_provider(settings)
104              configured = True
105          except ValueError:
106              configured = False
107          return {"status": "ok", "llm_configured": configured}
```

| 属性 | 实际值 | 证据 |
|---|---|---|
| HTTP 方法 | `GET` | `chat.py:100` |
| 路径 | `/api/client/agent/health`（prefix `/api/client/agent` + `/health`） | `chat.py:29` prefix 参数；`main.py:230-234` |
| 响应模型 | 无 Pydantic 模型，裸 `dict`；字段 `status`、`llm_configured` | `chat.py:107` |
| 返回码 | 恒 `200`；函数体无 `HTTPException`、无 `Response(status_code=...)` | `chat.py:101-107` |
| 探测性质 | **仅读配置**。调用纯函数 `resolve_llm_provider(settings)` 判断 Key/`LLM_PROVIDER` 是否可解析 | `config.py:113-139` |
| 异常处理 | 只捕获 `ValueError`；其他异常将冒泡为 500 | `chat.py:105` |
| 依赖注入 | 无 `Depends`，不接触 `app.state.store` / `graph` / Redis | `chat.py:101` |

**关键事实**：`status` 字段是硬编码常量 `"ok"`，与实际依赖无关。即使 `llm_configured=False`，`status` 仍为 `"ok"`，HTTP 仍为 200。

**另一实例**：`main.py:235-238` 用同一工厂创建了 `/api/admin/agent/chat` 路由，但未传 `include_health`（默认 `False`），因此**只有** `/api/client/agent/health` 一个 health 端点；管理员侧 chat 前缀下没有 health。

**启动期已存在的真实连通性检查**（可对照，非 health 端点）：

- `main.py:190-199`：`resolve_llm_provider` 启动即校验（失败则启动失败）；`RedisChatStore.init_db()` 失败仅 warning，**启动继续**（注释原文：「Redis 连接失败,启动继续(会话功能将不可用)」）。
- `main.py:202-204`：`prompts.initialize_snapshot()` 建立提示词快照；`config.py` 注释说明单项读取失败回退本地 Prompt。

---

## 2. 授权：health 当前无鉴权

| 端点 | 鉴权依赖 | file:line |
|---|---|---|
| `GET /api/client/agent/health` | **无**（handler 无参数、router 无 `dependencies=`） | `chat.py:99-107` |
| `POST /api/client/agent/stream` | `Depends(auth_dep)` = `verify_token` | `chat.py:35`；`main.py:232` |
| `GET/POST /api/client/agent/sessions` | `Depends(auth_dep)` = `verify_token` | `chat.py:52,66` |
| `GET .../sessions/{id}/history`、`POST .../sessions/{id}` | `Depends(auth_dep)` | `chat.py:76,93` |
| `/api/admin/agent/chat/*` | `auth_dep` = `require_admin` | `main.py:235-238` |
| `/api/admin/agent/prompts*`、`/config*` | `Depends(require_admin)`（每个路由显式声明） | `admin_config.py:22,27,35,43,51,56` |
| `/api/admin/agent/import` | router 级 `dependencies=[Depends(require_admin)]` | `import_api.py:7` |

**`create_chat_router` 的 `auth_dep` 是 router 级参数但只注入到各 handler**，不是 router 级 `dependencies=`，所以 `include_health` 分支可以、也确实绕过了它 —— 这是当前「health 未鉴权」的机制原因（`chat.py:29` 签名 vs `chat.py:99` 分支）。

**鉴权实现细节**：

- `verify_token`（`app/api/deps.py:12-33`）：本地 HS256 验签，不回调 Spring Boot；缺失/非 `Bearer ` 前缀/验签失败/无 `userId` 一律 401。角色非 `USER|ADMIN` 时降级为 `USER`（`deps.py:31`）。
- `require_admin`（`app/api/admin_config.py:10-15`）：先 `verify_token`，再校验 `role != "ADMIN"` → 403。

**上游 Business 代理层的授权差异（重要）**：`backend/business/agent/src/main/java/top/zhaizz/agent/controller/ClientAgentController.java:35-38` 的 `health(@RequestHeader("Authorization") String auth)` 把 `Authorization` 标注为**必填**。配合 `SecurityConfig.java:74` 的 `.requestMatchers("/api/client/**").authenticated()`，浏览器/前端路径上 `/api/client/agent/health` **必须带有效 JWT**，匿名请求在 Spring 侧即 401，Java 根本不会转发到 Python。

→ 结论：**Python 侧实际是「有守卫但守卫在上一层」**。直接命中 `:8090` 的调用方可匿名访问；经由 Spring 代理的正式路径需要登录。任何「公开匿名健康检查」的改动都会与此形成不一致。

**Business 侧的对照约定**：`SecurityConfig.java:62` 显式 `.requestMatchers("/actuator/health", "/actuator/health/**").permitAll()` —— 业务后端把健康端点做成匿名放行，且 `application.yml:110-130` 定义 liveness（仅进程）/ readiness（`include: db,redis`）两组；`application.yml:112` 注释明确「Agent/MinIO 不作为 readiness 强制条件」。`SecurityConfigAuthorizationTest.java:157-158` 有匿名访问 `/actuator/health` 的授权测试。

---

## 3. 依赖可用性探测的既有模式（逐个评估可复用性）

### 3.1 Redis（chat store）— 有现成探针

`app/adapters/redis/chat_store.py:35`：客户端构造时已带 `socket_connect_timeout=2`，**超时预算现成**。
`chat_store.py:49-50`：`init_db()` 实现就是一次 `await self._r.ping()`。
`chat_store.py:149` 起是 session/title 等其它操作，无其它 ping。

- **可复用**：`await app.state.store.init_db()`（即 `PING`）作为 Redis 探测，零新增生产代码。
- 注意：这是 **async** 探针，health handler 需为 `async def`（当前已是）。
- 注意：`RedisChatStore.__init__` 只调用 `from_url`，不会立即连接（`chat_store.py:35`），因此**每次探测都必须真正执行 ping**，不能靠「store 构造成功」判断。
- **探针语义**：`redis_url`（DB 0）用于会话；RAG 用的是 `effective_rag_redis_url`（`config.py:77-79` = `rag_redis_url or redis_url`）。二者可能是**不同实例**，探测会话 Redis 不能证明 RAG Redis 可用。

### 3.2 Vector Set 能力 — 有现成探针，但当前只在离线任务接线

`app/adapters/redis/vector_set.py:126-135` `RedisVectorSet.ensure_version()`：对 `VADD/VSIM/VREM` 逐个执行 `COMMAND INFO`，缺任一即抛 `VectorSetUnavailable`（`:26`）。
`app/adapters/redis/subject_index.py:91-100` `RedisSubjectIndex.ensure_version()`：同逻辑的**旧版副本**，抛 `RuntimeError`。
`_command_info_present`（`vector_set.py:236-244` 与 `subject_index.py:295-303`，两份重复实现）：`[None]`/`{"VADD": None}` 视为不支持。

**关键接线事实**：`ensure_version` 的调用方只有离线侧 —— `jobs/indexer/entity_index.py:58-59`、`jobs/indexer/main.py:115` 与 `:470`。

**在线侧从未调用**：`main.py:124-164` `_build_agent_dependencies` 只做 `RedisSubjectIndex(rag_redis)` 构造（`:129`）和 `RedisVectorSet` 无关的 `_subject_vector_lookup`（`:167-184`，直接用裸 `VEMB` 且 `except Exception: return None`），**没有** `ensure_version()` 调用。

→ 结论：Vector Set 能力探测的生产代码已存在且已有单测（`tests/rag/test_lexical_contract.py:97-101` 直接断言两份 `_command_info_present`），**在线 health 接入是新接线，不是新算法**。

### 3.3 RAG 可用性 — 有「显式不可用适配器」模式，无「探测」模式

`main.py:45-52` `_UnavailableIndex`：`lexical_search`/`semantic_search` 直接 `raise RuntimeError("RAG index disabled")`。
`main.py:55-58` `_UnavailableEmbeddings`：同理。
`main.py:61-64` `_NoPreferenceProvider`：返回 `(None, False)`。
装配开关在 `main.py:127-143`：`if settings.rag_enabled: ... else: 三个 _Unavailable*`。

- **可复用**：health 可据 `settings.rag_enabled`（`config.py:48`，默认 `False`）区分「关闭（预期，不算故障）」与「开启但探测失败（故障）」。这是**语义分层**的现成依据。
- **需新写**：把「RAG 是否真的可用」落成一个可调用的探针（要么调 Vector Set `ensure_version`，要么做一次最小 `VSIM`/`VEMB`）；现有代码只有「假装不可用」而没有「测试可用性」。

### 3.4 Business — 有归一化错误模式，无健康探针方法

`app/adapters/business_http.py:22-68` `request()` 是**唯一**出口，把所有失败归一为 `{"error": True, "code"?, "message"}`：

- `:44-45` TimeoutException → `{"error": True, "message": "后端服务超时"}`
- `:46-57` HTTPStatusError → 401 特判 `登录已过期`；其余取上游 `code`/`message`
- `:58-59` RequestError → `{"error": True, "message": "后端服务不可用: ..."}`
- `:60-68` 成功信封 `{code,message,data}` 拆 `data`；无 `data` 的 `Result<Void>` 归一为 `None`

现有方法（全部是业务查询，**没有任何 `ping`/`health` 方法**）：`batch_subjects`（`:70`）、`save_collection`（`:78`）、`search_subjects`（`:99`）、`batch_evidence`（`:107`）、`lexical_search`（`:115`）、`resolve_evidence`（`:128`）。

- **可复用**：错误归一语义（`_is_error` 判定，见 `retrieval.py:938-939`）、超时预算 `timeout_seconds=10.0`（`business_http.py:18`）。
- **需新写**：Business 健康探测。两个候选路径，各有取舍：
  - (a) 复用 `request("GET", <Business 现有健康路径>)` —— 需注意 `business_http.py:60-68` 会把 `{code,message,data}` 信封拆掉，`/actuator/health` 之类非信封结构会被原样返回。
  - (b) 新增 `HttpBusinessGateway` 上的专用轻量方法。
  - 注意 Business 侧 `/actuator/health` 由 Spring 自己提供（`business/app/pom.xml:18` actuator 依赖），且 **readiness 要求 MySQL+Redis**（`README.md:283`）——探它等于级联探测 Business→MySQL/Redis，与「只探 Agent 自身依赖」的范围可能冲突，属人工决策点。
- 注意：Business 网关实例在 `main.py:125` 构造，但**未存入 `app.state`**，只作为 `AgentDependencies.business` 传入图（`main.py:154-164`）。health handler 若要用它，需新增 `app.state` 暴露或在 lifespan 里另建。

### 3.5 RAG release / 版本解析 — 有 fail-closed 模式

`retrieval.py:158-171`：`versioned_semantic` 存在时，先调 Business lexical，取 `index_version = _index_version(lexical_payload)`；缺失即 `raise RuntimeError("Business lexical response missing indexVersion")` → 被 `:225-227` 的 `except Exception` 捕获，`redis_failed = True`，降级到 Business fallback（`:242-254`）。
`retrieval.py:925-935` `_index_version()`：只接受非空、无 `:`、无空白的字符串。

- **可复用**：版本合法性的校验函数 `_index_version`（`retrieval.py:925`）可复用为 health 报告 `index_version` 字段的校验。
- **本任务相关性**：如果 health 要报「RAG 索引版本」，此函数是唯一正确的解析入口；但**不建议**把「读 MySQL release」塞进 health（当前在线路径不直接查 MySQL release，见 `agent-guidelines.md` 关于 release 指针的约定，证据见第 8 节）。

### 3.6 既有失败矩阵测试（可作 AC 模板）

`tests/rag/test_fault_matrix.py`：按层组织 `TestRedisFailure`（`:81`）、`TestEmbeddingFailure`（`:115`）、`TestBusinessFailure`（`:151`）、`TestEvidenceFailure`（`:194`）、`TestUseCaseEvidenceIntegration`（`:232`）；全部用纯 mock 适配器，无真实网络。这是**本任务 AC 分层的现成范本**。

---

## 4. Vector Set 能力探测：`_command_info_present` 与 `ensure_version`

**定义**：`app/adapters/redis/vector_set.py:236-244`

```python
def _command_info_present(info: Any) -> bool:
    """Redis returns ``[None]`` for an unknown COMMAND INFO entry."""
    if not info:
        return False
    if isinstance(info, Mapping):
        return any(item is not None for item in info.values())
    if isinstance(info, (list, tuple)):
        return any(item is not None for item in info)
    return True
```

**用法（唯一在线调用点）**：`vector_set.py:126-135`

```python
def ensure_version(self, index_version: str) -> None:
    """Validate the server capability without creating a fake empty index."""
    validate_version(index_version)
    for command in ("VADD", "VSIM", "VREM"):
        try:
            info = self._redis.execute_command("COMMAND", "INFO", command)
        except Exception as exc:
            raise VectorSetUnavailable(f"无法探测 Redis Vector Set {command}") from exc
        if not _command_info_present(info):
            raise VectorSetUnavailable(f"Redis 未启用 Vector Set {command}；需要 Redis 8+")
```

- 契约：**不创建 key、不写数据、幂等**，可在 health 中安全调用（注释原文 "without creating a fake empty index"）。
- 异常类型 `VectorSetUnavailable(RuntimeError)`：`vector_set.py:26-27`。
- 需要的 client 类型：任意有 `execute_command` 的对象（`RedisVectorSet.__init__(redis_client)`，`:116`）；无需是 async。
- 同一段逻辑的另一副本：`subject_index.py:91-100`（抛 `RuntimeError`，消息尾缀「RAG 索引保持关闭」）。
- 重复实现风险：两份 `_command_info_present` 已被 `tests/rag/test_lexical_contract.py:97-101` 同时覆盖，改动时需同步。

**注意**：在线 RAG 用的是 `subject_index.RedisSubjectIndex`（`main.py:129`），它的 `ensure_version` 是同步方法、抛 `RuntimeError`；若 health 复用需注意**异常类型不同**（`VectorSetUnavailable` vs 裸 `RuntimeError`），且该实例未存 `app.state`。

---

## 5. Business 健康探测的既有入口

**结论：不存在。**

- `HttpBusinessGateway`（`business_http.py:17-141`）共 7 个方法，全部是业务查询，无健康/连通性方法（见 3.4 清单）。
- 唯一近似「探测」的是 `request()` 自身的异常归一（`business_http.py:32-59`）；调用方靠返回值是否含 `error` 判断，判定函数是 `retrieval.py:938-939`：

```python
def _is_error(response: Any) -> bool:
    return isinstance(response, Mapping) and bool(response.get("error"))
```

- 已有的「探 Business 可用性」的间接做法：`retrieval.py:556-561` `_authoritative_result` 捕获异常 → `RetrievalResult(available=False, reason="business_unavailable")`；`retrieval.py:618-623` `_business_fallback` 同样。这些是**检索路径内的降级**，不是可复用的独立探针。
- Business 网关实例未暴露到 `app.state`（`main.py:125, 154`），health 无法直接取到。

---

## 6. MinIO 是否属于 Agent 在线依赖 —— **不属于，建议排除出本任务范围**

**证据（全部指向 importer 离线侧）**：

| 证据 | 位置 | 说明 |
|---|---|---|
| MinIO SDK 导入 | `jobs/importer/storage.py:17` `from minio import Minio` | 只在 importer 存储适配器 |
| MinIO 客户端构造 | `jobs/importer/storage.py:47-64` | 读 `MINIO_*` 环境变量，非 `settings` |
| MinIO 读写 | `jobs/importer/storage.py:122,130,135,144-145` | `put_object` / `stat_object` / `bucket_exists` / `make_bucket` |
| MinIO 指纹 | `jobs/importer/quality.py:104-109`、`:246-252` | 离线质量报告 |
| MinIO 清理 | `jobs/importer/cleanup.py:39,58,108-115` | 离线清理 |
| 在线代码零引用 | `app/` 全目录 grep `minio` 仅命中 `app/config.py:64-74` | 只有配置字段声明，无客户端、无网络调用 |

**`app/config.py:64-74` 的 MinIO 字段是「容身共享 .env」的占位**，`config.py:53` 注释原文：

> `# ponytail: 以下字段仅为容身共享 .env（agent/importer 共用），避免 extra=forbid 报错；业务读取仍走 os.getenv`

即：`Settings` 声明 `minio_*` 只是因为 `Settings` 用 `extra="forbid"`（`config.py:9`），而 agent 与 importer 共用同一个 `.env`；在线代码**从不读取** `settings.minio_*`。`config.py:71-75` 的 `raw_bucket_must_be_private` 校验器是启动期唯一的 MinIO 相关逻辑，且是纯字符串比较、不触网。

**上游侧也不要求 MinIO**：`business/app/src/main/resources/application.yml:112` 注释「Agent/MinIO 不作为 readiness 强制条件」，`:124-125` readiness `include: db,redis`；`business/README.md:283` 同义。

**结论（明确）**：MinIO 是 importer 离线依赖，**不是 agent 在线服务的运行时依赖**。把 MinIO 探测放进 `/api/client/agent/health` 会引入一个在线进程从未使用的外部系统，并在 MinIO 不可用时误报 Agent 不健康。
**建议**：MinIO 探测**不在本任务范围**。若确实需要 MinIO 健康可见性，应归属 importer/quality 或运维探针，而非 agent health 端点。

---

## 7. 既有 health 相关测试：无

**确认结论：`backend/agent/tests/` 下没有任何 health 测试。**

- `tests/` 全目录 grep `health`：**0 命中**（`-i` 亦同）。
- `tests/` 全目录 grep `TestClient` / `from fastapi.testclient`：**0 命中** —— 没有任何 API 层（HTTP 路由）测试，现有测试全部是单元/适配器层。
- `tests/` 下**无 `conftest.py`**（`find tests -name conftest.py` 为空）；`pyproject.toml` 只有 `pythonpath=["."]` 与 `asyncio_mode="auto"`。
- 无 `respx` 使用（依赖已声明为 dev 依赖，`pyproject.toml` dev 组，但 grep 无命中），HTTP mock 统一用 `unittest.mock.patch("httpx.request", ...)`（模板见 `tests/adapters/test_business_http.py:16-24`）。
- 无 `verify_token` / `jwt_secret` 相关测试（grep 仅命中业务头断言）。

**可参考的测试组织方式**：`tests/rag/test_fault_matrix.py`（按故障层分 class）、`tests/adapters/test_business_http.py`（`unittest.mock.patch` + `MagicMock` 断言调用参数）、`tests/rag/test_lexical_contract.py:97-101`（`_command_info_present` 直接单测）。

---

## 8. spec 约束：健康检查 / 统一响应 / 状态码

### 8.1 `.trellis/spec/backend/agent-guidelines.md` — 「健康检查语义」专节（直接约束本任务）

`agent-guidelines.md:349-353`，原文要点：

- `:351` —「Agent `/api/client/agent/health` 当前始终返回 HTTP 200，并只反映 LLM 配置是否可解析；**不代表 Redis、Business、RAG 或 MinIO 可用**。」（即当前 spec 已把现状记为**已知缺口**）
- `:352` —「Business 的 liveness/readiness 配置见 `backend/business/app/src/main/resources/application.yml`；readiness 检查 MySQL 与 Redis，Security 只匿名放行 `/actuator/health` 与 `/actuator/health/**`，其他未显式允许的 URL 仍拒绝；**修改健康探针时必须补授权测试**。」
- `:353` —「变更健康检查时必须明确：**检查项、HTTP 状态、依赖不可用时的响应、公开字段和是否允许匿名访问**。」

→ 这五要素就是本任务 PRD 必须回答的清单，也是 AC 的骨架。

### 8.2 `.trellis/spec/backend/error-handling.md` — 状态码与响应结构约束

- `:12` —「统一响应为 `Result<T>{code,message,data}`，**HTTP 状态码与 `code` 相同**」（Java Business 层）。注意 Agent 直接挂在 Spring 之后，Spring 的 `ClientAgentController` 用 `Result<?>` 包装上游（`ClientAgentController.java:36-38`），而 Agent 自身返回裸 dict。
- `:84` —「**409 用于唯一约束或状态冲突；404 只在明确语义下可被工具解释为"不存在"**」
- `:89` — 常见错误第一条：「**Controller 返回 HTTP 200，但 body 中塞非 200 错误码。**」← **这条直接命中「恒返回 200 + body 表达降级」的选项，是本任务最关键的反向约束证据。**
- `:90` —「Python 工具用裸 `except Exception: return {}` 吞掉失败。」
- `:92` —「为局部场景新建另一套响应结构。」
- `:80-83` —「客户端可见信息」：**不返回** SQL、堆栈、文件路径、**对象存储详情**、上游响应体、JWT 或密钥；外部服务失败转换为领域化消息（例：「Agent 导入服务连接失败」）。
- `:166-172` — Agent 日志：结构化事件走 `log_event`，**字段必须在 `_ALLOWED_FIELDS` 白名单中**（`app/shared/observability.py:37-43`）；违规字段被静默过滤。当前白名单**不含**任何 health 字段，若 health 记事件需同步白名单。
- `:178` — 隐私红线：禁止记录 JWT、API Key、完整 Business 响应体。

### 8.3 相关 spec：`rag-retrieval-contract.md` / `agent-guidelines.md` 的 RAG 开关约定

- `agent-guidelines.md:18` —「RAG 索引运行前必须验证 Redis 提供 Vector Set 命令（至少 `VADD`、`VSIM`、`VREM`）；…**没有 Vector Set 时保持 `RAG_ENABLED=false` 或走 Business fallback，不得宣称已发布 RAG。**」
- `agent-guidelines.md:19` —「`RAG_ENABLED` 代码默认仍为 `false`。」（与 `config.py:48` 一致）
- `agent-guidelines.md:23` —「故障矩阵必须在测试中覆盖：Redis/Embedding/Business/Evidence 每层独立故障与组合故障，证明 fail-closed 或既定降级行为。」
- `agent-guidelines.md:413` —「运行环境仅提供普通 Redis 而未加载 Vector Set 时，不能执行 `jobs.indexer`。」
- `agent-guidelines.md:341` —「管理路由必须使用 `require_admin`，不能只靠提示词限制。」
- `agent-guidelines.md:342` —「`Settings` 使用 `extra="forbid"`；新增环境变量同步 `app/config.py` 与 `.env.example`。」
- `agent-guidelines.md:355-359` — 离线任务退出码/激活约定（与 health 无关，但说明「不得假设已有常驻宿主/容器部署」→ 影响探针接入形态：仓库无 k8s probe 配置可改）。

### 8.4 其它上下游文档

- `backend/agent/README.md:434` — 端点表：`GET /api/client/agent/health`，角色列写「**用户**」，描述「健康检查（含 LLM 配置校验）」。注意 `README.md:431-438` 整张表的权限列全部受 Spring Security 约束。
- `backend/business/README.md:16,283` — Business readiness = MySQL + Redis；MinIO 与 Agent 不参与。
- `docs/spec/openapi.yaml:2887-2913` — `/api/client/agent/health` 的 OpenAPI 定义**已声明 `Authorization` header `required: true`**，但响应 schema 是通用透传 `{code,message,data}`（`data: string`），与 Agent 实际返回的 `{status, llm_configured}` **不一致**。若要改响应体，此文件需同步。
- `backend/business/agent/src/main/java/top/zhaizz/agent/service/impl/AgentServiceImpl.java:147-156` — 代理层把上游 5xx 统一映射为 `ErrorType.SERVICE_UNAVAILABLE`（= 503，`ErrorType.java:57-61`），4xx 走 `mapUpstream4xx`。**这意味着：若 Python health 在依赖不可用时返回 503，前端会收到 Spring 的 503「服务暂不可用」，而不是 health 的降级明细。** 这是关键权衡证据（见下）。

---

## 9. 建议 Requirements 与 Acceptance Criteria（草案）

> 以下为研究结论推导的**建议稿**，供主 agent 写 `prd.md`。AC 全部设计为 `uv run pytest` 可验证。

### 9.1 建议 Requirements

- **R1 — 探测分项**：`GET /api/client/agent/health` 必须报告分项依赖状态，至少覆盖 **LLM 配置**、**Redis（会话存储）**、**Business（HTTP 网关）**；RAG/Vector Set 作为**条件分项**（仅当 `RAG_ENABLED=true` 时必须探测，关闭时报告 `disabled` 而非 `down`）。
- **R2 — 探测语义**：每分项取值为有限枚举（建议 `ok` / `down` / `disabled`），**不得**用异常文本、布尔混合或裸字符串表达；不得把「功能开关关闭」当成故障。
- **R3 — 探测必须真实触网**：Redis 分项必须实际执行 PING（复用 `RedisChatStore.init_db`，`chat_store.py:49-50`）；Business 分项必须实际发起 HTTP 请求（经 `HttpBusinessGateway`）；RAG 分项必须实际执行 `COMMAND INFO VADD/VSIM/VREM`（复用 `vector_set.py:126-135`），不得只读配置。LLM 分项维持现有 `resolve_llm_provider` 纯配置判定（其本质就是配置校验，无网络端点可探）。
- **R4 — 不确定即失败（fail-closed）**：任何探测抛异常、超时或返回 `{"error": true}`（`business_http.py:44-59`）必须判为 `down`，不得因捕获异常而误报 `ok`。禁止 `except Exception: pass`（`error-handling.md:90`）。
- **R5 — 超时预算**：探测总耗时有明确上界，单分项不得无限等待。Redis 复用 `socket_connect_timeout=2`（`chat_store.py:35`）；Business 复用 `timeout_seconds=10.0`（`business_http.py:18`）或为 health 收窄为独立更短值。
- **R6 — 授权**：health 端点的可访问性必须被明确决定并测试。候选：(a) 保持现状（Python 侧匿名，但经 Spring 代理仍需 JWT，`SecurityConfig.java:74`）；(b) 加 `auth_dep`。无论选哪个，都必须有**授权测试**（spec `agent-guidelines.md:352` 明确要求）。
- **R7 — 字段白名单（信息泄露）**：响应体**禁止**包含上游错误正文、堆栈、文件路径、连接串、桶名、JWT 或密钥（`error-handling.md:80-83`）；Business 的 `{"error": true, "message": ...}` 原文不得直接透出。
- **R8 — 范围排除**：**不含 MinIO 探测**（第 6 节结论：MinIO 是 importer 离线依赖，`app/` 零网络调用）。
- **R9 — 文档同步**：若响应字段或状态码变化，同步 `docs/spec/openapi.yaml:2887-2913`、`backend/agent/README.md:434`；若新增事件日志字段，同步 `observability.py:37-43` 白名单（`agent-guidelines.md:342` 的同步要求）。

### 9.2 建议 Acceptance Criteria（勾选项）

- [ ] **AC1** `uv run pytest tests/api/test_health.py` 通过；用 `fastapi.testclient.TestClient`（**需新增**，当前 `tests/` 零 API 层测试）对 `/api/client/agent/health` 发起 GET，断言 HTTP 状态码与响应键集合稳定。
- [ ] **AC2** 全部依赖可用（mock 全绿）时，各分项均为 `ok`，整体状态为健康值。
- [ ] **AC3** Redis PING 抛异常（mock `store.init_db` 抛 `redis.ConnectionError`）时，Redis 分项为 `down`，且**其余分项仍被探测并如实报告**（不得短路）。
- [ ] **AC4** Business 返回 `{"error": true, ...}`（mock `httpx.request` 抛 `httpx.ConnectError`，模板见 `tests/adapters/test_business_http.py:57-65`）时，Business 分项为 `down`。
- [ ] **AC5** `RAG_ENABLED=false`（`config.py:48` 默认）时，RAG 分项为 `disabled`（**非** `down`），且不发起 Redis Vector Set 探测。
- [ ] **AC6** `RAG_ENABLED=true` 且 `COMMAND INFO VADD` 返回 `[None]`（复用 `test_lexical_contract.py:97-101` 的桩法）时，RAG 分项为 `down`；三个命令全部存在时为 `ok`。
- [ ] **AC7** `resolve_llm_provider` 抛 `ValueError`（无任何 Key）时，LLM 分项为 `down` 或 `not_configured`，且**不触发**任何网络/Redis 调用。
- [ ] **AC8** 授权测试：无 `Authorization` header 的 GET 请求，断言选定的授权策略（401 或 200）。**此项的具体期望值由人工决策 D2 确定，测试与实现必须一致。**
- [ ] **AC9** 响应体不含敏感信息：断言响应 JSON 序列化后不匹配 `redis://`、`Bearer `、`minioadmin`、堆栈关键字（`Traceback`、`.py", line`）等模式。
- [ ] **AC10** 探测总耗时有界：注入「永不返回」的 Redis/Business 桩，断言请求在预设超时内返回（可用 `pytest` 的 timeout 或显式时延断言），不挂死。
- [ ] **AC11** 回归：`uv run pytest` 全套通过（当前基线 413 项，见 `agent-guidelines.md:239` 与 `:314` 的复核记录），确认改动未破坏既有测试。
- [ ] **AC12** MinIO 不在响应字段中，且 `app/` 下无新增 MinIO 导入（可用 grep 断言，防范围蔓延）。

### 9.3 不在本任务范围内（明确排除）

- **MinIO 探测**（第 6 节：importer 专属依赖，`app/` 零调用；上游 Business 也不把它列为 readiness 条件，`application.yml:112`）。
- **修改 Spring/Business 侧**：`ClientAgentController`、`SecurityConfig`、`AgentServiceImpl` 的错误映射（`AgentServiceImpl.java:147-156`）属 Java 层；本任务若只改 Python 响应语义，需在 PRD 中显式声明「Spring 代理仍会把 5xx 归一为 503」这一外部事实。
- **新增 k8s/容器健康探针配置**：仓库无常驻宿主/容器部署假设（`agent-guidelines.md:355-359`）。
- **Embedding 服务探测**（DashScope）：属于 RAG 链路但需外网调用与 Key 校验；是否纳入请人工决策（见 D3）。
- **MySQL 探测**：在线 Agent 不直连 MySQL（`retrieval.py` 的词法能力走 Business HTTP），无依赖可探。

---

## 10. 需人工决策的点

### D1【关键】「恒返回 200」该不该改？两个选项与取舍

**现状证据**：`chat.py:107` 恒 200；`error-handling.md:89` 把「HTTP 200 + body 内非 200 错误码」列为**常见错误**。

**选项 A — 依赖不可用时返回 HTTP 503**

- 做法：任一**必需**依赖（Redis / Business）`down` → `HTTPException(503)` 或 `JSONResponse(status_code=503)`；body 仍带分项明细。
- 支持理由：
  - `error-handling.md:89` 明确反对「200 里塞错误码」；
  - `error-handling.md:12` 要求 HTTP 状态与语义一致；
  - Spring 侧的 `AgentServiceImpl.java:149-151` **已经**把上游 5xx 映射为 `ErrorType.SERVICE_UNAVAILABLE`(503) —— 返回 503 与现有代理链路**语义自洽**，无需改 Java；
  - 负载均衡/编排系统能据此摘除实例。
- 代价 / 风险：
  - **级联放大**：Business 不可用会让 Agent 探针也 503，若上游据此摘除 Agent，则「只是 Business 抖了一下」会连带把本来能服务纯 LLM 对话的 Agent 摘掉；
  - **无宿主消费方**：仓库无 k8s probe 配置（`agent-guidelines.md:355-359`），503 可能只是让前端弹错；
  - 需区分「必需 vs 可选」依赖（RAG 关闭不能算 503 依据）。
- 需要先定的子问题：哪些依赖是**必需**（建议：LLM 配置、Redis；Business 视是否可降级而定）。

**选项 B — 保持 HTTP 200，在 body 内表达降级**

- 做法：恒 200，body 用顶层 `status: "ok" | "degraded" | "down"` + 分项明细表达。
- 支持理由：
  - 与**当前 Python 实现和 `README.md:434` 的既有契约**兼容，前端/代理零改动；
  - 与 spec 现状描述（`agent-guidelines.md:351`）不冲突，是「补字段」而非「改协议」；
  - 不触发 Spring 的 5xx → 503 映射，保留完整降级明细给调用方；避免级联摘除。
- 代价 / 风险：
  - **直接触犯 `error-handling.md:89`** 的「常见错误」条目（需要人工裁定这是否是可接受的例外，例如「健康检查是诊断端点，不属于业务响应」）；
  - 编排系统无法据此自动摘流。

**建议（非拍板）**：**混合方案**——HTTP 状态码与 body 双轨：(1) **liveness 语义**（进程活着、Python 可服务）恒 200；(2) 另设/或复用查询参数表达 readiness，仅当**必需**依赖 down 时返回 503。若人工只允许一个端点，建议优先满足 `error-handling.md:89`（选 A），但必须同时确认「上游不会因 Business 抖动级联摘除 Agent」。**此点必须由人工拍板。**

### D2 health 端点的授权策略

- 现状：Python 匿名（`chat.py:99-107`），Java 侧 `@RequestHeader("Authorization")` 必填 + `.authenticated()`（`ClientAgentController.java:36`、`SecurityConfig.java:74`）。两层的实际策略**已经不一致**。
- 选项：(a) 维持双侧不一致现状并加测试固化；(b) Python 也加 `auth_dep`，使直连 `:8090` 与经代理都需登录（一致性最好）；(c) 显式做成匿名端点（Python 保持匿名 + Java 放开 `/api/client/agent/health` 为 `permitAll`，对齐 Business `/actuator/health` 的做法 `SecurityConfig.java:62`）。
- 取舍：(b) 最安全但会让外部编排探针需要 token；(c) 便于探针接入但需改 Java（超出本任务可能的范围）；(a) 零改动但把不一致固化。
- 无论选哪个，spec `agent-guidelines.md:352` 都要求**补授权测试**（AC8）。

### D3 RAG 探测深度

- 选项：(a) 只探 Vector Set 命令能力（复用 `vector_set.py:126-135`，成本低、无外网）；(b) 追加探测 Embedding 服务（DashScope，需 Key + 外网，会引入新失败面与延迟）；(c) 追加读 MySQL `search_index_release` 拿 active 版本（当前在线路径不直连 MySQL，见 `retrieval.py` 全程走 Business HTTP，属**新增依赖**）。
- 建议：(a) 起步；(b)/(c) 需人工确认是否值得把 health 变成外网依赖。
- 注意 `ensure_version` 需要 `index_version` 参数（`vector_set.py:128` 会 `validate_version`），而 health 未必知道当前 active 版本 → 需要一个**不依赖具体版本**的能力探测入口（当前代码里没有 `COMMAND INFO` 的独立函数，`_command_info_present` 是私有 helper）。这是实现层面的一个小缺口。

### D4 探测是否并发 + 超时总预算

- 串行最坏耗时 = Redis(2s) + Business(10s, `business_http.py:18`) + RAG(每次 `COMMAND INFO` 各一次往返 × 3)。
- 是否并发探测、总预算是否设为固定值（例如 3s，超时项判 `down`），需人工定。AC10 依赖此决策。

---

## Caveats / Not Found

- **未运行测试**：本报告为静态源码调查，未执行 `uv run pytest`。基线数字（413 项）引自 spec `agent-guidelines.md:239,314` 的复核记录，非本次实测。
- **未验证运行时状态**：`RAG_ENABLED` 在真实 `.env` 中的取值未知（代码默认 `false`，`config.py:48`）；Vector Set 是否真的可用未探测。
- **未找到**：`tests/` 下 health 测试（确认无）；`tests/` 下 `TestClient` / `conftest.py` / `respx` 使用（确认无）→ 若写 API 层测试需**自建** HTTP 测试脚手架。
- **未找到**：业务后端是否有面向前端的 Agent health 消费方（前端是否调用 `/api/client/agent/health`）—— 未在前端目录调查。
- **不一致已记录**：`docs/spec/openapi.yaml:2887-2913` 的响应 schema（`{code,message,data:string}`）与 Agent 实际返回（`{status,llm_configured}`）不符；且 openapi 声明 `Authorization required` 而 Python 未强制。
- **未找到**：`app.state` 上是否暴露 Business gateway / RAG index（确认**未暴露**，`main.py:199,205-212` 只挂 `store`、`admin_config_service`、`import_service`、`chat_service`）→ health 需要新增暴露或另建轻量客户端。
