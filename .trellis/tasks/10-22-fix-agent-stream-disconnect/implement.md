# 执行计划：chat run 解耦

> 关联 [prd.md](./prd.md) 与 [design.md](./design.md)。
> 原则：每步都有独立可验证的产出；先让最小复现转绿，再逐项清理副作用。

## 步骤 0：固化复现（先做，不改产品代码）

- [ ] 把 `backend/agent/tests/agent/test_repro_disconnect.py` 重命名为 `tests/agent/test_run_disconnect.py`。
- [ ] 保留四个变体作为完整行为矩阵；`test_failing_repro_minimal` 就是 AC1 的载体。
- [ ] 验证：`pytest tests/agent/test_run_disconnect.py -q` → 3 passed, 1 failed（此时仍红，符合预期）。

## 步骤 1：`ChatRunManager` 骨架 + 断连不取消

- [ ] 新增 `app/chat/runs.py`：`RunStatus`、`ChatRun`、`ChatRunManager.start/get/active_for_session/subscribe/shutdown`。
- [ ] `subscribe(after)`：先回放 `events[after:]`，再挂 queue；退订只移除队列。
- [ ] `_drive()`：`async for` 累积缓冲 → 广播；结束写终态；**不**因订阅者退出而取消。
- [ ] 验证：`test_run_disconnect.py` 的 A/D 变体转绿（断连后答案落库、run 仍跑完）。

## 步骤 2：接入 `ChatService` 与 API

- [ ] `ChatService.start_run(...)`：复用现有 prepare 逻辑，产出事件流交给 manager。
- [ ] `stream_chat(...)` 保留为薄壳（`start_run` + `subscribe`），既有测试不受影响。
- [ ] `POST /stream`：响应首帧 meta 带 `run_id`。
- [ ] 新增 `GET /runs/{run_id}/stream?after=N`：校验 `user_id` 归属，不符返回 404。
- [ ] 新增 `GET /sessions/{session_id}/run`：返回当前/最近 run 的 `run_id` + `status`。
- [ ] 验证：`pytest tests/api tests/contracts -q` 全绿（R4 不回归）。

## 步骤 3：Redis run 状态

- [ ] `agent:run:{run_id}` hash 与 `agent:session_runs:{session_id}`，TTL 900s。
- [ ] `active_for_session` 对「status=running 但内存无 run」收敛为 `failed`。
- [ ] 验证：单测覆盖 4 种状态写入/读取、重启悬空收敛。

## 步骤 4：四项副作用

- [ ] 4.1 孤立 user 消息：`_drive()` 的 `finally` 幂等补写 assistant（成功/部分/中断三态）。
- [ ] 4.2 工具中间态：结束时合成 `state=end, result=aborted` 事件。
- [ ] 4.3 pending_action：失败路径不写半成品，正常路径照旧。
- [ ] 4.4 资源：断连不 cancel；`shutdown()` gather 取消；订阅队列退订即移除。
- [ ] 验证：新增 `tests/agent/test_run_side_effects.py`，四项各一条断言。

## 步骤 5：用户主动停止

- [ ] 新增 `POST /runs/{run_id}/stop`：`status=cancelled`，落库已生成部分。
- [ ] 与「刷新断连」区分：断连不退订为取消。
- [ ] 验证：单测 + 前端 `stop()` 行为测试。

## 步骤 6：前端重连

- [ ] `useAgentChat` 记录 `run_id`；挂载/切换会话查 `/sessions/{id}/run`。
- [ ] `running` 时用 `?after=0` 订阅回放，继续增量渲染。
- [ ] `stop()` 走 `/runs/{run_id}/stop`。
- [ ] 验证：`useAgentChat.events.test.tsx` 补重连用例；`npm test`（admin/client/shared）全绿。

## 步骤 7：Java 代理

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

## 待决

- 同会话并发 `POST /stream`：返回 409，还是订阅既有 run？（倾向 409，语义清晰）
- 事件缓冲上限的具体数值（事件数 2000 / 字节 1MB 起步，按实测调）。
- `after` 游标在缓冲被截断时的降级文案。
