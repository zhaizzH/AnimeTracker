# Java 代理补齐 chat run 三路由（重连/状态/停止）

## Goal

在 `backend/business/agent` 代理 Python 的三个 run 路由，让浏览器能直达后端已交付的 run 能力；
并让上游 409（同会话已有 running run）以结构化数据透传到前端，支撑「打断并插入」。

来源：`10-22-fix-agent-stream-disconnect` 的 [handoff.md](../10-22-fix-agent-stream-disconnect/handoff.md) 步骤 7。
步骤 6（前端重连）不在本任务内，另开任务。

## Requirements

### R1 三个路由 × client/admin 两端

Python 侧真实路径（`backend/agent/app/api/chat.py` + `main.py` 挂载前缀）：

| 方法 | client | admin | 说明 |
|---|---|---|---|
| GET | `/api/client/agent/runs/{runId}/stream?after=N` | `/api/admin/agent/chat/runs/{runId}/stream` | SSE 重连同一 run |
| GET | `/api/client/agent/sessions/{sessionId}/run` | `/api/admin/agent/chat/sessions/{sessionId}/run` | `{run_id, status}` |
| POST | `/api/client/agent/runs/{runId}/stop` | `/api/admin/agent/chat/runs/{runId}/stop` | 逻辑停止，立即 200 |

Spring 对外路径与上游路径**一致**（与既有 `/stream`、`/sessions` 代理同形），不做改写。

### R2 GET SSE 转发

- 新增 `AgentService.streamGet(path, query, authorization, lineConsumer)`（handoff 3.3 选项 a）。
- GET 不写请求体、不设 `Content-Type: application/json`；`after` 以 query 传递，不拼进路径常量。
- 复用无读超时的 SSE 客户端与逐行转发；收到上游首行前不得获取 response writer（既有防错约定）。
- `Authorization` 与 `X-Request-ID` 透传行为不变。

### R3 409 结构化透传（已定：统一信封变体）

- `forward` 与 `forwardStream` 遇到上游 409 → `BizException(ErrorType.CONFLICT, 中文消息, detail)`，
  由既有 `GlobalExceptionHandler` 输出 HTTP 409 + `{code, message, data}`。
- `data` = 上游 body 的 `detail` 对象（含 `active_run_id` / `status` / `capabilities`）。
- **不**新增异常类型、**不**新增 `@ExceptionHandler`、**不**返回裸 `{detail: ...}`——
  仓库硬约定是统一信封，且「Controller 不捕获再包装业务异常」（`error-handling.md`）。
- 上游 body 解析失败或缺少 `detail` 对象时 `data` 为 null；**不把原始上游 body 拼进 message**（隐私约定）。
- 其他 4xx/5xx 映射不变；导入网关 `HttpImportAgentGateway` 的错误映射**不**合并复用。

### R4 契约收录

- `docs/spec/openapi.yaml` 收录上述 6 个 operation（该文件记录 Java 对外层路径），
  含 `after` query、`text/event-stream` 响应、run 状态/停止响应体与 409 响应。
- `.trellis/spec/backend/contract-tests.md` 删除「openapi.yaml 暂未收录」的过渡说明，改写为已收录 + Java 409 信封事实。

## Acceptance Criteria

- [x] AC1: client 与 admin 各有 3 个新路由，Controller 单测验证 path / method / query 与 SSE 写出。
- [x] AC2: GET SSE 用例证明「上游报错前不取 writer」；`streamGet` 用例证明 GET 无 body 且 query 正确。
- [x] AC3: 上游 409 在 `exchange` 与 `streamGet` 两条路径都得到 HTTP 409 语义 + `data.active_run_id`；其他 4xx 映射不回归。
- [x] AC4: `docs/spec/openapi.yaml` 收录 6 个 operation，契约套件新增断言防止回退；`pytest tests/contracts -q` 绿。
- [x] AC5: `mvn -B test`（全 reactor）绿；`pytest backend/agent/tests -q` 全绿（Python 未改动，不允许回归）。
- [x] AC6: Security 无需改动即可放行（`/api/client/**` authenticated、`/api/admin/**` hasRole ADMIN），不新增 permitAll。

## Constraints

- 测试风格保持纯 JUnit 5 + Mockito，不起 Spring 上下文、不引入 MockMvc；`AgentServiceImpl` 的 HTTP 层用 `MockRestServiceServer` / JDK `HttpServer`。
- 不改 `SecurityConfig`、不改 `AgentConfig` 装配签名（`streamGet` 走既有 `AgentService` Bean）。
- 不实现前端重连、不改 `useAgentChat`；不动 Python 侧 run 逻辑。
- 新路由不需要在 `SecurityConfig` 单独登记；不得为「调通」而加 `permitAll`。

## Notes

- 上游 404（他人 run / 无 run）保持既有 `mapUpstream4xx` → 404，不暴露存在性。
- `stop` 是逻辑停止：Java 只透传，不等待底层任务结束，也不另加超时。
- 交付后浏览器可直达三路由，但「刷新后增量恢复」仍依赖步骤 6 前端任务。
