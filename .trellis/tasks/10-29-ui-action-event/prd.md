# `ui_action` SSE 事件端到端打通

## Goal

新增第五类 Agent 事件 `ui_action`，从 Python 内部事件一路通到前端回调，并保证**断线重连不重复执行**。

本任务只打通通道，**不实现产生事件的业务节点**（那是 `navigation-graph` 的事）。验收用测试事件驱动。

## Background（源码事实）

SSE 是**两层枚举**，且有传递断言，漏改任一处契约测试即红：

- 内部 `AgentEventType`（`app/chat/events.py`）五值：answer / thinking / function_call / status / **END**
- wire `MessageType`（`app/api/schemas/sse.py`）四值：无 end，结束由 `is_end=true` 表达
- `app/api/sse.py` 用 `MessageType(event.type.value)` 收敛，END 特判成 `is_end=true`
- `tests/contracts/test_sse_contract.py` 的 `test_all_serializable_event_types_are_covered` + `test_message_type_matches_agent_event_type` 通过契约 enum 传递，两侧必然同时变红
- `app/chat/runs.py`：`run.events` 缓冲所有事件，`subscribe(after=cursor)` 原样重放 → **不过滤就会重复导航**
- `useAgentChat.ts` 的 `dispatch` 是白名单 switch，未登记类型不落正文

## Requirements

- 内部 `AgentEventType` 加 `UI_ACTION = "ui_action"`
- wire `MessageType` 同步加值；`Content` 复用现有字段 + `meta` 承载 action/params，不新增顶层字段
- `runs.subscribe()` 在**重放缓存段**给 `UI_ACTION` 补 `meta.replayed=true`（**不跳帧**，跳帧会让前端 `after` 游标与 `run.events` 下标错位）；实时订阅段不打标。详见 [design.md](./design.md) D1
- `ui_action` 仍入 `run.events` 缓冲（保留可回溯性），只在读取侧重放时过滤
- `useAgentChat.ts` 的 switch 加 `case 'ui_action'`：不写正文、不进 tools 列表，调用注入的 `onUiAction` 回调；带 `replayed` 标记的帧直接忽略
- 前端跳页直接用服务端下发的 `meta.path`，不重复实现 action→URL 映射；`meta.label` 驱动浮层系统提示
- `docs/spec/openapi.yaml` 的 `SSEFrame` type 枚举加值
- ~~人工核对 `AgentSseResponseWriter.java`~~ 已实测：逐行原样转发、无类型白名单，**无需改动**

## Acceptance Criteria

- [ ] 内部五值（去 END）与 wire 五值一致，契约测试两侧全绿
- [ ] 实时订阅能收到 `ui_action` 且 `meta` 不被剔除
- [ ] 断线后用 `after=cursor` 重连，缓冲里的 `ui_action` 带 `replayed=true` 下发但前端**不执行**；**连续两次重连不重复不遗漏任何帧**（游标对齐回归）
- [ ] 缓冲截断 warning（`state=warning`）行为不回归
- [ ] 前端收到 `ui_action` 时正文不变、tools 列表不变、`onUiAction` 被调用且参数正确；带 `replayed` 时回调不被调用
- [ ] `meta.path` 为 `javascript:` / 外链时前端不跳转
- [ ] 结束帧形态不变（`type=answer` + `is_end=true` + 空 content）
- [ ] `cd backend/agent && uv run pytest` 全绿；Java 透传已实测无需改动

## Out of Scope

- 不产生真实的 `ui_action`（无业务节点）
- 不做前端实际跳页逻辑（child 1 提供浮层保持，跳页由 `onUiAction` 的具体实现方接入）
- 不改 `AgentEvent` 的字段结构（复用 `meta`）
