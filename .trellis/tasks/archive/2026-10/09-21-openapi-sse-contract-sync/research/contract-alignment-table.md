# OpenAPI ↔ 三端逐项对照表

- **核对日期**：2026-10-14
- **基准**：`main` @ `b71c2ab5`
- **权威来源**：可执行源码 + 测试（`docs/README.md:224`、`cross-layer-thinking-guide.md:44,63`）
- **校验命令**：`npx --yes @redocly/cli@latest lint docs/spec/openapi.yaml`

## 基线对比（同一校验器）

| 版本 | errors | warnings | 错误构成 |
|---|---|---|---|
| 改前（`HEAD:docs/spec/openapi.yaml`） | 101 | 171 | `security-defined` ×69、`spec-components-invalid-map-name` ×30、`no-empty-servers` ×1、其余 struct |
| 改后（本次） | **31** | 171 | `spec-components-invalid-map-name` ×30、`no-empty-servers` ×1（**全部为改前既有、非本任务引入**） |

改前 69 条 `security-defined` + 21 条 path 级 struct 错误由本任务的「补 securitySchemes / 删无效 path 级 `security:`」消解。剩余 31 条为文件既有债务（中文 schema 名与缺 servers），不在本任务范围（见 Out of Scope）。

## 逐项对照

### R1 / R2 — SSE 建模

| 项 | openapi.yaml | 实现证据 | 一致 |
|---|---|---|---|
| admin stream 声明 `text/event-stream` | `:2970` | `AdminAgentController.java:120` `produces = MediaType.TEXT_EVENT_STREAM_VALUE` | ✅ |
| client stream 声明 `text/event-stream` | `:3205` | `ClientAgentController.java:54` 同上 | ✅ |
| 帧格式 `data: <JSON>\n\n` | `:13`（info.description） | `app/api/schemas/sse.py` `serialize_sse`：`f"data: {...}\n\n"` | ✅ |
| `type` 枚举四值 | `:4699` | `sse.py` `MessageType{ANSWER,THINKING,FUNCTION_CALL,STATUS}` | ✅ |
| 无 `type=end`；结束由 `is_end=true` | `:20-21`、`:4683`+`:4734` | `serialize_agent_event`：`AgentEventType.END → Content(), is_end=True` | ✅ |
| `content` 子字段集 8 项 | `:4701-4728` | `sse.py` `Content`：text/node/parent_node/state/message/result/name/arguments | ✅ |
| `meta` 可空、空时不序列化 | `:4729-4733` | `exclude_none=True` + `meta=event.meta or None` | ✅ |
| `timestamp` 毫秒整数 | `:4737-4740` | `int(time.time() * 1000)` | ✅ |
| 响应头 `Cache-Control`/`Connection`/`X-Accel-Buffering` | `:2963`（description） | `create_sse_response` headers | ✅ |

### R3 — stream 请求体

| 项 | openapi.yaml | 实现证据 | 一致 |
|---|---|---|---|
| admin stream `requestBody` = `ChatRequest` | `:2955-2959` | Spring 侧 `Map<String, Object> body`（透传）；下游 Python `ChatRequest` | ✅ |
| client stream `requestBody` = `ChatRequest` | `:3190-3194` | 同上 | ✅ |
| 字段集 `{session_id, content}` + `required` | `:4668-4681` | `app/api/schemas/chat.py:4-6` | ✅ |
| `content` 长度 1..4096 | `:4678-4680` | `Field(..., min_length=1, max_length=4096)` | ✅ |

> 说明：Spring 层用 `Map` 透传、不校验形状；契约记的是 Python 权威 `ChatRequest`。

### R4 — Bearer securityScheme

| 项 | openapi.yaml | 实现证据 | 一致 |
|---|---|---|---|
| `components.securitySchemes.bearerAuth` | `:4659-4665` | `SecurityConfig.java:86-87` role/auth 策略 + shared `Bearer` 拦截器 | ✅ |
| 全局默认 `security: [{bearerAuth: []}]` | `:37-38` | Spring 默认 `authenticated()` | ✅ |
| 21 个公开端点显式 `security: []` | 见下节 | `SecurityConfig.java:75-85` `permitAll()` | ✅ |

公开端点（21）：`/api/client/tags`、`/tags/{tag}/subjects`、`/auth/{register,verify-email,resend-code,login,forgot-password,reset-password,refresh,logout}`、`/subjects`、`/subjects/search`、`/subjects/lexical-search`、`/subjects/season`、`/subjects/schedule`、`/subjects/batch`、`/evidence/batch`、`/evidence/resolve`、`/subjects/{id}`、`/subjects/years`、`/subjects/{id}/episodes`。

对照 `SecurityConfig.java:75-85`：
- `permitAll` GET `/api/client/subjects/**` → openapi 覆盖 `subjects`、`search`、`season`、`schedule`、`{id}`、`years`、`{id}/episodes`（7）
- `permitAll` POST `/subjects/batch`、`/subjects/lexical-search`、`/evidence/batch`、`/evidence/resolve`（4）
- `permitAll` GET `/tags/**` → `tags`、`tags/{tag}/subjects`（2）
- `permitAll` auth 8 条 → 8
- 合计 21 ✅

### R5 — refresh cookie

| 项 | openapi.yaml | 实现证据 | 一致 |
|---|---|---|---|
| refresh 端点 `at_refresh` cookie 入参 | `:494-498` | `AuthCookieProperties.java:15` `name="at_refresh"`、`:19` `path="/api/client/auth"` | ✅ |
| refresh 端点 `Set-Cookie` 响应头 | `:504-507` | `RefreshCookieService.java:36-41` `response.addHeader("Set-Cookie", ...)` | ✅ |
| logout 端点 `at_refresh` cookie 入参 | `:561-565` | 同上 | ✅ |
| logout 端点 `Set-Cookie`（清空） | `:571-574` | `RefreshCookieService.java:50-55` `addHeader("Set-Cookie", "")` + `maxAge(0)` | ✅ |
| login 端点 `Set-Cookie` | `:355-357` | 登录成功写 refresh cookie | ✅ |
| HttpOnly / SameSite=Lax / Secure 可配 | `:356`（description） | `AuthCookieProperties.java:23,27` + `RefreshCookieService.java:38-39` | ✅ |

> **有意差异（非漂移）**：openapi 未把 login 的 `Set-Cookie` 挂在 refresh 同一 header 名下的多值语义上；单个 header 声明即可表达。

### R6 — X-Request-ID

| 项 | openapi.yaml | 实现证据 | 一致 |
|---|---|---|---|
| 16 个 `/api/**/agent/**` 与 admin 端点声明请求头 | `:2624` 起 16 处 | `observability.py:103,107`（Agent）、`RequestIdFilter.java:19,24`（Business） | ✅ |
| 两个 stream 端点声明响应头 | `:2965-2968`、`:3200-3203` | `observability.py:107` `response.headers[HEADER_X_REQUEST_ID] = trace_id` | ✅ |
| 字符集 `[A-Za-z0-9._-]{1,128}`、非法/缺失生成 UUID | `:2626`（description） | `RequestIdFilter.java:21` `VALID_ID` + `observability.py:93-96` | ✅ |

> **已知差异（已登记）**：非 agent 的其余 52 个端点未逐一声明 `X-Request-ID`。`RequestIdFilter` 是全局 `@Order(HIGHEST_PRECEDENCE)` 过滤器，实际对所有 `/api/**` 生效——openapi 只在本任务范围内（agent + auth）声明。属已知债务，见下节。

### R7 — 已知债务落点

| 项 | 落点 |
|---|---|
| `end` 建模歧义 | `openapi.yaml:25-26`（info.description 第 1 条） |
| 删除端点路径分层不一致 | `:27-29`（第 2 条） |
| Spring 逐行转发空行差异 | `:30-32`（第 3 条） |
| stream 错误响应缺失 | `:33-35`（第 4 条） |
| `X-Request-ID` 未覆盖非 agent 端点 | 本表 R6「已知差异」 |
| 31 条 lint 错误（中文 schema 名 / 缺 servers） | 本表「基线对比」+ `openapi.yaml` Out of Scope 记录 |

## 漂移项

**0 个**（本任务范围内 R1–R6 全部一致或已登记为债务）。

## 未纳入本任务的既有债务（Out of Scope，仅登记）

1. `spec-components-invalid-map-name` ×30：`components.schemas` 使用中文键名（如 `标签信息 VO`），不符合 `^[a-zA-Z0-9\.\-_]+$`。改键名需同步 8 处 `$ref`，属独立工程。
2. `no-empty-servers` ×1：无 `servers` 段。
3. 52 个非 agent 端点未声明 `X-Request-ID`。
4. 全文 68 路径的 `{code,message,data}` 内联响应未抽 `components.schemas`。
5. `docs/README.md:224` 记录的「openapi 与 Controller 一致性无自动校验」——本任务选择 AC-A（人工对照表），不引入校验脚本。
