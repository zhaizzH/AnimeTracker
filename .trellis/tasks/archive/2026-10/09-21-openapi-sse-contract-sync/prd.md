# OpenAPI/SSE 契约同步

## Goal

把 `docs/spec/openapi.yaml` 与三端（Spring Controller / Python Router / shared TS）的真实 SSE、鉴权、cookie、追踪头契约对齐；未同步项显式登记为已知债务。

## 重设计说明（2026-09-29 复核）

原 PRD 为模板占位（`Requirements: TBD`），未撰写。研究文档 `research/openapi-sse-facts.md` 已完备（252 行，含全部 file:line 证据）。本次据研究结论落笔。

**方向判定（研究 §建议 Requirements 已论证）**：以**改契约文档为主，代码对齐为辅**。依据 `cross-layer-thinking-guide.md:44,63` 与 `docs/README.md:224`——openapi.yaml 是手工维护的**描述性契约**，权威来源是可执行源码+测试。**不为迁就文档改动任何运行时行为。**

## Background（研究已核实，摘要）

- `openapi.yaml` **5725 行**，`openapi: "3.0.1"`（无 `itemSchema`，SSE 只能以单帧 schema + description 建模）。
- `components` **只有 `schemas:`**，无 `securitySchemes`。全文无 `security:`、无 `text/event-stream`、无 `X-Request-ID`、无 `Cookie`/`Content-Type` 声明。
- `Authorization` header 是裸声明 `schema: {}`（如 `:2739-2744`、`:2918-2923`），未表达 Bearer 语义。
- 两处 stream 请求体为伪 schema `{key:{properties:{}}}`（`:2745-2754`、`:2924-2933`），真实为 `ChatRequest{session_id: str, content: str(1..4096)}`（`app/api/schemas/chat.py:4-6`）。
- 两处 stream 响应仅 `"200": description: "No Content"`，无 `content`。
- **无任何 openapi 漂移校验测试/CI 步骤**（研究 §7）。

## Requirements

- **R1** 为两个 stream 端点（`POST /api/admin/agent/chat/stream`、`POST /api/client/agent/stream`）补 `text/event-stream` 响应建模，如实描述帧格式（单 `data:` 行、`\n\n` 分帧、类型在 JSON 内）。
- **R2** 补 SSE 事件联合 schema：五类事件 + `Content` 字段集（text/node/parent_node/state/message/result/name/arguments）+ `is_end`/`timestamp`/`meta`；**显式记录 `end` 以 `is_end=true` 表达**（`type` 枚举不含 `end`，事实见 `app/api/sse.py:10-11`）。
- **R3** 用真实 `ChatRequest` 替换两份 `{key:{}}` 占位请求体（`session_id` + `content`，含 `min_length=1`/`max_length=4096`，标 `required`）。
- **R4** 新增 `components.securitySchemes`（`type: http`, `scheme: bearer`, `bearerFormat: JWT`）并挂到受保护端点。
- **R5** 补 refresh cookie：`in: cookie` 的 `at_refresh` 入参 + `Set-Cookie` 响应头（HttpOnly、Path=/api/client/auth、SameSite=Lax、Secure 可配）。事实源 `RefreshCookieService.java:26-32`。
- **R6** 补 `X-Request-ID` 请求头与响应头声明（实现 `observability.py:103,107`、`RequestIdFilter.java:19,24`）。
- **R7** 把「三端已对照、仍未同步项」登记为**已知债务**，至少覆盖研究 §8 的第 7/8/9/10 条（`end` 建模歧义、删除端点路径分层不一致、Spring 逐行转发的空行差异、stream 错误响应缺失）。落点：`openapi.yaml` 的 `info.description` 或 spec guide（**二选一，需先决定**）。
- **R8** 不改动任何运行时源码（Python/Java/TS），除非发现与权威源码冲突的文档错误。

## Acceptance Criteria

- [ ] **AC1** 两个 stream 端点声明了 `text/event-stream` 的 `content` 与单帧 schema，并在 description 中说明分帧与 `is_end` 语义。
- [ ] **AC2** SSE schema 的 `type` 枚举 ⊇ `{answer, thinking, function_call, status}`，且存在 `is_end`/`timestamp` 字段；`content` 子字段集与 `Content` 一致。
- [ ] **AC3** 两处 stream `requestBody` 属性集 == `{"session_id","content"}`，含长度约束与 `required`。
- [ ] **AC4** `components.securitySchemes` 含 bearer 定义；受保护端点引用之。
- [ ] **AC5** refresh/logout 端点声明 `at_refresh` cookie 入参；`/login`、`/refresh` 声明 `Set-Cookie` 响应头。
- [ ] **AC6** 两个 stream 端点声明 `X-Request-ID` 请求头与响应头。
- [ ] **AC7** 已知债务（研究 §8 第 7/8/9/10 条）已落在 `openapi.yaml` 或 spec，位置明确可检索。
- [ ] **AC8** 逐项对照表：对 R1–R6 每项给出 `openapi.yaml:<line>` ↔ 实现 `<file>:<line>` + 核对日期，落 `research/` 或 spec；漂移项 0 个或全部登记为债务。
- [ ] **AC9** openapi.yaml 仍可被标准 OpenAPI 3.0 校验器解析（**先实测**：文件含中文 schema 名与 `properties: {}`，若不可解析则收缩为「YAML 可解析」并登记）。
- [ ] **AC10** `git diff` 仅含 `docs/spec/openapi.yaml`（及可选的 spec/research md），`backend/`、`frontend/` 零改动。
- [ ] **AC11** `uv run pytest` 与 `mvn -B test` 保持通过（本任务不改实现，应 trivially green）。

## Out of Scope

- 修改任何运行时源码（`sse.py`/`chat.py`/`deps.py`、Java Controller、`useAgentChat.ts`/`sse.ts`/`api/agent.ts`）。
- 引入 springdoc / 自动生成 OpenAPI。
- 把全文 68 路径的 `{code,message,data}` 内联响应重构为 `components.schemas` 复用（独立大工程）。
- 穷举 openapi.yaml 其余 66 路径的字段级漂移（本研究只覆盖 SSE/鉴权/cookie/追踪头范围）。
- 修复 `tests/jobs/importer/test_contract_drift.py` 记录的数据层漂移（与 openapi 无关）。
- 更改 `at_refresh` cookie 属性、鉴权协议或路径前缀。

## Notes

- 研究全文：`.trellis/tasks/09-21-openapi-sse-contract-sync/research/openapi-sse-facts.md`（含 §8 十一条债务、§建议 AC 的 AC-A/AC-B 二选一、§需人工决策的 5 点）。
- **待决策（阻塞 implement.md）**：
  1. SSE 建模深度：单帧 schema + description（推荐）vs 仅 `{}` 占位 vs 升级 3.1。
  2. 是否引入轻量校验脚本（AC-B）并接入 CI——还是仅人工对照表（AC-A，推荐）。
  3. 已知债务落点：`openapi.yaml` 内联 vs spec guide。
  4. 契约基准层：openapi 记 Spring 对外路径（现状），确认是否有意。
- 本任务为**纯文档**任务，风险低；建议先决策上列 4 点，再写 `implement.md`。
