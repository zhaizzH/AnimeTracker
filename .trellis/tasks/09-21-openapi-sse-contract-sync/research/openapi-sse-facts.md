# Research: OpenAPI/SSE 契约同步 — 事实清单

- **Query**: docs/spec/openapi.yaml 缺 SSE text/event-stream 与事件联合、bearer securityScheme、refresh cookie、X-Request-ID；stream 请求体误建模为占位。逐项对齐三端并记录已知债务。
- **Scope**: internal（仓库内三端契约载体 + spec）
- **Date**: 2026-09-21

---

## 1. openapi.yaml 现状

| 项目 | 现状 | 证据 |
|---|---|---|
| 文件 | `docs/spec/openapi.yaml`，**5711 行** | `wc -l` |
| OpenAPI 版本 | `openapi: "3.0.1"`（不是 3.1，因此 SSE 无法用 `itemSchema` 原生建模） | `docs/spec/openapi.yaml:1` |
| `components` 子键 | **只有 `schemas:` 一个**，无 `securitySchemes` / `responses` / `parameters` | `docs/spec/openapi.yaml:4359-4360` |
| `securitySchemes` | **完全不存在**（`grep -c -i securityscheme` = 0；`grep -n "security:"` 无匹配，exit 1） | 全文件 |
| 全局/端点 `security:` | **完全不存在** | 全文件 |
| `text/event-stream` | **不存在**。仅 4 处 summary/description 提到「SSE 流式透传」中文描述 | `docs/spec/openapi.yaml:2737-2738`（admin）、`2916-2917`（client） |
| `X-Request-ID` 声明 | **不存在**（`grep -n "X-Request-ID"` 无匹配，exit 1） | 全文件 |
| `Content-Type` / `Cookie` header 声明 | **不存在**（grep exit 1） | 全文件 |
| Authorization header 声明 | 存在，但为裸声明：`name: "Authorization" / in: "header" / required: true / schema: {}`（**schema 为空对象，未声明 Bearer scheme**） | stream: `2739-2744`（admin）、`2918-2923`（client）；全文件大量重复 |

### stream 请求体「占位」确切形态

两个 stream 端点的 `requestBody` 都是同一个伪 schema——一个属性名为 `key`、且 `properties: {}` 为空的嵌套对象：

```yaml
# docs/spec/openapi.yaml:2745-2754 (POST /api/admin/agent/chat/stream)
      requestBody:
        content:
          application/json:
            schema:
              type: "object"
              properties:
                key:
                  type: "object"
                  properties: {}
              description: ""
      responses:
        "200":
          description: "No Content"
```

同样形态见 `docs/spec/openapi.yaml:2924-2936`（POST `/api/client/agent/stream`）。响应只声明 `"200": description: "No Content"`，无 `content`、无 SSE、无错误响应。

注意请求体上还**缺 `required: true`**，且 `application/json` 未标注 charset。

### stream 路径清单（8 条 agent 相关）
`/api/admin/agent/chat/stream` :2735、`/api/admin/agent/chat/sessions` :2758、`.../sessions/{sessionId}/history` :2821、`.../sessions/{sessionId}/remove` :2854、`/api/client/agent/stream` :2914、`/api/client/agent/sessions` :2937、`.../sessions/{sessionId}/history` :3000、`.../sessions/{sessionId}/remove` :3033

### auth 路径现状
`/api/client/auth/login` :291、`/refresh` :441、`/logout` :495 均只声明 `200` JSON 响应；**未声明 `Set-Cookie` / `at_refresh` 响应头**，未声明 refresh/logout 的 Cookie 入参。`/refresh` 响应体正确回 `data.token` + `data.user`，与 LoginVO 一致（`docs/spec/openapi.yaml:445-494`）。

---

## 2. Agent 侧 SSE 真实契约

### 事件联合（领域层，权威来源）
`backend/agent/app/chat/events.py:6-11`：
```python
class AgentEventType(str, Enum):
    ANSWER = "answer"
    THINKING = "thinking"
    FUNCTION_CALL = "function_call"
    STATUS = "status"
    END = "end"
```
`AgentEvent` 为 frozen dataclass，字段（`backend/agent/app/chat/events.py:14-25`）：
`type: AgentEventType`、`text`、`state`、`message`、`result`、`name`、`node`、`parent_node`、`arguments`（均 `str | None = None`）、`meta: dict[str, Any] = field(default_factory=dict)`。

### wire schema
`backend/agent/app/api/schemas/sse.py`：

- `Content`（:8-16）：`text, node, parent_node, state, message, result, name, arguments` 全为 `str | None`。
- `MessageType`（:19-23）：`ANSWER/THINKING/FUNCTION_CALL/STATUS` 四值 —— **`Content`/`MessageType` 无 `end` 枚举值**。
- `AssistantResponse`（:26-31）：`content: Content`（default_factory）、`type: MessageType`（默认 `ANSWER`）、`meta: dict | None = None`、`is_end: bool = False`、`timestamp: int`（`int(time.time()*1000)`）。
- `serialize_sse`（:34-37）：
  ```python
  f"data: {json.dumps(payload.model_dump(mode='json', exclude_none=True), ensure_ascii=False)}\n\n"
  ```

**`end` 事件语义（关键）**：`end` 不进入 `MessageType`；在 `backend/agent/app/api/sse.py:10-11` 中 `AgentEventType.END` 被映射为 `AssistantResponse(content=Content(), is_end=True)` —— 即 `type` 仍为默认 `"answer"`，靠 `is_end=true` 表达结束。`is_end=true` 的帧经 `exclude_none=True` 后只含 `content:{}`、`type:"answer"`、`is_end:true`、`timestamp`（`meta` 为 None 被剔除）。

### 分帧格式
- 每帧**只有 `data:` 行**，**不使用 `event:` 行、不使用 `id:`、不使用 `retry:`**；类型信息在 JSON 内部（`type` 字段）。
- 帧分隔符为 `\n\n`（`schemas/sse.py:36` 结尾 `\n\n`）。
- `Content` 内的 `None` 字段被 `exclude_none=True` 剔除 → 每帧字段集随事件类型变化（前端因此大量使用可选字段）。
- 响应头见 `backend/agent/app/api/sse.py:33-37`：`media_type="text/event-stream"`、`Cache-Control: no-cache`、`Connection: keep-alive`、`X-Accel-Buffering: no`。

### Spring 代理的分帧改写（跨层事实）
`ClientAgentController.java:62` 与 `AdminAgentController.java:124` 逐行转发时写 `line + "\n"`。上游行 `data: {...}\n\n` 被按行读出后，空行在转发时被 drop（若按行过滤空串），或保留为 `"\n"` —— 与 Agent 原始字节不完全一致。前端 `streamSse` 以 `\n` 分行后 `if (!line) continue;`，因此对空行不敏感（见第 6 节）。

---

## 3. Agent 侧 stream 端点

`backend/agent/app/api/chat.py:29` 工厂 `create_chat_router(*, prefix, auth_dep, include_health=False)`。

| 端点 | 注册前缀 | 鉴权依赖 | 证据 |
|---|---|---|---|
| `POST {prefix}/stream` | client: `/api/client/agent`；admin: `/api/admin/agent/chat` | client → `verify_token`；admin → `require_admin` | `backend/agent/main.py:230-238`（`:232` auth_dep=verify_token，`:237` auth_dep=require_admin）；`chat.py:32-48` |
| `GET {prefix}/sessions` | 同上 | 同上 | `chat.py:50-61` |
| `POST {prefix}/sessions` | 同上 | 同上 | `chat.py:63-71` |
| `GET {prefix}/sessions/{session_id}/history` | 同上 | 同上 | `chat.py:73-88` |
| `POST {prefix}/sessions/{session_id}`（删除） | 同上 | 同上 | `chat.py:90-97` |
| `GET /health`（仅 include_health） |  | 无鉴权 | `chat.py:99-107` |

注意：删除端点的 Python 路由是 `POST /sessions/{session_id}`，而 openapi 记为 `/sessions/{sessionId}/remove`（`docs/spec/openapi.yaml:3033`）—— Spring 层对外路径为 `/remove`，Python 层为 `/{id}`，**两层路径本就不同**（Spring 改写），需要人工确认以哪层为契约基准。

### 真实请求体模型
`backend/agent/app/api/schemas/chat.py:4-6`：
```python
class ChatRequest(BaseModel):
    session_id: str
    content: str = Field(..., min_length=1, max_length=4096)
```
→ 与 openapi 的 `{key: {}}` 占位**完全不符**：缺 `session_id`/`content`、多出 `key`、缺 `required` 与长度约束。

`chat.py:39-41` 还有不在 openapi 中的行为：`session_id` 不属于当前用户 → `404 {"detail":"会话不存在或无权限"}`。

---

## 4. 鉴权契约

### Agent 本地验签
`backend/agent/app/api/deps.py:12-33`：
- 入参 `authorization: str | None = Header(None)`（**HTTP header `Authorization`**，非 cookie）。
- 必须以 `"Bearer "` 开头，否则 `HTTPException(401, "认证失败")`（:14-15）。
- HS256 本地验签 `jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])`（:19）；`InvalidTokenError` → 401 `"认证失败，请重新登录"`（:20-21）。
- claim 取 `userId`，缺失 → 401（:23-25）；`role` 缺省 `USER`，非 `USER`/`ADMIN` 归一为 `USER`（:27-33）。

### admin 端点
`backend/agent/app/api/admin_config.py:10-15`：`require_admin(authorization)` 先调 `verify_token`，再判 `user.role != "ADMIN"` → 拒绝（纵深防御）。用于 `admin_config.router` 各端点（:22,27,35,43,51,56）与 `import_api.router`（`backend/agent/app/api/import_api.py:7`，prefix `/api/admin/agent/import`）。

### Business 侧 refresh cookie
- 名称/属性事实来源：`backend/business/app/src/main/resources/application.yml:69-74` → `at.auth.refresh-cookie`: `name: at_refresh`、`path: /api/client/auth`、`secure: ${AT_AUTH_COOKIE_SECURE:true}`、`same-site: Lax`。
- 绑定类默认值一致：`AuthCookieProperties.java:13-19`（`name="at_refresh"`、`path="/api/client/auth"`、`secure=true`、`sameSite="Lax"`）。
- 写 Cookie：`RefreshCookieService.java:26-32`（`httpOnly(true)` + `.secure()` + `.sameSite()` + `.path()` + `.maxAge()`）；清理：:40-46（`maxAge(Duration.ZERO)` 同名同属性）。**未设置 Domain**。
- access token 传递：由 shared request interceptor 加 `Authorization: Bearer`（spec `.trellis/spec/guides/cross-layer-thinking-guide.md:49`）；Agent 收到的是 Spring 透传的同一 header（`ClientAgentController.java:49`、`AdminAgentController.java:115` 的 `@RequestHeader("Authorization")`），不是 cookie。

### 与 spec「不可破坏的系统约束」核对
`.trellis/spec/backend/index.md:27`：「Access Token 只保存在前端内存；刷新凭据只使用 `at_refresh` HttpOnly Cookie」—— 与上述实现**一致**。`:29`「Java API 成功/失败统一为 `{code,message,data}`；**SSE 除外**」—— 与 SSE 裸帧一致。

---

## 5. X-Request-ID / 追踪头

- 头名常量：`HEADER_X_REQUEST_ID = "X-Request-ID"` —— `backend/agent/app/shared/observability.py:25`。
- middleware：`trace_context_middleware` —— `observability.py:98-110`：**读取**请求头 `request.headers.get(HEADER_X_REQUEST_ID)`（:103），经 `sanitize_trace_id` 校验或生成 UUID（:91-95，正则 `^[A-Za-z0-9._-]{1,128}$`），**回写响应头** `response.headers[HEADER_X_REQUEST_ID] = trace_id`（:107），finally 中清理 ContextVar（:109-110）。
- Business 对端：`RequestIdFilter.java:19,24`（同一头语义、接受或生成 UUID、写 MDC 与响应头）；常量 `TraceConstants.java:11`；CORS 白名单含该头 `CorsConfig.java:32`。
- 前端共享 `streamSse` **不发送** X-Request-ID（`frontend/packages/shared/src/sse.ts:9-14` 只加 `Content-Type` + `Authorization`）。

---

## 6. 三端载体路径

`.trellis/spec/backend/index.md:9` 原文划定：「涉及接口字段或路径时，同时核对 `docs/spec/openapi.yaml`、Spring Controller、Python Router 与 `frontend/packages/shared/src`」。据此三端（实为四类载体）：

| 端 | 契约载体 | 路径 |
|---|---|---|
| 文档 | OpenAPI 3.0.1 手工维护 | `docs/spec/openapi.yaml` |
| Business | Spring Controllers | `backend/business/agent/src/main/java/top/zhaizz/agent/controller/ClientAgentController.java`、`AdminAgentController.java`；路径常量 `.../agent/constant/AgentApiPaths.java`（`ADMIN_CHAT_STREAM:16`、`CLIENT_STREAM:24`）；追踪 `app/.../filter/RequestIdFilter.java`；cookie `client/.../service/RefreshCookieService.java` |
| Agent | FastAPI Routers + wire schema | `backend/agent/app/api/chat.py`、`sse.py`、`schemas/sse.py`、`schemas/chat.py`、`deps.py`、`admin_config.py`；装配 `backend/agent/main.py:230-240`；领域事件 `app/chat/events.py` |
| Frontend | shared types + API + SSE 消费 | `frontend/packages/shared/src/api/agent.ts`、`api/admin/agent.ts`、`sse.ts`、`hooks/useAgentChat.ts`、`types/index.ts` |

SSE wire 契约的直接消费者：`frontend/packages/shared/src/hooks/useAgentChat.ts:9-13`（`SsePayload{type?,is_end?,content?{text?,name?,state?,message?}}`）、:118-128（状态机）、`sse.ts:24-29`（按 `\n` 分行、剥离 `data:` 前缀、跳过空行）。`api/agent.ts:8` 的 `streamBody` 组装 `{content, session_id}`，注释明确「字段与 Python ChatRequest(content/session_id) 对齐」。

---

## 7. 既有测试：是否存在 OpenAPI 契约漂移测试

**结论：不存在任何校验 openapi.yaml 与实现一致性的测试。**

- `tests/jobs/importer/test_contract_drift.py` **路径不存在**；实际文件在 `backend/agent/tests/jobs/importer/test_contract_drift.py`，其内容是 importer/normalize/repository/indexer 与 **db-schema** 之间的漂移（文件头 :6-12 列举 eps/volumes、credit_type、AIRING、stale replace-set、profile hash），**与 openapi.yaml 无关**。该文件是「故意失败的记录型测试」。
- 全仓库 `openapi|swagger|spectral|swagger-cli` 的匹配仅出现在 md 文档、task.json 和 openapi.yaml 自身，**无任何校验脚本**。
- CI `.github/workflows/ci.yml` 三个 job：frontend typecheck（:20）、`mvn -B test`（:32）、`uv run pytest`（:42），**无 openapi 校验步骤**。
- 前端 `frontend/packages/shared/package.json:7-10` 仅有 `test`/`typecheck`；根 `frontend/package.json:5-11` 无契约校验脚本。
- 文档层面已承认：`docs/README.md:224`「`spec/openapi.yaml` 为手工维护，与 Controller 的一致性未经自动校验」；`.trellis/spec/guides/index.md:34`「OpenAPI 当前未被 CI 自动校验」。
- 已存在的 SSE 相关测试（可复用作 AC 证据）：`backend/business/agent/src/test/java/top/zhaizz/agent/controller/ClientAgentControllerTest.java:55`（`verify(response).setContentType("text/event-stream")`）、`AgentConfigTest.java:59,84`（`/stream` 透传与无读超时 + X-Request-ID）。

---

## 8. 已知债务候选

1. **SSE 无 content type 建模**：两个 stream 端点 `responses.200` 只有 `description: "No Content"`，缺 `content: text/event-stream` 与 schema（`docs/spec/openapi.yaml:2755-2757`、`:2934-2936`）。
2. **SSE 事件联合缺失**：`answer/thinking/function_call/status/end` 五类事件与 `content` 子字段（text/node/parent_node/state/message/result/name/arguments）、`is_end`、`timestamp`、`meta` 全部未建模。
3. **stream 请求体占位失实**：`{key:{}}` vs 真实 `ChatRequest{session_id: str, content: str(1..4096)}`（`docs/spec/openapi.yaml:2745-2754`、`:2924-2933` vs `backend/agent/app/api/schemas/chat.py:4-6`）。
4. **缺 bearer securityScheme**：`components` 只有 `schemas`；所有 `Authorization` header 为 `schema: {}` 裸声明，无法表达 Bearer 语义（`:4359-4360` 及全文）。
5. **缺 `at_refresh` cookie 建模**：`in: cookie` 参数（refresh/logout 入参）与 `Set-Cookie` 响应头均未声明（`:441-515`）；实现见 `RefreshCookieService.java:26-32`。
6. **缺 X-Request-ID**：请求头与响应头均未声明，而三端实现均读写该头（`observability.py:25,103,107`、`RequestIdFilter.java:11`、`CorsConfig.java:32`）；共享的 `{code,message,data}` 包装也未在 openapi 里以 `components` 复用（全文内联展开）。
7. **`end` 事件的建模歧义（候选债务，也可能是可接受简化）**：Agent 侧 `type` 枚举无 `end`，结束靠 `is_end=true`；而任务描述、`.trellis/spec/backend/agent-guidelines.md:161` 与 `cross-layer-thinking-guide.md:61` 都表述为 `answer|thinking|function_call|status|end` 联合。文档与 wire 事实需要显式说明「end 表现为 is_end=true 而非 type=end」，否则契约本身会误导实现者。
8. **删除端点路径分层不一致**：Python `POST /sessions/{session_id}`（`chat.py:90`）vs openapi/Spring `/sessions/{sessionId}/remove`（`:3033`、Spring 对外路径）。属跨层事实，需在契约中注明以 Spring 对外路径为准。
9. **分帧字节不完全一致**：Spring 逐行 `line + "\n"` 转发会改变空行处理（`ClientAgentController.java:62`），上游 `\n\n` 分帧在代理后不保证原样；前端因跳过空行而不受影响（`sse.ts:27`）。属已知的隐性契约。
10. **错误响应缺失**：stream 端点未声明 401/403/404（`chat.py:41` 会返 404），全文件对 agent 端点普遍只写 200。
11. **openapi 无自动校验**：CI 无任何步骤证明文档与三端一致（`.github/workflows/ci.yml`、`docs/README.md:224`）。

---

## 建议 Requirements（供 prd.md）

**方向判定：以「改契约文档」为主，代码对齐为辅。**
依据：`.trellis/spec/guides/cross-layer-thinking-guide.md:44` 明确「当前 OpenAPI 是手工维护，CI 未自动证明它与三端一致……必须把 OpenAPI、Java/Python 实现和 shared 类型逐项对照，并**记录未同步项为已知债务**」；`:63` 进一步说明「[OpenAPI 缺陷] 这是契约债务，**本轮只在 spec 中记录**，改动 API 时必须同步修复」。`docs/README.md:191` 也确认 openapi 未集成 springdoc，为手工维护的描述性契约。故 openapi.yaml 是**描述性文档、非权威来源**；权威来源是「可执行源码 + 测试」（`cross-layer-thinking-guide.md:26-30`）。本任务不应为迁就文档而改 API 行为。

- R1 在 openapi.yaml 为两个 stream 端点补 `text/event-stream` 响应建模，并如实描述帧格式（`data:` 单行、空行分帧、JSON 内含 type）。
- R2 补 SSE 事件联合 schema（五类事件 + content 字段集 + is_end/timestamp/meta），并显式记录 `end` 以 `is_end=true` 表达的语义。
- R3 用真实 `ChatRequest`（session_id/content，含长度约束）替换两份 `{key:{}}` 占位请求体。
- R4 新增 `components.securitySchemes`（`type: http`, `scheme: bearer`, `bearerFormat: JWT`）并挂到受保护端点。
- R5 补 refresh cookie：`in: cookie` 的 `at_refresh` 入参 + `Set-Cookie` 响应头（HttpOnly、Path=/api/client/auth、SameSite=Lax、Secure 可配）。
- R6 补 `X-Request-ID` 请求头与响应头。
- R7 将「三端已对照、仍未同步项」作为**已知债务**写入文档（推荐落在 openapi.yaml `info.description` 或 spec 的 cross-layer guide），至少覆盖第 8 节 7/8/9/10 条。
- R8 不改动任何运行时行为（Python/Java/TS 源码），除非发现与权威源码冲突的文档错误；本任务默认纯文档 + 可选校验脚本。

## 建议 Acceptance Criteria（可验证）

因无既有漂移测试，需**新增**校验手段。二选一（推荐 A）：

- **AC-A（人工核对，零新增依赖，推荐）**：在 `research/` 或 spec 记录一份「逐项对照表」，对第 1/2/3/4/5 节的每个字段给出 `openapi.yaml:<line>` ↔ 实现 `<file>:<line>`，并附验证命令与核对日期；要求漂移项 0 个或全部登记进已知债务。
- **AC-B（新增轻量校验脚本，需人工决策）**：新增 `python backend/tools/check_openapi.py`（或 pytest）断言：
  1. openapi 中两个 stream 端点存在 `text/event-stream` 的 `content`；
  2. stream `requestBody` 属性集 == `ChatRequest.model_fields`（`session_id`,`content`）；
  3. `components.securitySchemes` 含 bearer 定义；
  4. 两个 stream 端点 200 响应声明 `X-Request-ID` 响应头；
  5. SSE schema 的 `type` 枚举 ⊇ `{answer,thinking,function_call,status}`，且存在 `is_end`。
  并接入 CI（`.github/workflows/ci.yml`）或明确登记为「仅本地运行」。
- **AC（文档可行性）**：openapi.yaml 通过任一 OpenAPI 3.0 校验器（如 `npx @redocly/cli lint` 或 swagger-ui Docker）解析无错误——因该文件为手写、含中文 schema 名，需先实测能否解析，否则收缩为「YAML 可解析」。
- **AC（不回归）**：`uv run pytest` 与 `mvn -B test` 保持通过（本任务不改实现，应为 trivially green），并确认 `ClientAgentControllerTest`、`useAgentChat.enabled.test.tsx` 未受影响。
- **AC（范围）**：不为对齐文档修改任何 Controller/Router/hook 行为；若必须改，另开任务。

## 需人工决策的点

1. **SSE 在 OpenAPI 3.0 建模到多深？** 3.0.1 无 `itemSchema`/stream 原生支持，只能把 `text/event-stream` 的 schema 描述为「单帧 JSON 对象」并加文字说明；过度建模（试图表达 `\n\n` 分帧、data: 前缀）会失真。选项：(a) 单帧 schema + description 说明分帧（推荐）；(b) 仅 `content: text/event-stream: {}` 占位 + 文字；(c) 升级到 OpenAPI 3.1 用 `itemSchema`（成本高，需确认工具链）。
2. **`end` 事件如何表达**：wire 事实是 `type:"answer"` + `is_end:true`，而 spec 文字与任务描述都写五值联合。是「文档按 wire 事实描述」还是「把 type 也允许 end」（后者需改实现，超出纯文档范围）？
3. **是否值得引入校验脚本（AC-B）**：手工维护 + 无 springdoc，脚本收益长期确定但引入新工具与 CI 步骤；需决定是否纳入本任务或另开。
4. **契约以哪层路径为基准**：Python `/sessions/{id}` 与 Spring 对外 `/sessions/{sessionId}/remove` 不一致；openapi 目前记 Spring 层，需确认这是否是有意设计（浏览器只访问 `/api/**`，Spring 代理）。
5. **已知债务写在何处**：openapi.yaml 内联 description、论文式独立 md、还是 spec guide。三者位置不同，长期可维护性不同。

## 不在本任务范围内

- 修改任何运行时源码（Python `sse.py`/`chat.py`/`deps.py`、Java Controller、TS `useAgentChat.ts`/`sse.ts`/`api/agent.ts`）。
- 引入 springdoc / 自动生成 OpenAPI（`docs/README.md:191` 明确未集成）。
- 把现有 `{code,message,data}` 内联响应重构为 `components.schemas` 复用（全文 68 路径规模，属独立大工程）。
- 修复 `backend/agent/tests/jobs/importer/test_contract_drift.py` 记录的数据层漂移（与 openapi 无关）。
- 更改 `at_refresh` cookie 属性、鉴权协议或路径前缀。

---

## Caveats / Not Found

- 未运行任何 lint/校验工具实测 openapi.yaml 是否可被标准校验器解析（含中文 schema 名与 `properties: {}` 空对象）；AC 中该条需先实测。
- 未逐一穷举 openapi.yaml 其余 66 个路径的其他字段级漂移；本报告只覆盖任务指定的 SSE/鉴权/cookie/追踪头范围。
- Spring 逐行转发的空行处理未能从代码静态确定（`line` 是否可能为空串取决于 `agentService.stream` 的上游分行实现，未展开）。
- `verify_token` 的 `username=""` 由 Agent 本地置空（`deps.py:30`），用户信息依赖 Business 回查。
