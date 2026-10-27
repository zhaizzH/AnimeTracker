# 前端 chat run 重连：run_id 记录、增量回放与停止

## Goal

后端已把对话生成解耦成 run（断连只退订，答案照常落库），Java 代理也已接通三条 run 路由。
但前端仍停留在旧语义：`stop()` 只是 abort、首帧 `meta.run_id` 被丢弃、刷新后不回放。
本任务让前端接上 run 能力：刷新能继续看、停止能通知后端、冲突能显式选择。

来源：[handoff.md](../10-22-fix-agent-stream-disconnect/handoff.md) §4（步骤 6）；
三个已定决策见下文「已定决策」。

## Requirements

### R1 记录 run_id

- `SsePayload` 增加 `meta?: { run_id?: string }`。
- `send()` 在首帧取到 `meta.run_id` 后存入 ref（不是 state：首帧高频、无需重渲染）。
- 每个 run 结束时清空该 ref，避免旧 run_id 被下一次停止误用。

### R2 重连与增量回放（已定：`after=0` 逐帧回放）

- `AgentChatApi` 增加三个方法，client/admin 适配层同步补：
  - `sessionRun: (id: string) => Promise<{ run_id: string; status: string }>`
  - `runStreamUrl: (runId: string, after: number) => string`
  - `stopRun: (runId: string) => Promise<void>`
- 挂载或切换会话时：`sessionRun(id)` → `status === 'running'` 则订阅 `runStreamUrl(runId, 0)` 回放。
- **回放必须新建一个空 assistant 气泡**，不得清空或复用历史气泡：`loadHistory()` 已写入持久化内容，
  回放会再推一遍全量事件，复用气泡会把内容拼接两遍。
- `after` 语义是**事件序号**（已收到的事件帧数），不是文本长度或 token 数。
- `is_end` 锁（现有局部 `ended`）在回放路径必须复用同一把，不能另建一套判据。
- status 为 `failed` / `done` / `cancelled` 时**不订阅**：`failed` 多为进程重启后的懒收敛，
  应直接 `loadHistory()` 并给「上次回答未完成」提示；`done` 说明历史里已有内容。

### R3 GET SSE 传输

- `streamSse` 当前硬编码 `method: 'POST'` 且有必填 `body`。需支持 GET：
  新增 `streamSseGet({ url, token, signal, onEvent })` 或在 `StreamOptions` 上加 `method`——
  二选一，但**不得**让 POST 调用方必须传 GET 专用字段。
- GET 路径不发请求体、不设 `Content-Type: application/json`。
- **401/403 不借用 Axios 刷新**：`hook-guidelines.md` 规定 `streamSse` 不带拦截器，
  SSE 路径必须自行分类。沿用现有「未认证或无权限」文案，不新增无限重试。

### R4 停止（已定：先 POST 后 abort；首帧前降级为 abort）

- `stop()` 顺序**必须**是 `stopRun(runId)` → 再 `abort()`。
  先 abort 会让后端把它当断连，run 继续跑完。
- `run_id` 尚未到达时**降级为纯 abort**，不排队、不抖动：此时后端还没有 run 可停，
  run 会后台跑完并落库，用户下次打开会话仍能看到答案。
- `stopRun` 失败不阻塞本地 abort（网络抖动不该让用户卡在停止中），但要记录可诊断信息。

### R5 409 冲突 UI（已定：完整冲突 UI）

- `api/http.ts` 的 `toError` 目前只保留 `message`，`data` 被丢弃；
  `sse.ts` 的 `SseError` 也只把 body 截断进 message。两条通路都要让调用方拿到解析后的 `data`。
- 后端 409 body（Java 代理层）为 `{code: 409, message, data: {active_run_id, status, capabilities}}`。
- 前端收到 409 时弹选择：**打断并插入**（`stopRun(active_run_id)` 后重发）或**等待**（不重发）。
- 选择面板必须可取消；取消后不留下半条 assistant 气泡。

## Acceptance Criteria

- [ ] AC1: 首帧 `meta.run_id` 被记录；run 结束后清空；有测试断言这两个时点。
- [ ] AC2: 挂载时 `status=running` → 以 `after=0` 订阅回放，且新建气泡不重复拼接正文。
- [ ] AC3: `after` 用事件帧计数推进，有测试证明帧数与文本长度无关。
- [ ] AC4: `status=failed`/`done`/`cancelled` 不订阅，改走 `loadHistory()`；`failed` 有用户提示。
- [ ] AC5: `stop()` 先 `stopRun` 后 `abort`（用调用顺序断言）；`run_id` 为空时只 abort。
- [ ] AC6: 409 弹出冲突选择；选「打断并插入」会先 `stopRun(active_run_id)` 再重发；选「等待」不发请求。
- [ ] AC7: `npm test`（shared/client/admin 三包）与 `npm run typecheck` 全绿；`npm run build` 通过。
- [ ] AC8: 既有 SSE 行为不回归：`answer/thinking/function_call/status` 白名单、`is_end` 锁、
      401/403 文案、主动 abort 不写中断文案。

## Constraints

- 不改后端与 Java 代理；三条 run 路由已交付（提交 `c10d0ed9`）。
- 不破坏 `SseAbortError`（主动 abort）与 `SseError`（故障）的判据分离。
- `useAgentChat` 的公开 API 尽量只增不改：现有 `messages/streaming/send/stop/select/create/remove` 行为不变。
- 401/403 走 SSE 自有分类，不引入 Axios 刷新闭环（该闭环是 `10-19-sse-client-hardening` 的独立待办）。
- client 与 admin 不互相导入；共享能力进 `@animetracker/shared`。

## 已定决策（2026-10-27）

| 决策 | 选择 | 理由 |
|---|---|---|
| 409 前端深度 | 完整冲突 UI | 「打断并插入」是 run 化的主要收益；只带数据不做 UI 等于把风险留给多 tab 场景 |
| 刷新后呈现 | `after=0` 增量回放 | 用户能看到答案继续生成，而不是空等 |
| 首帧前点停止 | 降级为纯 abort | 后端还没有 run 可停；排队或抖动只会让 UI 更糟 |

## Notes

- **刷新 ≠ 停止**：刷新时组件卸载会 abort，后端 run 继续。
- 进程重启后 `running` 投影会被懒收敛为 `failed`，且后端不补写消息——前端必须从
  「历史里没有这条回答」推出失败，不能假设能接着跑。
- `stop` 是逻辑停止：后端不 cancel 底层 task，token 仍会消耗到节点返回。
- 缓冲截断时后端先发 `status`/`warning` 帧；当前 `case 'status'` 只在 `state==='error'` 写正文，
  warning 会被静默丢弃。回放路径需决定是否提示「部分实时内容已过期」，并写进测试。
- 历史加载只恢复 role/content，不恢复 thinking；回放补的是增量，不等于能恢复思考区。
