# 修复 agent 对话断连：解耦流式生产端与请求生命周期

## Goal

刷新页面后 agent 对话中断且答案从未落库。把流式生产端从 HTTP 请求生命周期中解耦，使断连后后台继续跑完并正确落库，并清理孤立 user 消息、工具中间态、pending_action 丢失、producer 取消四项副作用。

## 现象

用户在客户端/管理端与 agent 对话时刷新页面，对话直接终止：

- 前端 `useAgentChat` 卸载时 `ab.current?.abort()`，`POST /stream` 的 fetch 连接断开。
- 后端 `stream_agent_events` 收到 `GeneratorExit`，收尾逻辑整段跳过。
- 结果是**已经流到屏幕上的回答从未落库**，刷新后该会话历史里只剩孤立的 user 消息。

## 已确认的根因（Phase 1–4，已插桩验证）

1. `backend/agent/app/chat/streaming.py`：`on_answer_completed`（assistant 落库）写在 `while` 消费循环**之后**。断连触发 `GeneratorExit` 时该段不执行，`aggregated_answer` 直接丢失。
2. 同文件 `finally: producer.cancel()`：断连时主动取消生产端，LangGraph 也停在中途，无法“后台跑完”。
3. 插桩实测时序：`aclose()` 先返回，随后 `producer` 才收到 `CancelledError`。即断连 = 前端掉线 **且** 后端连人带活一起停。

结构性根源：`tests/contracts/test_sse_contract.py` 明确写「`stream_agent_events` 本身是流的唯一收尾责任人」，**收尾职责与“有人在读”绑定**。

## 最小复现（已入库，修复后转正为回归测试）

`backend/agent/tests/agent/test_repro_disconnect.py`：

```bash
cd backend/agent && .venv/Scripts/python.exe -m pytest tests/agent/test_repro_disconnect.py -q
# 1 failed, 3 passed in 0.19s
# test_failing_repro_minimal: assert [] == ['A']
```

四个变体固定了因果：

| 变体 | 场景 | 结果 |
|---|---|---|
| A | 挂起流程 + 中途断连 | `[]`（用户症状） |
| B | 快速完成 + 读完 | `['A']`（正常路径 OK） |
| C | 快速完成 + 中途断连 | `[]`（断连即丢） |
| D | 断言「断连后应落库」 | 红 |

## Requirements

### R1 生产端与请求生命周期解耦（核心）

- 流式执行（workflow 运行 + 事件产出 + 落库）不得因 HTTP 客户端断连而取消。
- HTTP 响应（SSE）降级为**订阅者**：断连只停止该订阅者推送，不影响生产端。
- 生产端必须持有独立的生命周期，不依赖生成器被读取才推进。

### R2 断连后跑完并落库

- 刷新后重新打开同一会话，历史中能看到**完整** assistant 回答。
- 落库时机不依赖 SSE 连接存活。

### R3 清理四项断连副作用

- **孤立 user 消息**：`user` 已落库而 `assistant` 缺失的状态不得长期存在；生产端跑完后必须补齐 assistant 消息（或明确标记）。
- **工具调用中间态**：断连时处于 `running` 的工具不得永久停留在 `running`；跑完/失败/中止须有终态。
- **pending_action 丢失**：`save_pending_action`（TTL 600s）不得因断连被跳过。
- **资源泄漏 / producer 取消**：不再无差别 `cancel()`；底层 LLM/HTTP 连接与 event sink / pending_action collector 的 contextvar 必须被正确清理。

### R4 现有契约不得回归

- `tests/contracts/test_sse_contract.py`：恰好一个 `is_end` 帧、且必须是最后一帧；错误路径同样。
- `tests/api/test_sse_serialization.py`：media type 与响应头。
- 前端 `useAgentChat.events.test.tsx` / `useAgentChat.enabled.test.tsx` 行为不变。

## Acceptance Criteria

- [ ] AC1: 最小复现 `test_repro_disconnect.py` 全绿（断连后答案落库）。
- [ ] AC2: 生产端在消费者断连后仍跑完；有测试证明生产端未被取消。
- [ ] AC3: 断连后从历史能读到完整 assistant 回答（端到端或集成层验证）。
- [ ] AC4: 四项副作用各有测试覆盖：孤立 user 消息补齐、工具终态、pending_action 保留、无 producer 取消/资源清理。
- [ ] AC5: `pytest backend/agent/tests` 全绿（含 contracts 与 api），前端 admin/client/shared 测试全绿。
- [ ] AC6: `test_streaming.py` 与 `test_sse_contract.py` 的收尾契约在新结构下仍成立。

## Constraints

- 不引入常驻进程外部队列基础设施（仓库既有 offline-jobs 是 CLI + 明确退出码），若需要后台执行须在现有 FastAPI 进程内以 `asyncio.Task` 实现，并说明重启丢失的边界。
- Redis store 是既有持久化层（`agent:session:*` / `agent:messages:*`），不新增数据库表。
- 遵守 `.trellis/spec/backend/agent-guidelines.md` 的分层：节点不读环境变量、不建基础设施客户端。
- 前端 `useAgentChat` 的公开 API 尽量不变（`messages`/`streaming`/`send`/`stop`/`select`/`create`/`remove`）。

## Open Questions

- 生产端生命周期边界：进程内 `asyncio.Task`（重启丢失）是否可接受？还是需要 run 状态写 Redis 以支持重启后恢复？（倾向进程内 + Redis 记录终态，需确认）
- 订阅语义：刷新后重连同一 run 继续接收增量，还是等 run 结束后从历史一次性读出？（两者工作量和体验差异大）
- 前端是否需要感知「run 仍在后台进行」并在 UI 上体现（如“仍在生成…”）？

## Notes

- 最小复现测试文件当前是临时文件，修复后应转为正式回归测试并移除 `repro` 命名。
- 插桩前缀 `[DEBUG-a4f2]` 仅存在于临时脚本，未进入仓库代码。
