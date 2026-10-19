# Design：SSE 客户端加固

## 权威事实（来自源码与契约）

- 后端单帧格式（`backend/agent/app/api/schemas/sse.py:serialize_sse`）：
  `data: {json}\n\n` —— **单行 JSON、空行分帧、`exclude_none=True`、`ensure_ascii=False`**。
- 结束帧（`sse.py:serialize_agent_event`）：`AgentEventType.END` → `{ "content": {}, "is_end": true }`，**无 `type`**。
- 响应头：`text/event-stream` + `Cache-Control: no-cache` + `Connection: keep-alive` + `X-Accel-Buffering: no`。
- 错误前置：`create_sse_response` 在流开始前返回；上游 4xx/5xx 在响应提交前是普通 JSON 错误体（`openapi.yaml` 已知债务 #4，本任务**按"响应提交前返回 JSON"处理**，即校验 Content-Type 会挡下这类情况）。
- `openapi.yaml` 已知债务 #3（Spring 转发可能写出空 `data:` 行）属后端行为，前端**容错**而非修复。

## 设计决策

### D1 分帧粒度：以空行 `\r?\n\r?\n` 为准，不按单换行

后端单帧本身不含换行（单行 JSON），但实际流经 Spring 逐行转发后，一个 `data:` 帧可能被拆成多个 chunk 到达；且规范上 SSE 以空行分帧。**落点**：累积 buffer，按空行切帧；帧内允许多行，只取 `data:` 前缀的行拼接（防御性，正常只有一行）。这样同时覆盖「单帧一行」与「防御未来多行」两种情况。

### D2 Content-Type 校验在 `res.ok` 之后立即做

`res.ok` 只保证 2xx；Spring 转发错误页/JSON 时 `res.ok` 为 true 但 `Content-Type` 不是 `text/event-stream`。**落点**：`streamSse` 内 `if (!res.ok) → 读 body 抛带状态的错`；`else if (!contentType.includes('text/event-stream')) → 抛协议错`。错误消息带状态码与实际 Content-Type。

### D3 尾帧 flush：流结束（`done=true`）时把 buffer 残片作为最后一帧处理

只要后端始终按 `\n\n` 收尾，这条是防御性的；但 `openapi.yaml` #3 说明 Spring 转发空行处理不确定，flush 能兜住「最后一帧没带结尾空行」的情况。**落点**：`reader.read()` 返回 `done` 后，若 `buf.trim()` 非空则再走一遍帧解析。

### D4 Abort vs 故障：`signal.aborted` 是唯一判据

不解析 error 文案（`AbortError` 名字在不同环境不一致）。**落点**：catch 到任何错，先看 `signal?.aborted`——是则抛 `SseAbortError`（或带 `aborted: true` 标记），否则抛 `SseError`。调用方（`useAgentChat`）据此区分「用户点了停止」与「流断了」。

### D5 事件类型分发：`type` 优先，`content.text` 不再作为兜底

现状 bug：`else if (c.text)` 会让任何带 `text` 的事件（包括 `status`、`function_call` 的 message）落进正文。**落点**：
- `answer` → 正文累加
- `thinking` → thinking 累加（现状已对，保留）
- `function_call` → `tools` 数组；`state: 'start' | 'end'`，**失败是 `state: 'end'` + `result: 'error'`**（`middleware.py:emit_function_call`），不是 `state: 'error'`；两者都要落到 `status: 'error'`，不得把失败工具标成 `done`；
- `status` → 不进正文；但 `state: 'error'` 时 `message` 是后端给用户看的持久化失败文案（`streaming.py:160,177`），必须追加到回答尾部，不得静默丢弃；非 error 的 `status` 不渲染（本任务不引入新的 UI 面）
- 结束帧 `{is_end: true}` → 置 `ended.current = true`，之后所有帧直接 return（**结束锁**）

### D6 结束锁用局部对象不用 state

`streaming` 是 state，置位有渲染延迟；结束锁必须同步生效（下一帧到来时立刻拦）。**落点**：`send` 内用局部 `const ended = { current: false }`（每次 send 独立生命周期，比 hook 级 ref 更干净），`is_end` 时置位，`onEvent` 开头检查。

### D7 鉴权失败单独分类

401/403 在 `streamSse` 内 `!res.ok` 分支识别（读 body 尝试解析 `{code, message}`），抛带 `status: 401|403` 的错；`useAgentChat` catch 后按 `err.status` 区分：401/403 → 「未认证/无权限」文案，其它 → 「流式中断，请重试」。**不**在本任务做自动刷新重试（spec 标注「后续应实现」，已列入 P3 待办）。

## 不做的事

- 不改后端帧格式、不改 Spring 转发。
- 不引入 `eventsource` polyfill / 第三方 SSE 库（现 fetch+reader 够用，引入依赖收益不抵成本）。
- 不做 401 自动刷新闭环（P3）。
- 不动 client/admin 各自的渲染组件。

## 测试策略

- **sse.ts**：构造 `ReadableStream` 桩（jsdom 有原生实现），用 `fetch` mock 返回可控流——按帧/按字节切碎、缺尾空行、错误 Content-Type、`res.ok=false`、`signal.abort()`。
- **useAgentChat**：沿用现有 `useAgentChat.enabled.test.tsx` 的 `vi.mock('../sse')` 模式，让 `streamSseMock` 捕获 `onEvent` 回调并手动喂帧——四类事件分发、`is_end` 锁帧、`function_call` error 状态、401/403 文案。
