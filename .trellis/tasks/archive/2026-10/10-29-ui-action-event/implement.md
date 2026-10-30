# 执行计划：`ui_action` 事件端到端打通

> **2026-10-29 修订**：重放方案改为「打 `replayed` 标记」而非「跳帧」（游标错位 bug），
> 前端直接消费服务端下发的 `meta.path`。以 [design.md](./design.md) D1/D4 为准，
> 本文切片 B/C 的旧描述已被覆盖。

## 改动清单（7 处，按依赖顺序）

### 1. `backend/agent/app/chat/events.py`
`AgentEventType` 加 `UI_ACTION = "ui_action"`。`AgentEvent` 复用现有 `meta: dict`，不新增字段。

### 2. `backend/agent/app/api/schemas/sse.py`
`MessageType` 加 `UI_ACTION`。`Content` 不动。

### 3. `backend/agent/app/api/sse.py`
`serialize_agent_event` 走既有 `MessageType(event.type.value)`，无需特判。**实测确认 `meta` 非空时保留**（`exclude_none=True` 下 `meta={}` 会变 None 被剔除，需按现有行为对齐）。

### 4. `backend/agent/app/chat/runs.py`
`subscribe()` 的**重放缓存段**给 `UI_ACTION` 补 `meta.replayed=true`，**不跳帧**：

```python
for event in run.events[start - run.buffer_start:]:
    if event.type is AgentEventType.UI_ACTION:
        yield self._with_run_id(run, self._mark_replayed(event))
        continue
    yield self._with_run_id(run, event)
```

实时订阅段（queue 循环）不打标。`_drive()` 仍入缓冲。
跳帧会让前端 `after`（已收帧数）与后端 `run.events` 下标错位，详见 design D1。

### 5. `frontend/packages/shared/src/hooks/useAgentChat.ts`
`dispatch` switch 加 `case 'ui_action'`：不写正文、不进 tools；`meta.replayed` 为真时直接 break；
否则调 `onUiAction`。hook 选项新增
`onUiAction?: (action: string, params: Record<string, unknown>, label?: string) => void`，
用 ref 持有（同 `apiRef` 的理由）。`SsePayload.meta` 扩 `action/params/path/label/replayed`。

`AgentChat.tsx` 提供实现：`markAgentNavigation()` → `navigate(meta.path)` → `showNavHint(label)`。
`path` 只接受以 `/` 开头且不以 `//` 开头的值（design D4）。

### 6. `docs/spec/openapi.yaml`
`SSEFrame` 的 `type` 枚举加 `ui_action`；`/api/client/agent/stream` 描述同步。

### 7. `backend/agent/tests/contracts/test_sse_contract.py`
契约 enum 加值。`test_all_serializable_event_types_are_covered` / `test_message_type_matches_agent_event_type` 靠传递断言自动覆盖。

## 顺序

1. 先加内部枚举 + wire 枚举 → 跑契约测试，确认传递断言的行为
2. 加 `runs.subscribe` 重放打标 → 写重放测试（含连续两次重连的游标对齐回归）
3. 加前端 case + `onUiAction` → 写前端测试
4. 改 openapi
5. ~~人工核对 Java 透传~~ **已实测**：`AgentSseResponseWriter.java` 逐行原样转发，无白名单，**无需改动**

## TDD 切片

- 切片 A：契约测试先红（新枚举未被 wire 覆盖）→ 加值后绿
- 切片 B：写「缓冲含 ui_action，after 重连时该帧带 `replayed=true` 且帧数与缓冲一致」的失败测试 → 实现打标 → 绿；另加连续两次重连的游标回归
- 切片 C：前端「收到 ui_action 正文不变、onUiAction 被调」失败 → 实现 → 绿

## 验证

```bash
cd backend/agent && uv run pytest
cd ../business && mvn -B clean test   # 若动了 Java 透传
cd ../../frontend && pnpm test
```

## 公共测试缝（已确认，开工前定）

基线：`cd backend/agent && uv run pytest -q` → **862 passed**（2026-10-30 实测）。
全部为既有测试文件，不新建只为本实现服务的钩子。

| 缝 | 位置 | 能捕获 | 捕获不到 |
|---|---|---|---|
| 契约 enum 双向对齐 | `tests/contracts/test_sse_contract.py`（`test_all_serializable_event_types_are_covered` / `test_message_type_matches_agent_event_type`） | 两层枚举漏改任一处、openapi 与代码漂移 | 手写错误但两侧一致的情况 |
| `_sample_events()` 采样 | 同文件 | **只加枚举不加样本会漏掉序列化路径**，必须补带完整 meta 的 `UI_ACTION` 事件 | —— |
| 序列化行为 | `tests/api/test_sse_serialization.py` | `meta` 非空时保留、空 meta 被 `exclude_none` 剔除、结束帧形态不变 | 真实 HTTP 传输 |
| 重放/实时差异 | `tests/agent/test_chat_run_manager.py`（`test_subscribe_replays_from_cursor` 相邻） | 重放段带 `replayed`、实时段不带、**帧数与缓冲下标 1:1（游标不错位）** | 前端 `after` 的真实累加 |
| dispatch 白名单 | `shared/src/hooks/useAgentChat.events.test.tsx`（已存在） | `ui_action` 不落正文、不进 tools、`onUiAction` 被调、参数正确 | 真实路由跳转 |
| 重放帧忽略 | `shared/src/hooks/useAgentChat.replay.test.tsx`（已存在） | 带 `replayed` 的 `ui_action` 不触发回调 | —— |
| 客户端的指纹 | `client/src/test/agent.float.test.tsx`（child 1 已扩到 10 用例） | `markAgentNavigation` / `showNavHint` 效果、`clearNavHint` 作废 | 未覆盖 `onUiAction` 接线（本任务补） |

**两侧都要测的理由**：后端保证「重放段仍下发但打标」，前端保证「带标就不执行」。
任一侧单测都拦不住「两边都以为对方会拦」——必须在两侧各自断言。

**否定断言先建正向基线**（`quality-guidelines.md`）：
测「`ui_action` 不落正文」前，先在同一用例里断言一个 `answer` 帧**确实**落了正文。

## 不做

- 不实现产生事件的业务节点
- 不改 `AgentEvent` 字段结构
- 不在 `_drive()` 写入侧过滤
- 不在重放段跳帧（会错位，见 design D1）
- 不在前端重复实现 action→path 映射（用服务端下发的 `meta.path`）
