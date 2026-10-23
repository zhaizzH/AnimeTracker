# 设计决策记录

> 2026-10-23 经 `/grill-me` 拷问（Q1–Q14）后修订。D1/D2 保留核心方向但修正关键细节；D3–D10 为拷问新增。

## D1: `_drive` 与 `stream_agent_events` 的关系 — 回调提升（方案二）

**日期**: 2026-10-23
**状态**: 已确认

### 决策

采用**回调提升**方案：从 `stream_agent_events` 中移除 `on_answer_completed` 和 `on_pending_action` 的调用逻辑（~30 行），使其成为**纯事件生产者**。`ChatRunManager._drive()` 成为唯一的收尾责任人，在 `finally` 中统一执行持久化回调。

### 对 `stream_agent_events` 的改动

- **删除**: L150-181 的 `on_answer_completed` / `on_pending_action` 调用段落
- **保留**: producer task + queue + contextvar 设置/清理 + observability + `extract_final_content` + END 帧 + `producer.cancel()`
- `StreamConfig` 的 `on_answer_completed` / `on_pending_action` 字段保留（`_drive` 读取）

### contextvar 细节（Q3 确认）

- `start()` 在 `create_task` **之前** `set_event_sink(...)` + `set_pending_action_collector()`，token 传进 `_drive`。
- `asyncio.create_task` 拷贝当前 context，`_drive` 内部继承 sink/collector。
- `_drive` 消费时累积 `aggregated_answer` 和 `used_tools`；finally 里 `get_pending_action_event()` + 调回调 + `reset`。

### `_drive` finally 中的 CancelledError 防御

- 不使用 `asyncio.shield()`（语义复杂且 shield 自身也抛 CancelledError）
- 用 `try/except CancelledError` 兜底二次取消；二次取消时答案丢失，由 §6 stale-run 检测在下次启动时补写"生成已中断"
- `shutdown()` 约束：只 `cancel()` 一次 + `gather` 等待，不设超时后二次 cancel

### 理由

- **单一持久化路径**：消除纯包裹方案中两条持久化路径的幂等协调问题
- **改动面可控**：对 `streaming.py` 是纯删除，不碰 producer / queue / contextvar / observability
- **可测试性**：持久化行为只需在 `_drive` 层测试一处

### 拒绝的方案

- **纯包裹**：`stream_agent_events` 内部回调 + `_drive` 补偿 → 两条持久化路径，需跨模块幂等标记
- **完全内联**：消除 `stream_agent_events` → 改动面过大，破坏所有现有测试锚点

---

## D2: 同会话并发 run — 409 + 用户显式选择

**日期**: 2026-10-23
**状态**: 已确认

### 决策

后端检测到同会话存在 active run 时返回 **409 Conflict**，前端弹出选择面板让用户决策。本次提供「直接插入」选项；「引导对话」选项展示但标记为不可用，待 checkpointer 等前置条件完成后启用。

### 后端行为

- `POST /stream`：若 `active_for_session()` 找到 `status=RUNNING` 的 run → 返回 `409 { active_run_id, status, capabilities: ["interrupt"] }`
- `POST /runs/{run_id}/stop`：**逻辑停止**（见 D3）——标记 `cancelled` + 合成工具终态帧 + END 帧 + 立即返回 200。底层 task 不 cancel，自然跑完后落库部分答案。
- `capabilities` 字段预留扩展：将来加 checkpointer 后返回 `["interrupt", "steer"]`，前端据此启用「引导对话」。

### 前端行为

- **前置拦截**：`streaming=true` 时前端本地拦截发送，直接弹选择面板（不走网络）。
- **后端安全网**：刷新/多 tab 场景下 409 兜底，前端解析后弹同样的面板。
- **选择面板**：「直接插入」可用（stop → send）；「引导对话（即将推出）」置灰。
- `interruptAndSend(runId, content)`：先 `POST /runs/{id}/stop` → await 200 → 再 `POST /stream`。

### 消息顺序保证

原 D2 的 stop-and-wait 已被 D3（逻辑停止）替代。消息顺序改由 **per-session persist future** 保证（见 D4）：新 run 落 user 消息前 `await` 上一 run 的持久化完成，超时 5s 降级继续。

### Java 代理层

需确认 `agentService` 对 409 的透传：当前若将非 2xx 统一包装为 500，需改为透传 409 status + body。

### 拒绝的方案

- **Auto-stop-and-wait（静默处理）**：不给用户选择权，与 §9 的显式双选需求矛盾；且将来无法扩展为 steering
- **允许并存**：两个 assistant 交错写入，消息顺序不可控

---

## D3: 停止语义 — 逻辑停止，非物理取消

**日期**: 2026-10-23（Q1 确认）
**状态**: 已确认

### 决策

`POST /runs/{run_id}/stop` 是**逻辑停止**：标记 `status=cancelled`，合成未闭合工具的 `state=end, result=aborted` 帧 + END 帧广播给订阅者，立即返回 200。底层 `asyncio.Task` **不 cancel**，让它自然跑完；跑完时 `_drive` finally 发现 `status==cancelled`，落库已生成部分为「部分答案」。

### 理由

已核实：节点是同步闭包（`build_search_agent` 返回 `def search_agent(state)`），LangGraph 将其丢进 `run_in_executor` 线程池，且整个 agent 循环（多轮 LLM+工具）是**一个节点**。`task.cancel()` 只能打在节点边界，**停不掉正在执行的节点**。所谓「物理取消」在当前架构下不存在。

逻辑停止的 stop 延迟 ~5ms，永不 hang。真·中途停 LLM 需要 async 节点改造（design.md §9 前置条件 2），属 steering 任务范围。

### 拒绝的方案

- **stop-and-wait**（原 D2）：`cancel()` + `await task`，等的是节点自然跑完（几秒到 30s+），前端体验差且需超时兜底。

---

## D4: 消息顺序保证 — per-session persist future + 超时降级

**日期**: 2026-10-23（Q2/Q7 确认）
**状态**: 已确认

### 决策

`ChatRunManager` 为每个 session 维护一个 `asyncio.Future`，run 完成持久化（`_drive` finally 的落库调用返回）时 resolve。新 run 的 `start()` 在 service 层 `save_message("user", ...)` **之前** `await` 同会话上一 run 的 future：

```python
await asyncio.wait_for(prev_persist_future, timeout=5.0)
```

超时或 future 带异常 → 打 warning 日志，**继续**落 user 消息（降级，不阻塞对话）。

### 理由

- `save_message` 是 Redis `rpush`，无跨调用顺序保证。
- 串行化点只在「同一 session」，跨 session 不受影响。
- 5s 对一次 Redis `rpush` 是极宽松上限；降级保证一次 Redis 抖动不卡死整个会话。

---

## D5: 「被打断的部分答案」用户可见形态 — 文本前缀标记

**日期**: 2026-10-23（Q4 确认）
**状态**: 已确认

### 决策

部分答案落库时 content 前加固定前缀 `*（生成已中断）*`，前端不做任何改动即可显示。不扩 `ChatStore` 协议（`save_message` 无 `meta` 列，扩它违反「不新增表/字段」约束）。

将来前端做重连时如需结构化判断，再随前端任务一起扩协议。

---

## D6: stop 后事件流语义 — 封存

**日期**: 2026-10-23（Q5 确认）
**状态**: 已确认

### 决策

stop 时刻事件缓冲**定格**：之后底层 task 产出的事件**丢弃**（不进 buffer、不广播）。`GET /runs/{id}/stream?after=N` 只能回放到 stop 时的 END 帧为止。

`_drive` 内部继续消费（让底层自然跑完并拿到完整聚合答案落库），但事件不再对外可见。历史里落库的「部分答案」可能包含 stop 之后生成的文本——这是诚实记录，可接受。

### 拒绝的方案

- **继续缓冲**：用户主动停止后还能看到它继续生成，语义怪异，且订阅者已被 END 帧关闭。

---

## D7: 被 stop 的 run 不落 pending_action

**日期**: 2026-10-23（Q6 确认）
**状态**: 已确认

### 决策

`status=cancelled` 的 run，`_drive` finally 只落部分答案，**跳过** `on_pending_action`。pending_action 是「等待用户确认的动作」，用户已明确打断，留着待确认气泡会干扰。已写入 Redis 的旧 pending_action 由 TTL（600s）自然过期。

**区分**：断连（非 stop）的 run 不受影响——那是「后台跑完」，pending_action 照常落库（R3 要求）。

---

## D8: 「active run」定义 — cancelled 不算 active

**日期**: 2026-10-23（Q8 确认）
**状态**: 已确认

### 决策

`active_for_session()` 只认 `status=RUNNING`。`cancelled` 的 run 即使底层 task 还在跑，也**不算** active。新 `POST /stream` 直接放行，与旧 task 并存（旧 task 只剩「跑完 + 落库部分答案」，消息顺序由 D4 的 persist future 保证）。

若 cancelled 算 active，D2 的 409 会把「打断并插入」卡在旧 task 自然跑完之前——逻辑停止白做。

---

## D9: 进程生命周期边界 — 懒加载 stale 收敛 + shutdown 10s 超时

**日期**: 2026-10-23（Q9 确认）
**状态**: 已确认

### 决策

1. **stale 收敛只做懒加载**：`active_for_session` / `get` 读到 `status=running` 但内存无 run（进程重启过）→ 收敛为 `failed` + 补写「生成已中断」assistant 消息。不做启动时扫描（SCAN 全量 key 成本高，且多数 stale run 永远不会再被查询）。
2. **shutdown 超时**：lifespan 关闭时 `manager.shutdown()` cancel 所有 run task + `gather(return_exceptions=True)`，外包 `asyncio.wait_for(..., timeout=10s)`。超时打日志放弃——FastAPI 关闭不该被 LLM 拖住；进程退出后线程池随之消失，未落库部分由 stale 收敛兜底。

---

## D10: 收尾决策（Q10–Q14）

**日期**: 2026-10-23
**状态**: 已确认

| # | 决策 | 结论 |
|---|---|---|
| Q10 | run_id 到达前端 | SSE 首帧 `meta.run_id` 注入；`GET /sessions/{id}/run` 作刷新后恢复通道 |
| Q11 | `test_streaming.py` 两条既有测试 | 改到 manager 层测 `_drive` 持久化行为；`test_streaming.py` 只断言纯事件产出 |
| Q12 | 断连时工具终态合成 | 不需要。断连≠停止，run 还在跑，工具自然闭合；只有 stop 才合成 aborted 帧 |
| Q13 | `GET /sessions/{id}/run` 归属校验 | 校验 session 归属（session 必须属于当前 JWT user），否则 404 |
| Q14 | 缓冲超限降级 | `GET /runs/{id}/stream?after=N` 检测 `N < buffer_start` → 先发 STATUS 帧提示「部分实时内容已过期，完整回答请查看历史记录」，再从 buffer_start 继续推 |
