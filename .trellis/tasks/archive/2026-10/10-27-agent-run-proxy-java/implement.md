# 执行计划：Java 代理 run 三路由

> 关联 [prd.md](./prd.md) 与上游交接 [handoff.md](../10-22-fix-agent-stream-disconnect/handoff.md) §3。
> 每一步先写红测试再实现；不引入 MockMvc / Spring 上下文。

## 步骤 0：基线（已完成）

- `mvn -B -o -pl agent -am test` → BUILD SUCCESS（agent 模块 12 tests）。
- `backend/agent` 全量 854 passed（提交 `05f6c43a` 之后）。

## 步骤 1：`streamGet` + GET 无 body（TDD）

- [x] `AgentServiceImplTest`（新建，`MockRestServiceServer` 绑普通 RestTemplate 不行——SSE 客户端是内部私有
      `getStreamRestTemplate()`，故用 JDK `HttpServer` 起本地端点，参照 `AgentConfigTest`）：
  - `GET /runs/r1/stream?after=0` 收到的是 GET、query 为 `after=0`、无请求体、无 JSON Content-Type。
  - 上游 409 → `BizException` code 409，`data` 含 `active_run_id`。
- [x] `AgentService` 增加 `streamGet(path, query, authorization, lineConsumer)`；`forwardStream` 按 method 分支
      （GET 不设 Content-Type、不写 body；query 由 caller 作为独立参数拼 URL）。

## 步骤 2：409 映射（TDD）

- [x] `forward` / `forwardStream` 的 `catch (HttpStatusCodeException)`：409 → `BizException(CONFLICT, msg, detail)`。
- [x] `detail` 取自 `objectMapper.readValue(e.getResponseBodyAsString(), Map.class)` 的 `detail` 键；
      非 JSON / 缺 detail → data null。message 用固定中文，不拼接上游原文。
- [x] 用例：`exchange` 路径 409 带 detail / 409 无 detail / 404 仍 NOT_FOUND。

## 步骤 3：Controller 六路由（TDD）

- [x] `AgentApiPaths` 加 `CLIENT_RUNS` / `ADMIN_RUNS`。
- [x] `ClientAgentController`：`GET /runs/{runId}/stream`、`GET /sessions/{sessionId}/run`、`POST /runs/{runId}/stop`。
- [x] `AdminAgentController`：同三路由，前缀 `/chat`。
- [x] 两个 Controller 测试各补：GET stream 的 path+after+逐行写回、session run 的 exchange path+method、stop 的 path+method；
      GET stream 上游抛错时 `verify(response, never()).getWriter()`。
- [x] SSE 写出行逻辑与既有 `stream` 重复 → 抽一个私有方法/共用辅助，避免复制第三份。

## 步骤 4：契约与 spec 回写

- [x] `docs/spec/openapi.yaml`：6 个 operation + 必要 schema（复用 `SSEFrame`；新增 run 状态/停止/409 响应的引用，避免孤儿 schema）。
- [x] `backend/agent/tests/contracts/`：补「Java 对外 run 路由已收录」断言（6 个 operation 存在、GET stream 声明 text/event-stream、
      after 为 query 参数、stop/session-run 有 200、/stream 有 409 响应声明）。
- [x] `contract-tests.md`：过渡说明改为已收录，并写明 Java 409 是 `{code,message,data}` 信封、detail 在 data。
- [x] `java-modules-agent.md`：补 run 代理与 409 结构化透传契约。

## 步骤 5：收尾

实测（2026-10-27）：`mvn -B -o clean test` BUILD SUCCESS（全 reactor **125** tests，agent 26）；`backend/agent` 全量 **862** passed；契约子集 **154** passed。

> 提交 `c10d0ed9` 的信息里写成「152 tests」是错的（把契约子集 154 与 Java 总数混了）；正确值是 125。

- [x] `mvn -B clean test`（全 reactor，交付前门禁）。
- [x] `pytest backend/agent/tests -q` 全绿。
- [x] `handoff.md` §3.2 标注「已定：统一信封变体，未新增异常类型」，指向本任务。
- [x] 提交；步骤 6 前端另开任务。

## 范围外

- 前端 `useAgentChat` 重连、`SseError` 携带解析后 body、`streamSse` 支持 GET：属步骤 6。
- Python run 行为、Redis 投影、409 的 Python 产生逻辑：均已交付，不改。
