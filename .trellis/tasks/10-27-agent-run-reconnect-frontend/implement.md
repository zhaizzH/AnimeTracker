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

- [ ] `api/agent.ts`：`sessionRun`、`stopRun`（`runStreamUrl` 在 hook 里由 `streamUrl` 前缀推导，
      或显式给出——两者择一，但 client/admin 必须一致）。
- [ ] `api/admin/agent.ts`：对应三方法。
- [ ] `api/http.ts` 的 `toError`：把解析后的 `data` 挂到 Error 上，供 409 UI 读取。
- [ ] client/admin 两个注入对象（`client/src/components/AgentChat.tsx`、`admin/src/pages/AgentChat.tsx`）同步补字段。
- [ ] 用例：路径前缀正确（client vs admin）、`stopRun` 走 POST、`sessionRun` 走 GET。

## 步骤 3：run_id 记录与停止时序（TDD）

- [ ] `SsePayload` 加 `meta`；首帧存 `runIdRef`，run 结束（`finally`）清空。
- [ ] `stop()`：`runIdRef.current` 存在 → `stopRun(runId)` 再 `abort()`；
      不存在 → 直接 `abort()`。`stopRun` 失败也要 abort。
- [ ] 用例：顺序断言（用调用序列数组）、首帧前停止只 abort、`stopRun` 抛错仍 abort。

## 步骤 4：重连回放（TDD）

- [ ] 挂载/切会话：`sessionRun(id)`。
  - `running` → 新建空 assistant 气泡 + 订阅 `runStreamUrl(runId, 0)`，复用同一 `ended` 锁。
  - `failed` → `loadHistory()` + 「上次回答未完成」提示；`done`/`cancelled` → 仅 `loadHistory()`。
- [ ] 事件计数游标：每收到一帧 `after += 1`；不订阅时游标归零。
- [ ] `status` 的 `warning` 文案：决定在回放路径提示「部分实时内容已过期」并写进测试。
- [ ] 用例：回放不重复拼接（历史一条 + 回放增量 → 正文只出现一次）、`failed` 不订阅、
      `is_end` 之后不再累积。

## 步骤 5：409 冲突 UI（TDD）

- [ ] shared 暴露冲突错误类型（携带 `active_run_id`），`send()` 捕获后进入选择状态。
- [ ] client 与 admin 各加选择面板：`打断并插入` / `等待` / 取消。
      - 打断并插入：`stopRun(active_run_id)` → 重新 `send(同一文本)`。
      - 等待 / 取消：不发请求，清掉半成品气泡。
- [ ] 用例：409 进入选择态、打断路径先 stop 再 send、等待不发请求、取消不留下空气泡。

## 步骤 6：收尾

- [ ] `npm test`（三包）+ `npm run typecheck` + `npm run build`。
- [ ] spec 回写：`frontend/hook-guidelines.md` 的 SSE 现状段落补 run 重连语义
      （断连≠停止、after 是事件序号、回放新建气泡、409 选择）。
- [ ] 提交。

## 范围外

- 后端 run 行为、Java 代理路由：已交付（`c10d0ed9`）。
- SSE 401 自动刷新闭环：属 `10-19-sse-client-hardening` 的 P3 待办，本任务只用现有分类。
- 历史恢复 thinking：后端不存 thinking，属独立任务。
