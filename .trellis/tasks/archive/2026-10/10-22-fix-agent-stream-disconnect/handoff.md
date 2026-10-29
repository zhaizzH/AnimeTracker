# Handoff：步骤 6（前端重连）与步骤 7（Java 代理）

> 生成于 2026-10-23，任务 `10-22-fix-agent-stream-disconnect` 后端部分收尾之后。
> 后端步骤 0–5 + 8 已完成并提交；本文件只交接**未开工的两个后续步骤**。
> 读这份文件前不需要重读 design.md，但涉及决策背景时请回查 [decisions.md](./decisions.md) 与 [design.md](./design.md) §9。

---

## 1. 当前交付状态（一句话）

刷新页面不再丢答案：生成跑在独立的 `asyncio.Task`（run）里，SSE 断连只退订。**但前端仍在刷新时 abort、且浏览器无法直达新路由**——因为 Java 代理还没加、前端还在用旧的 abort 语义。所以「用户感知不到丢答案」这个目标目前只到「答案在历史里」这一层，增量恢复还没接通。

已完成（均已提交，全量 853 passed / 契约子集 146 passed / 前端三包全绿）：

| 步骤 | 提交 |
|---|---|
| 0 固化复现 | `e6f58d60` |
| 1 ChatRunManager 骨架 + 断连不取消 | `327772b1` |
| 2 接入 service 与 API | `8ca0d7b2` |
| 3 Redis run 状态投影 + 懒收敛 | `6cb7afe0` |
| 4 四项副作用 | `737a195c` |
| 5 用户主动停止（逻辑停止） | `737a195c` |
| 8 收尾（spec 回写等） | `876e4fb2` / `4d83dfbb` |

---

## 2. 后端已提供的三个新路由（步骤 6/7 的唯一接口依据）

Python 侧实现见 `backend/agent/app/api/chat.py`，行为契约见 `.trellis/spec/backend/contract-tests.md` 的「Run 生命周期契约」。

| 方法 | Python 路径（client） | Python 路径（admin） | 说明 |
|---|---|---|---|
| `GET` | `/api/client/agent/runs/{run_id}/stream?after=N` | `/api/admin/agent/chat/runs/{run_id}/stream?after=N` | 重连同一 run；`after` 为已收到的事件数；缓冲截断时先发 `status`/`warning` 帧；恰好一个 `is_end` 且最后 |
| `GET` | `/api/client/agent/sessions/{session_id}/run` | `/api/admin/agent/chat/sessions/{session_id}/run` | 返回 `{run_id, status}`；`status ∈ running/done/failed/cancelled`；无 run → 404 |
| `POST` | `/api/client/agent/runs/{run_id}/stop` | `/api/admin/agent/chat/runs/{run_id}/stop` | 立即 200，返回 `{run_id, status:"cancelled"}`；幂等 |

另外 `POST /stream` 首帧的 `meta.run_id` 是**前端唯一能拿到 run_id 的地方**（Q10）：

```json
{"type":"answer","content":{"text":"…"},"meta":{"run_id":"<hex>"},"is_end":false,"timestamp":...}
```

`POST /stream` 在同会话已有 running run 时返回 **409**：

```json
{"detail": {"active_run_id": "<hex>", "status": "running", "capabilities": ["interrupt"]}}
```

---

## 3. 步骤 7：Java 代理（**已由任务 `10-27-agent-run-proxy-java` 实施**）

> 本节保留交接时的调查背景；最终接口以该任务的 `prd.md`、Java 源码和 `docs/spec/openapi.yaml` 为准。
> 已定并实施：新增 `streamGet`，三路由两端均已代理；409 采用统一信封变体，detail 放入 `data`，未新增异常类型或 `@ExceptionHandler`。

### 3.1 要改的文件（已核实，非推测）

| 文件 | 改动 |
|---|---|
| `backend/business/agent/src/main/java/top/zhaizz/agent/constant/AgentApiPaths.java` | 加 client/admin 两套 run 路径常量 |
| `.../controller/ClientAgentController.java` | 加 3 个路由（GET stream / GET session run / POST stop） |
| `.../controller/AdminAgentController.java` | 同上，前缀是 `/api/admin/agent/chat` |
| `.../service/AgentService.java` | **可能需要扩签名**，见 3.3 |
| `.../service/impl/AgentServiceImpl.java` | **必须改**，见 3.2 / 3.3 |
| `docs/spec/openapi.yaml` | 收录三个路由（该文件记录的是 Java 对外层路径） |

### 3.2 阻塞点 1：409 被吞成 400，且 body 丢失

`AgentServiceImpl.forwardStream`（L201-206）与 `forward`（L149-154）都是：

```java
catch (HttpStatusCodeException e) {
    if (e.getStatusCode().is5xxServerError()) throw new BizException(ErrorType.SERVICE_UNAVAILABLE);
    throw new BizException(mapUpstream4xx(e.getStatusCode().value()));
}
```

而 `mapUpstream4xx`（L219-227）：

```java
private ErrorType mapUpstream4xx(int status) {
    return switch (status) {
        case 401 -> ErrorType.UNAUTHORIZED;
        case 403 -> ErrorType.FORBIDDEN;
        case 404 -> ErrorType.NOT_FOUND;
        case 429 -> ErrorType.TOO_MANY_REQUESTS;
        default -> ErrorType.BAD_REQUEST;   // ← 409 落到这里
    };
}
```

后果：D2 的 409 到前端变成 `400 请求参数错误`，且 `detail.active_run_id` **完全丢失**（`BizException` 只承载 `ErrorType` + message）。

`ErrorType.CONFLICT(409)` 已存在，不用新增枚举。**交接时待定**的三种候选如下；最终采用统一信封变体，见本节开头说明：

- **A（契约完整）**：新增 `AgentConflictException`（携带上游 body），`forward`/`forwardStream` 在 409 时抛它，Controller 用 `@ExceptionHandler` 原样回 409 + body。
- **B（最小改动）**：只加 `case 409 -> ErrorType.CONFLICT`，前端二次 `JSON.parse(message)`（丢字段语义）。
- **C（本次不做 409）**：只接通三个 GET/POST 路由，`/stream` 的 409 留到前端任务一起做；风险是多 tab / 刷新后重发会静默并存两条 run。

> 建议 A。理由是「打断并插入」是这次 run 化的主要收益之一，B 让前端只能靠字符串解析，C 会把并发保护推迟到一个更晚的任务里。

### 3.3 阻塞点 2：`stream()` 签名假设「POST + JSON body」

```java
void stream(String path, HttpMethod method, String authorization, Object body, Consumer<String> lineConsumer);
```

`forwardStream` 内部无条件（L178 / L189）：

```java
headers.setContentType(MediaType.APPLICATION_JSON);
...
if (body != null) { request.getBody().write(body.getBytes(UTF_8)); }
```

`GET /runs/{id}/stream?after=N` 是 **GET + query 参数**。`java.net.HttpURLConnection` 对 GET 带 body 会报错（或行为未定义），且 query 必须拼进 URL。

两条路：

- **a**：新增 `streamGet(String path, String query, String auth, Consumer<String> lineConsumer)` 重载，避免让既有 POST 路径背上 `body==null` 的分支判断。
- **b**：在 `forwardStream` 里按 `method == GET` 分支处理（不设 Content-Type、不写 body、query 由 caller 拼进 path）。

> 建议 a：语义清晰，且 `AgentService` 是接口、改动成本低。注意 `path` 里如果 callers 自己拼 `?after=` 也可行，但会让「路径常量」不再是纯路径——不推荐。

### 3.4 常量组织

现状是「完整路径常量」（`CLIENT_SESSIONS = "/api/client/agent/sessions"`，Controller 里 `+ "/" + sessionId + "/history"`）。建议延续：

```java
/** 客户端 run 路由前缀 */
public static final String CLIENT_RUNS = "/api/client/agent/runs";
/** 管理端 run 路由前缀 */
public static final String ADMIN_RUNS = "/api/admin/agent/chat/runs";
```

`/sessions/{id}/run` 复用已有 `CLIENT_SESSIONS + "/" + sessionId + "/run"`，不需要新常量。

### 3.5 验收

Java 侧测试风格是**纯 JUnit 5 + Mockito，不起 Spring 上下文**（`spring-boot-starter-test` 在，但现有 `ClientAgentControllerTest` / `AdminAgentControllerTest` 都是 `mock(AgentService.class)` + 直接 new Controller + mock `HttpServletResponse`）。不要引入 MockMvc，与既有风格保持一致。

- `mvn -B -pl agent test` 绿（模块目录 `backend/business/agent`）。
- 在 `ClientAgentControllerTest` / `AdminAgentControllerTest` 补：
  - GET stream：验证 `agentService.streamGet(...)` 收到正确 path 与 `after` query，逐行写回 writer。
  - GET session run / POST stop：验证 `exchange(...)` 的 path + method，返回包装后的 `Result`。
  - 409 透传：服务层验证 `BizException` 的 code 为 409 且 `data.active_run_id` 保留；由既有 `GlobalExceptionHandler` 输出统一信封。
- 手工：`curl -N -H "Authorization: Bearer $T" "http://localhost:8080/api/client/agent/runs/$RUN/stream?after=0"`。

---

## 4. 步骤 6：前端重连

### 4.1 现状（已核实）

`frontend/packages/shared/src/hooks/useAgentChat.ts`（170 行）：

- `send()` 用 `streamSse({url, body, token, signal})`；`stop()` 就是 `ab.current?.abort()`——**纯 abort，不通知后端**。所以现在点「停止」= 断连 = run 继续跑完（后端会落库带中断前缀的答案，但用户看不到变化）。
- `SsePayload` 接口**没有 `meta` 字段**，首帧的 `run_id` 目前被丢弃。
- `AgentChatApi` 接口只有 `listSessions/createSession/history/deleteSession/streamBody/streamUrl/health`，没有 run 相关方法。
- `frontend/packages/shared/src/sse.ts` 的 `streamSse` **硬编码 `method: 'POST'`**，重连要走 GET 就必须扩签名（加 `method` / 或新增 `streamSseGet`）。
- `SseAbortError` 语义是「调用方主动 abort，不是故障」——重构时不要破坏这个判据。

已有测试：`useAgentChat.events.test.tsx`、`useAgentChat.enabled.test.tsx`。

### 4.2 要做的改动

1. `SsePayload` 加 `meta?: { run_id?: string }`；`send()` 收到首帧时存进 ref。
2. `AgentChatApi` 加：
   - `sessionRun: (id) => Promise<{run_id: string; status: string}>`
   - `runStreamUrl: (runId: string, after: number) => string`
   - `stopRun: (runId: string) => Promise<void>`
   - client/admin 各自的 api 适配层（`frontend/client/src/**`、`frontend/admin/src/**` 里注入 `api` 对象的地方）要同步补。
3. 挂载 / 切换会话：`sessionRun(id)` → 若 `status === 'running'` 用 `?after=0` 订阅回放。
4. `stop()` 改为：`stopRun(runId)` → 然后 abort 本地流（**顺序不能反**：先 abort 会让后端把它当断连，run 继续跑）。
5. 409 处理：`streamSse` 抛的 `SseError` 已带 `status`，但 body 只截断进 message。若要弹选择面板，需要让 `SseError` 带上解析后的 body（配合步骤 7 的选项 A）。

### 4.3 语义陷阱（务必写进测试）

- **刷新 ≠ 停止**：刷新时组件卸载会 abort，后端的 run 继续。回放时 `after=0` 会重放全部事件，**前端必须先把当前 assistant 气泡清空**，否则内容会拼接两遍。
- **`after` 是事件序号，不是 token 数**：必须用「已收到的事件帧数量」作为游标，不能用文本长度。
- **`is_end` 出现即停止累积**：现有 `ended.current` 锁已有，但重连路径要复用同一把锁，否则 END 之后还可能漏进帧。
- **`status`/`warning` 帧**（缓冲截断降级）：现在 `case 'status'` 只在 `state === 'error'` 时写正文，warning 会被静默丢弃。重连路径要考虑是否提示「部分实时内容已过期，完整回答请查看历史记录」。
- **进程重启后 `running` 会被懒收敛成 `failed`**（D9）：前端拿到 `failed` 时不该去订阅（会 404 或立刻结束），应直接 `loadHistory()` 并提示。

### 4.4 验收

- `useAgentChat.events.test.tsx` 补：run_id 记录、`after=0` 回放不重复拼接、`stop()` 先 POST 后 abort、`failed` 时回退到历史。
- `npm test`（三包）绿；`npm run typecheck` 绿。

---

## 5. 未决问题（需要决策后才能开工）

1. **409 契约**：已定并实施为统一信封变体；前端从 `data.active_run_id` 读取，不再等待 A/B/C 选择。
2. **执行顺序**：建议先 7 后 6（Java 是纯透传、MockMvc 可测；前端重连依赖它才能端到端验证）。若先做 6，前端只能用 mock 验证，真实联调要等 7。
3. **任务台账**：是否在 `.trellis/tasks/` 下新建两个任务（推荐，便于独立排期与回退），还是继续留在 `10-22-fix-agent-stream-disconnect` 下追加步骤。

---

## 6. 其他已知边界（不要误判为 bug）

- **重启不恢复执行**：run 只活在进程内。`agent:run:{run_id}`（TTL 900s）是状态投影，读到 `running` 但内存无此 run → 懒收敛为 `failed`，且**不补写消息**。
- **`stop` 不会真的停掉底层计算**：节点是同步闭包跑在 LangGraph 的 executor 里，`task.cancel()` 无效。`stop` 只标状态 + 合成终态帧 + 立即返回；token 仍会被继续消耗到节点返回。这是架构限制，不是实现偷懒。
- **`openapi.yaml` 未收录三个新路由**：因为它记录 Java 对外层路径，而代理未实现。步骤 7 必须一起补。
- **`_drive` 里 pending_action collector 是自管 contextvar**：不能在 `start()` 里 set 后跨任务 reset（会抛 `ValueError: was created in a different Context`）。改这块前先读 `app/chat/runs.py` 顶部注释。
- **test_streaming.py 已改为纯事件断言**：落库相关测试都在 manager 层（`test_chat_run_manager.py` / `test_run_side_effects.py`）。别把持久化断言加回 streaming 层。

---

## 7. 参考命令

```bash
# 后端
cd backend/agent && source .venv/Scripts/activate
python -m pytest tests/ -q
python -m pytest tests/contracts -q
python -m pytest tests/api/test_run_api.py -q
python -m pytest tests/agent/test_chat_run_manager.py tests/agent/test_run_side_effects.py -q

# 前端
cd frontend && npm test && npm run typecheck

# Java
cd backend/business && mvn -B -pl agent test
```
