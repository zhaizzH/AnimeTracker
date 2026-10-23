# 执行计划：chat run 解耦

> 关联 [prd.md](./prd.md) 与 [design.md](./design.md)。
> 原则：每步都有独立可验证的产出；先让最小复现转绿，再逐项清理副作用。

## 进度（截至 commit `876e4fb2`）

| 步骤 | 状态 | 提交 | 验证 |
|---|---|---|---|
| 0 固化复现 | ✅ | `e6f58d60` | 3 passed, 1 xfailed |
| 1 Manager 骨架 + 断连不取消 | ✅ | `327772b1` | 829 passed |
| 2 接入 service 与 API | ✅ | `8ca0d7b2` | 837 passed |
| 3 Redis run 状态 | ✅ | `6cb7afe0` | 845 passed |
| 4 四项副作用 | ✅ | `737a195c` | 853 passed |
| 5 用户主动停止 | ✅ | `737a195c`（API 在 `8ca0d7b2`） | `test_run_api.py` + `test_run_side_effects.py` |
| 6 前端重连 | 本次不做 | | |
| 7 Java 代理 | 本次不做 | | |
| 8 收尾 | ✅（后端部分） | `876e4fb2` | 853 passed，契约子集 146 passed |

## 步骤 0：固化复现（**已完成**，commit `e6f58d60`）

- [x] 把 `backend/agent/tests/agent/test_repro_disconnect.py` 重命名为 `tests/agent/test_run_disconnect.py`。
- [x] 保留四个变体作为完整行为矩阵；`test_answer_survives_client_disconnect` 就是 AC1 的载体。
- [x] 缺陷用例以 `xfail(strict=True)` 登记（项目约定）：当前 `3 passed, 1 xfailed`，CI 保持绿。
- [x] 验证：`pytest tests/agent/test_run_disconnect.py -q` → 3 passed, 1 xfailed。

> 注意：一修复，D 变体会因 strict 模式变成 XPASS(failed)；这是故意的，强制在同一次改动里删除标记。

## 步骤 1：`ChatRunManager` 骨架 + 断连不取消（**已完成**，commit `327772b1`）

- [x] 新增 `app/chat/runs.py`：`RunStatus`、`ChatRun`（含 `buffer_start`、`persist_future`）、`ChatRunManager.start/get/latest_for_session/active_for_session/stop/subscribe/shutdown`。
- [x] `start()`：在 `create_task` **之前**用 `uuid` 起 run 并建 `persist_future`；**Q3 修正**：`pending_action_collector` 改由 `_drive` 自己 set/reset——`start()` set 的 token 无法在另一个任务里 reset（`ValueError: was created in a different Context`）。
- [x] `subscribe(after)`：先回放 `events[max(after, buffer_start):]`，再挂 queue；`after < buffer_start` 时先发 STATUS 降级提示帧（Q14）；退订只移除队列。
- [x] `_drive()`：`async for` 累积 `aggregated_answer`/`used_tools` → 缓冲 → 广播；结束写终态 + resolve `persist_future`；**不**因订阅者退出而取消。
- [x] `_drive` finally：调 `on_answer_completed` / `on_pending_action`（D1 回调提升）+ reset contextvar token + resolve persist_future。
- [x] `active_for_session`：只认 `status=RUNNING`（D8）。
- [x] `shutdown()`：cancel + gather + `wait_for(timeout=10s)`（D9）。
- [x] `stop()`（D3 逻辑停止）：标记 cancelled + 合成工具终态（R3）+ 唯一 END 帧（R4）+ 立即返回，不 cancel 底层 task。封存（D6）：stop 后事件不再入缓冲/广播，但仍聚合答案以便落库。
- [x] 同批完成 D5（部分答案 `*（生成已中断）*` 前缀，仅在没有显式 `error_message` 时加）、D7（被 stop 的 run 跳过 pending_action）、Q12（断连不合成工具终态）。
- [x] `stream_agent_events` 改为纯事件生产者（D1），异常路径补显式 `STATUS(state="error")` 帧。
- [x] 验证：`pytest tests/agent/test_chat_run_manager.py` 11 passed；`test_run_disconnect.py` 4 passed（xfail 已转正，AC1）；全量 829 passed。

## 步骤 2：接入 `ChatService` 与 API（**已完成**，commit `8ca0d7b2`）

- [x] `ChatService.start_run(...)`：`_prepare()` 返回 `(events, on_answer_completed, on_pending_action)`，交给 manager；`stream_chat` 保留为薄壳（`start_run` + `subscribe`）。
- [x] D4：`save_message("user")` 前 `await wait_for(prev.persist_future, 5s)`，超时/异常降级继续（`PERSIST_WAIT_SECONDS`）。
- [x] `POST /stream`：首帧 `meta.run_id`（Q10，由 `_subscription` 的 `_with_run_id` 统一补）；同会话 active run → 409 `{ active_run_id, status, capabilities: ["interrupt"] }`（D2）。
- [x] 新增 `GET /runs/{run_id}/stream?after=N`：校验 `user_id` 归属，不符返回 404（不暴露存在性）。
- [x] 新增 `GET /sessions/{session_id}/run`：校验 session 归属（Q13），返回 `run_id` + `status`。
- [x] `main.py`：lifespan 创建 `ChatRunManager` 并挂 `app.state.chat_runs`；关闭时 `await chat_runs.shutdown()`。
- [x] 验证：`tests/api/test_run_api.py` 7 passed；全量 837 passed（R4 不回归）。

## 步骤 3：Redis run 状态（**已完成**，commit `6cb7afe0`）

- [x] `agent:run:{run_id}` hash（session_id/user_id/status/event_count）与 `agent:session_runs:{session_id}`，TTL 900s。
- [x] 端口 `app/chat/run_state.py`（`RunState` + `RunStateStore` Protocol）；适配器 `app/adapters/redis/run_state.py`。写失败只记日志，不阻塞 run（投影可丢）。
- [x] `ChatRunManager` 接受可选 `run_state_store`；`start`/`stop`/`_drive` 收尾写投影。
- [x] `resolve_session_run(session_id)`：内存优先；否则读投影，`status=running` 但内存无此 run → 收敛为 `failed`（D9）并回写。
- [x] `GET /sessions/{id}/run` 改走 `resolve_session_run`，跨进程可读；`main.py` 装配 `RedisRunStateStore`（独立 Redis 客户端）。
- [x] 验证：`tests/adapters/redis/test_run_state.py` 5 passed + manager 3 条收敛用例；全量 845 passed。

## 步骤 4：四项副作用（**已完成**，commit `737a195c`）

- [x] 4.1 孤立 user 消息：`_drive()` 的 `finally` 幂等落库。**实现时修正了判定**：
  - 有内容且非 DONE（且无显式错误文案）→ 加 `*（生成已中断）*` 前缀（D5）；
  - 非 DONE 且无任何内容 → 落 `*（生成已中断）*`，不留空串；
  - DONE 且无内容 → **不落库**（原计划无条件落库会制造空消息噪声）。
- [x] 4.2 工具中间态：stop 时 `_finish` 合成未闭合工具的 `state=end, result=aborted` 帧（D3）；断连不合成（Q12，有测试钉住）。
- [x] 4.3 pending_action：正常路径 `_drive` finally 里 `get_pending_action_event()` + 回调；被 stop 的 run 跳过（D7）；落库失败发 STATUS/error（不写半成品）。
- [x] 4.4 资源：断连不 cancel；订阅队列退订即从 `subscribers` 摘除；`shutdown()` 取消 + **`asyncio.wait(timeout=10s)`**。
- [x] **发现并修复的真 bug（D9 保护失效）**：原 `wait_for(gather(...))` 在超时时会二次 cancel 并等取消完成；同步节点跑在 LangGraph executor 里对 cancel 免疫，二次等待无上限，超时保护反而变成陷阱。改用 `asyncio.wait`。
- [x] 验证：`tests/agent/test_run_side_effects.py` 8 passed；全量 853 passed。

## 步骤 5：用户主动停止（逻辑停止，D3）（**已完成**）

- [x] `POST /runs/{run_id}/stop`：归属校验 → 标记 `cancelled` + 合成工具终态帧 + END 帧 + **立即返回 200**（不 cancel 底层 task），幂等。
- [x] 底层 task 自然跑完后 `_drive` finally 落库部分答案（D5 前缀），跳过 pending_action（D7）。
- [x] 封存（D6）：stop 后事件缓冲定格，之后产出的事件丢弃（但仍聚合答案以便落库）。
- [x] 与「刷新断连」区分：断连只退订，不改变 run 状态，也不合成工具终态（Q12）。
- [x] 验证：`test_stop_returns_immediately_and_marks_cancelled`、`test_stop_synthesises_aborted_tool_frame_and_single_end`、`test_stop_seals_event_stream`、`test_cancelled_run_skips_pending_action`、`test_each_run_persists_exactly_once`、`test_run_api.py::test_stop_endpoint_returns_200_and_marks_cancelled`。

## 步骤 6：前端重连（**本次不做**，留待后续）

- [ ] `useAgentChat` 记录 `run_id`；挂载/切换会话查 `/sessions/{id}/run`。
- [ ] `running` 时用 `?after=0` 订阅回放，继续增量渲染。
- [ ] `stop()` 走 `/runs/{run_id}/stop`。
- [ ] 验证：`useAgentChat.events.test.tsx` 补重连用例；`npm test`（admin/client/shared）全绿。

## 步骤 7：Java 代理（**本次不做**，留待后续）

- [ ] `AgentApiPaths` 加 `RUNS_STREAM` / `SESSION_RUN` / `RUN_STOP`。
- [ ] `ClientAgentController`、`AdminAgentController` 三个新路由。
- [ ] 验证：`mvn -B -pl agent test`（或对应模块）Controller 测试通过。

## 步骤 8：收尾（**后端部分已完成**，commit `876e4fb2`）

- [x] `grep -rn "DEBUG-a4f2" backend/agent frontend/` → 无结果。
- [x] 全量：`pytest backend/agent/tests -q` → 853 passed；`pytest tests/contracts -q` → 146 passed。
- [x] spec 回写：
  - `agent-guidelines.md`：改「客户端断开」口径（退订而非 CancelledError）；新增 Scenario「Chat run 生命周期与重连」（断连≠取消、落库单一责任人、每 run 恰好一条 assistant、唯一 `is_end`、stop=逻辑停止、封存、409、归属 404、重启不恢复）。
  - `contract-tests.md`：测试套件表补 `tests/api/test_run_api.py`；Contracts 新增「Run 生命周期契约」四路由接口事实；显式声明 `openapi.yaml` 暂未收录（它记录 Java 对外层路径）及补齐时要一起动的三处。
- [x] 提交信息写清「根因：收尾职责与读者绑定；修复：run 解耦」。
- [ ] **剩余**：前端三包测试未跑（本次未改前端，R4 待步骤 6 一并验证）。

### 交付边界（明确未做）

- 步骤 6 前端重连、步骤 7 Java 代理均未做。生产端解耦已生效：即使前端刷新时 abort，答案照常落库，刷新后从历史可见。
- 因此 `GET /runs/{id}/stream`、`GET /sessions/{id}/run`、`POST /runs/{id}/stop` 在 Spring 代理补齐前浏览器无法直达（只能直连 `:8090`）。

### 步骤 8 的执行清单（含验证命令）

1. `grep -rn "DEBUG-a4f2" backend/ frontend/` → 应为空。
2. `cd backend/agent && .venv/Scripts/python -m pytest tests -q` → 当前 853 passed。
3. spec 回写两处：
   - `spec/agent-guidelines.md`（流式章节）：run 生命周期、断连=退订、stop=逻辑停止、重启不恢复。
   - `spec/contract-tests.md`：新增三个路由的契约（`GET /runs/{id}/stream`、`GET /sessions/{id}/run`、`POST /runs/{id}/stop`）。
4. 检查 design.md 与实现是否漂移（已知偏差已记在本文步骤 4：空答案不落库、`asyncio.wait` 替代 `wait_for`）。
5. 最终提交信息模板：

   ```
   fix(agent): 刷新丢弃已生成回答

   根因：收尾职责绑在读者上——stream_agent_events 的 on_answer_completed 位于消费循环之后，
   客户端断连触发 GeneratorExit 时整段跳过，已上屏的回答从未落库。

   修复：每条对话变成有独立生命周期的 run（asyncio.Task），SSE 降级为订阅者，
   断连只退订。落库统一由 _drive 的 finally 负责。
   ```

## 回滚点

- 每步独立提交，可单独 revert。
- 步骤 1–2 是核心，若步骤 2 的 API 变更引发回归，回退到步骤 1 的 manager 仍可单测通过。
- 步骤 3 的投影层是可选的（`run_state_store=None` 时纯内存），删掉它最差退化为「重启后看不到 run 状态」，不影响断连不丢答案这个主目标。
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
