# Implement：SSE 客户端加固

按设计落地，每一步可独立验证。所有改动都在 `frontend/packages/shared/src/` 与对应测试文件，不动后端。

## 前置核对

```bash
cd frontend && npm run typecheck && npm test
# 基线：125 用例全绿（shared 16 / client 38 / admin 71）
```

## Step 1 — sse.ts 传输层重写

文件：`frontend/packages/shared/src/sse.ts`

1. 定义两个错误类型（导出，供 useAgentChat 判断）：
   - `SseError extends Error { status?: number; contentType?: string }`
   - `SseAbortError extends Error`（`name = 'SseAbortError'`）
2. `streamSse` 内部：
   - `if (!res.ok)` → 读 `res.text()`，抛 `SseError`，带 `status` 与截断的 body 摘要；
   - 校验 `res.headers.get('content-type')` 含 `text/event-stream`，否则抛 `SseError`；
   - 分帧改空行：维护 `buf`，循环找 `\r?\n\r?\n`；帧内按行取 `data:` 前缀拼接；
   - `done=true` 后 flush `buf` 残片（非空再走一遍帧解析）；
   - `catch` 任意错 → `if (signal?.aborted) throw new SseAbortError()` 否则重抛。

**验证**：`npm run typecheck -w @animetracker/shared` 过。

## Step 2 — sse.ts 测试

新文件：`frontend/packages/shared/src/sse.test.ts`

用例（fetch 全局 mock，返回 `new Response(readable, { headers })`；`ReadableStream` jsdom 原生支持）：
1. 正常两帧（`data: {...}\n\ndata: {...}\n\n`）→ `onEvent` 收到两条 JSON 字符串；
2. 一帧被切成两个 chunk 到达 → 仍只触发一次 `onEvent`；
3. 最后一帧不带结尾空行 → flush 触发 `onEvent`；
4. Content-Type 为 `application/json` → 抛 `SseError`，`onEvent` 未被调用；
5. `res.ok=false`（500）→ 抛 `SseError` 带 `status: 500`；
6. `signal.abort()` → 抛 `SseAbortError`（或 `name==='SseAbortError'`）。

**验证**：`npm test -w @animetracker/shared` 过，用例数从 16 → 22。

## Step 3 — useAgentChat.ts 消费层改造

文件：`frontend/packages/shared/src/hooks/useAgentChat.ts`

1. `send` 内加 `const endedRef = { current: false }`（局部，非 hook ref——每次 send 独立生命周期；或用 `useRef` 在 send 开头重置，二选一，取**局部对象**更干净）；
2. `onEvent` 开头：`if (endedRef.current) return;`；解析后 `if (ev.is_end) { endedRef.current = true; return; }`；
3. 事件分发改显式 `type` 判断：
   - `type === 'answer' && c.text` → 正文累加；
   - `type === 'thinking' && c.text` → thinking 累加（保留现状）；
   - `type === 'function_call' && c.name` → start/end/error 三态，error 时 `status: 'error'`（`ToolStep.status` 联合类型加 `'error'`）；
   - `type === 'status'` → 不进正文（本任务忽略）；
   - 其余（含「有 `c.text` 但 type 不在白名单」）→ 忽略；
4. catch 分支按错误类型分流：
   - `SseAbortError` → 不写入「流式中断」文案（用户主动停止是正常路径）；
   - `SseError` 且 `status` 401/403 → 写「(未认证或无权限，请重新登录)」；
   - 其它 → 保留现状「(流式中断，请重试)」。

**验证**：`npm run typecheck -w @animetracker/shared` 过。

## Step 4 — useAgentChat 测试补强

文件：`frontend/packages/shared/src/hooks/useAgentChat.enabled.test.tsx`（沿用现有 mock 模式，`streamSseMock` 捕获 `onEvent`）

新增用例：
1. `answer` 帧累加正文、`thinking` 帧累加 thinking（回归）；
2. `status` 帧带 `content.text` → 正文**不**被污染（修复点）；
3. `is_end=true` 后再来一帧 `answer` → 正文不再追加（结束锁）；
4. `function_call` `state: 'error'` → 对应 tool `status === 'error'`，不停在 running；
5. `streamSse` 抛 `SseError({status:401})` → 消息内容为未认证文案，非通用中断文案；
6. `streamSse` 抛 `SseAbortError` → 不写中断文案。

**验证**：`npm test -w @animetracker/shared` 全绿。

## Step 5 — 全量门禁 + spec 收尾

1. `cd frontend && npm run typecheck && npm test && npm run build` 全绿（AC3：用例数 > 125）；
2. 更新 `.trellis/spec/frontend/hook-guidelines.md`：把「已知债务」段中已修复的行为（Content-Type/尾帧/类型分发/结束锁）删除或改写为现状描述；保留「401 自动刷新未实现」作为仍在的 P3 待办；
3. `git diff --stat` 核对无 `backend/**` 改动（AC5）。

## 回滚

全部改动在 `shared/src/sse.ts`、`shared/src/hooks/useAgentChat.ts`、两个测试文件与一份 spec。任一 step 出问题 `git checkout -- <file>` 单文件回滚，不影响其它。

## 提交计划

1. `fix(shared): SSE 客户端按空行分帧、校验 Content-Type、flush 尾帧并区分 Abort`（sse.ts + sse.test.ts）
2. `fix(shared): useAgentChat 按 type 分发事件、is_end 锁帧、错误状态单独分类`（useAgentChat.ts + 测试 + spec 更新）
