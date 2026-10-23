# 执行计划：chat run 解耦

> 关联 [prd.md](./prd.md) 与 [design.md](./design.md)。
> 原则：每步都有独立可验证的产出；先让最小复现转绿，再逐项清理副作用。

## 步骤 0：固化复现（**已完成**，commit `e6f58d60`）

- [x] 把 `backend/agent/tests/agent/test_repro_disconnect.py` 重命名为 `tests/agent/test_run_disconnect.py`。
- [x] 保留四个变体作为完整行为矩阵；`test_answer_survives_client_disconnect` 就是 AC1 的载体。
- [x] 缺陷用例以 `xfail(strict=True)` 登记（项目约定）：当前 `3 passed, 1 xfailed`，CI 保持绿。
- [x] 验证：`pytest tests/agent/test_run_disconnect.py -q` → 3 passed, 1 xfailed。

> 注意：一修复，D 变体会因 strict 模式变成 XPASS(failed)；这是故意的，强制在同一次改动里删除标记。

## 步骤 1：`ChatRunManager` 骨架 + 断连不取消

- [ ] 新增 `app/chat/runs.py`：`RunStatus`、`ChatRun`（含 `buffer_start`、`persist_future`）、`ChatRunManager.start/get/active_for_session/stop/subscribe/shutdown`。
- [ ] `start()`：create_task **前** set contextvar（event_sink + pending_action_collector），token 传 `_drive`（Q3）。
- [ ] `subscribe(after)`：先回放 `events[after:]`，再挂 queue；`after < buffer_start` 时先发 STATUS 降级提示帧（Q14）；退订只移除队列。
- [ ] `_drive()`：`async for` 累积 `aggregated_answer`/`used_tools` → 缓冲 → 广播；结束写终态 + resolve `persist_future`；**不**因订阅者退出而取消。
- [ ] `_drive` finally：调 `on_answer_completed` / `on_pending_action`（D1 回调提升）+ reset contextvar token + resolve persist_future。
- [ ] `active_for_session`：只认 `status=RUNNING`（D8）；stale 懒加载收敛（D9）。
- [ ] `shutdown()`：cancel + gather + `wait_for(timeout=10s)`（D9）。
- [ ] 验证：`test_run_disconnect.py` 的 A/D 变体转绿（断连后答案落库、run 仍跑完）。

## 步骤 2：接入 `ChatService` 与 API

- [ ] `ChatService.start_run(...)`：复用现有 prepare 逻辑；`save_message("user")` 前 `await wait_for(prev.persist_future, 5s)`（D4），超时降级。
- [ ] `stream_chat(...)` 保留为薄壳（`start_run` + `subscribe`），既有测试不受影响。
- [ ] `POST /stream`：响应首帧 `meta.run_id`（Q10）；同会话 active run → 409 `{ active_run_id, status, capabilities: ["interrupt"] }`（D2）。
- [ ] 新增 `GET /runs/{run_id}/stream?after=N`：校验 `user_id` 归属，不符返回 404。
- [ ] 新增 `GET /sessions/{session_id}/run`：校验 session 归属（Q13），返回 `run_id` + `status`。
- [ ] 验证：`pytest tests/api tests/contracts -q` 全绿（R4 不回归）。

## 步骤 3：Redis run 状态

- [ ] `agent:run:{run_id}` hash 与 `agent:session_runs:{session_id}`，TTL 900s。
- [ ] `active_for_session` 对「status=running 但内存无 run」收敛为 `failed`。
- [ ] 验证：单测覆盖 4 种状态写入/读取、重启悬空收敛。

## 步骤 4：四项副作用

- [ ] 4.1 孤立 user 消息：`_drive()` 的 `finally` 幂等补写 assistant（成功/部分/中断三态）；部分/中断态加 `*（生成已中断）*` 前缀（D5）。
- [ ] 4.2 工具中间态：stop 时合成未闭合工具的 `state=end, result=aborted` 帧（D3）；断连不合成（Q12）。
- [ ] 4.3 pending_action：正常路径 `_drive` finally 里 `get_pending_action_event()` + 回调（Q3）；被 stop 的 run 跳过（D7）；失败路径不写半成品。
- [ ] 4.4 资源：断连不 cancel；`shutdown()` cancel + gather + 10s 超时（D9）；订阅队列退订即移除。
- [ ] 验证：新增 `tests/agent/test_run_side_effects.py`，四项各一条断言。

## 步骤 5：用户主动停止（逻辑停止，D3）

- [ ] 新增 `POST /runs/{run_id}/stop`：标记 `cancelled` + 合成工具终态帧 + END 帧 + **立即返回 200**（不 cancel 底层 task）。
- [ ] 底层 task 自然跑完后 `_drive` finally 落库部分答案（D5 前缀），跳过 pending_action（D7）。
- [ ] 封存（D6）：stop 后事件缓冲定格，之后产出的事件丢弃。
- [ ] 与「刷新断连」区分：断连不退订为取消。
- [ ] 验证：单测（stop 延迟 ~5ms、部分答案落库带前缀、pending_action 不落）+ 前端 `stop()` 行为测试。

## 步骤 6：前端重连（**本次不做**，留待后续）

- [ ] `useAgentChat` 记录 `run_id`；挂载/切换会话查 `/sessions/{id}/run`。
- [ ] `running` 时用 `?after=0` 订阅回放，继续增量渲染。
- [ ] `stop()` 走 `/runs/{run_id}/stop`。
- [ ] 验证：`useAgentChat.events.test.tsx` 补重连用例；`npm test`（admin/client/shared）全绿。

## 步骤 7：Java 代理（**本次不做**，留待后续）

- [ ] `AgentApiPaths` 加 `RUNS_STREAM` / `SESSION_RUN` / `RUN_STOP`。
- [ ] `ClientAgentController`、`AdminAgentController` 三个新路由。
- [ ] 验证：`mvn -B -pl agent test`（或对应模块）Controller 测试通过。

## 步骤 8：收尾

- [ ] `grep -rn "DEBUG-a4f2"` → 无结果。
- [ ] 全量：`pytest backend/agent/tests`、前端三包测试。
- [ ] spec 回写：`agent-guidelines.md` 流式章节补 run 生命周期与「重启不恢复」边界；`contract-tests.md` 补 run 契约。
- [ ] 提交信息写清「根因：收尾职责与读者绑定；修复：run 解耦」。

## 回滚点

- 每步独立提交，可单独 revert。
- 步骤 1–2 是核心，若步骤 2 的 API 变更引发回归，回退到步骤 1 的 manager 仍可单测通过。
- 前端（步骤 6）与 Java（步骤 7）可独立回退，后端 run 化不依赖它们。

## 范围（2026-10-22 定）

- **本次只做后端**（步骤 0–5 + 步骤 8 的后端部分）。
- 前端重连（步骤 6）与 Java 代理（步骤 7）**本次不做**：生产端解耦后，即使前端仍在刷新时 abort，答案也照常落库，刷新后从历史即可看到完整回答。前端增量回放与 Java 路由留作后续。
- 后果：`GET /runs/{run_id}/stream` 等新路由在 Spring 代理未加之前浏览器**无法直达**（前端只请求 `/api/{client,admin}/agent/...`）。后端可先交付并用 `TestClient` 验证，但端到端体验要等 Java 代理补齐。
- 「assistant 消息带 meta」已否决（Q4）：`ChatStore.save_message` 无 meta 列，改用文本前缀（D5）。将来前端重连如需结构化判断，随前端任务扩协议。

## 待决（已定）

- 同会话并发 `POST /stream`：409 + 用户显式选择（D2）。
  - 打断+插入 = `stop` 旧 run（逻辑停止 D3，落库部分答案 D5）+ 新 `POST /stream`（顺序由 persist future D4 保证），本次范围内。
  - 真 steering（中途注入指令）= **不在本次范围**，需先重构执行模型（checkpointer + async 节点 + 拆线程池绕路），见 design.md §9。
- 事件缓冲上限：事件数 2000 / 字节 1MB 起步，按实测调。
- `after` 游标在缓冲被截断时的降级：先发 STATUS 提示帧「部分实时内容已过期，完整回答请查看历史记录」，再从 buffer_start 继续推（Q14）。
