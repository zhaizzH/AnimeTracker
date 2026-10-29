# 执行计划：前端 chat run 重连

> 关联 [prd.md](./prd.md) 与上游交接 [handoff.md](../archive/2026-10/10-22-fix-agent-stream-disconnect/handoff.md) §4。
> 每步先写红测试；`shared` 的 hook 测试用现有 `streamSseMock` 桩，不触网。

## 步骤 0：基线

- [x] `cd frontend && npm test`（shared/client/admin）与 `npm run typecheck` 记录当前通过数。

实测 2026-10-27（提交 `4420298d` 之后）：`shared` 6 文件 / 34 用例，`client` 9 文件 / 38 用例，`admin` 11 文件 / 73 用例 → 合计 **26 文件 / 145 用例，全绿**；`npm run typecheck` 三包零输出（通过）。本任务完成后对照此基线：只增不减，`useAgentChat` 两个已有用例文件（`useAgentChat.events.test.tsx`、`useAgentChat.enabled.test.tsx`）必须仍在绿。

## 步骤 1：传输层支持 GET（TDD）

- [x] `sse.ts`：让 GET 可复用分帧/abort/Content-Type 校验逻辑，但**不**要求 POST 调用方传 GET 字段。
      POST 现有行为逐字不变（含 `body: JSON.stringify(body)`）。
- [x] `SseError` 增加 `body?: unknown`（解析后的 JSON，解析失败为 undefined），message 仍只放截断摘要。
- [x] 用例：GET 请求 method 为 GET、无 body、无 JSON Content-Type；POST 行为不回归；
      非 event-stream 仍抛 `SseError`；abort 仍抛 `SseAbortError`。

实现：`StreamOptions` 加 `method?: 'POST' | 'GET'`（默认 POST）、`body` 改可选；GET 分支只省掉 body 与 JSON Content-Type，分帧/abort 判据逐字不动。`parseBody()` 把非 2xx 错误体读成 JSON 挂到 `SseError.body`，解析失败为 `undefined`（绝不抛）。新增 4 用例，`shared` 34 → 38。

## 步骤 2：API 适配层（TDD）

- [x] `api/agent.ts`：`sessionRun`、`stopRun`（`runStreamUrl` 在 hook 里由 `streamUrl` 前缀推导，
      或显式给出——两者择一，但 client/admin 必须一致）。
- [x] `api/admin/agent.ts`：对应三方法。
- [x] `api/http.ts` 的 `toError`：把解析后的 `data` 挂到 Error 上，供 409 UI 读取。
- [x] client/admin 两个注入对象（`client/src/components/AgentChat.tsx`、`admin/src/pages/AgentChat.tsx`）同步补字段。
- [x] 用例：路径前缀正确（client vs admin）、`stopRun` 走 POST、`sessionRun` 走 GET。

实现：`runStreamUrl` 选择**显式给出**（client `/api/client/agent/runs/{id}/stream`，admin `/api/admin/agent/chat/runs/{id}/stream`），不在 hook 里由 `streamUrl` 前缀推导——两者路径段不同（`agent/runs` vs `agent/chat/runs`），推导只会引入字符串魔法。`AgentChatApi` 三个新方法设为**必填**，让 typecheck 强制 client/admin 两个注入点同步（缺失即编译失败，而不是运行时静默跳过重连）。

## 步骤 3–6：已拆成 tracer bullet 工单

后续工作的单一来源改为 [issues/](./issues/)（每个工单一个文件，按依赖顺序编号）：

| 工单 | 内容 | 依赖 |
|---|---|---|
| [01](./issues/01-run-id-and-real-stop.md) | 记录 `run_id`，`stop()` 先停 run 再 abort | 无 |
| [02](./issues/02-reconnect-replay.md) | 刷新/切会话后增量回放，正文不重复 | 无（与 01 同文件，建议顺序做） |
| [03](./issues/03-conflict-choice.md) | 409 冲突三选一（打断插入 / 等待 / 取消） | 01 |
| [04](./issues/04-spec-and-deliver.md) | 规范回写 + 三包测试 + build 交付 | 01–03 |

原步骤 3–6 的分层清单已并入上述工单的验收标准，本节不再重复（避免两处描述漂移）。

## 范围外

- 后端 run 行为、Java 代理路由：已交付（`c10d0ed9`）。
- SSE 401 自动刷新闭环：属 `10-19-sse-client-hardening` 的 P3 待办，本任务只用现有分类。
- 历史恢复 thinking：后端不存 thinking，属独立任务。

## 交接附注：已知缺口（不阻塞 AC，但别误判为已修）

- **409 面板连环弹**：原记载「stopRun 是逻辑停止、run 未立即结束所以重发仍 409」**已被源码证伪**（`runs.py:199` 同步置 CANCELLED，`:186` 只认 RUNNING）。真实入口只有两个：停 run 失败后仍盲重发；双击触发两次尝试。两者均由任务 `10-29-fix-conflict-retry-loop` 修复。多标签场景是设计意图，不修。
- **`capabilities` 未读**：面板恒显三个按钮。已由 `10-29-fix-conflict-retry-loop` 接上（显式不含 `interrupt` 时禁用，缺字段按可用处理）。
- **`failed` 提示是临时气泡**：作为一条 assistant 消息写入，刷新即消失。要常驻需在 client/admin 渲染层加 notice 通道。
- **回放正常结束不刷新会话列表**：`send()` 的 `finally` 会 `refreshSessions()`，回放路径没有，列表排序/标题可能滞后。
- **回放落库与状态投影有毫秒级窗口**：run 已落库但状态仍是 `running` 时刷新，会「历史一条 + 回放一条」。窗口极窄，未处理。
