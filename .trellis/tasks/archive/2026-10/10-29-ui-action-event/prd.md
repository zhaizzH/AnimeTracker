# `ui_action` SSE 事件端到端打通

> **状态：已完成**（2026-10-30）。9 条 AC 全部达标，详见文末「验收证据」。

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

- [x] 内部五值（去 END）与 wire 五值一致，契约测试两侧全绿
- [x] 实时订阅能收到 `ui_action` 且 `meta` 不被剔除
- [x] 断线后用 `after=cursor` 重连，缓冲里的 `ui_action` 带 `replayed=true` 下发但前端**不执行**；**连续两次重连不重复不遗漏任何帧**（游标对齐回归）
- [x] 缓冲截断 warning（`state=warning`）行为不回归
- [x] 前端收到 `ui_action` 时正文不变、tools 列表不变、`onUiAction` 被调用且参数正确；带 `replayed` 时回调不被调用
- [x] `meta.path` 为 `javascript:` / 外链时前端不跳转
- [x] 结束帧形态不变（`type=answer` + `is_end=true` + 空 content）
- [x] `cd backend/agent && uv run pytest` 全绿；Java 透传已实测无需改动

## Out of Scope

- 不产生真实的 `ui_action`（无业务节点）
- 不做前端实际跳页逻辑（child 1 提供浮层保持，跳页由 `onUiAction` 的具体实现方接入）
- 不改 `AgentEvent` 的字段结构（复用 `meta`）

## 验收证据（2026-10-30）

### 门禁结果

| 门禁 | 结果 |
|---|---|
| `cd backend/agent && uv run pytest -q` | **867 passed**（基线 862，+5；其中 `test_chat_run_manager.py` 新增 4 例、`test_sse_serialization.py` 新增 1 例） |
| `cd backend/agent && uv run pytest tests/contracts -q` | 154 passed |
| `cd backend/agent && uv run ruff check .` | All checks passed |
| `cd frontend && npm test` | shared 12 文件 / 92 用例；client 11 / 72；admin 11 / 81 |
| `cd frontend && npm run typecheck` | 三包 `tsc` 全过 |

### AC → 测试映射

| 验收项 | 测试 |
|---|---|
| 内部（去 END）与 wire 五值一致 | `test_contract_type_enum_has_no_end`、`test_all_serializable_event_types_are_covered`、`test_message_type_matches_agent_event_type` |
| 实时能收 `ui_action` 且 meta 不被剔除 | `test_live_subscription_does_not_mark_ui_action`（断言 `action`/`path`/`label` 仍在，不只 `run_id`）、`test_ui_action_carries_meta_and_empty_content` |
| 重连带 `replayed=true`，两次重连不重不漏 | `test_replay_marks_ui_action_but_keeps_frames_one_to_one`、`test_two_consecutive_reconnects_neither_duplicate_nor_skip` |
| 缓冲截断 warning 不回归 | `test_truncated_buffer_still_warns_first` |
| 前端正文/tools 不变、参数正确、`replayed` 不调 | `useAgentChat.events.test.tsx`（不落正文/不进 tools/参数正确/非法 action 丢弃/params 补空）、`useAgentChat.replay.test.tsx`（`replayed` 不触发回调） |
| `javascript:` / 外链不跳转 | `agent.float.test.tsx::非站内 path 一律丢弃` |
| 结束帧形态不变 | `test_end_event_uses_is_end_marker_not_type_end` |
| Java 透传无需改动 | 源码已核（逐行原样转发，无类型白名单） |

### 变异验证（断言确实能杀）

| 变异 | 转红用例 |
|---|---|
| 重放段改成真跳帧（去掉 `yield _mark_replayed` 只留 `continue`） | `test_replay_marks_ui_action_but_keeps_frames_one_to_one`（`assert 3 == 4`）、`test_two_consecutive_reconnects_neither_duplicate_nor_skip`、`test_truncated_buffer_still_warns_first` |
| 实时段也打 `replayed` | `test_live_subscription_does_not_mark_ui_action`（`assert 'replayed' not in {...}`） |

两次变异后均 `cp` 还原，`git diff --stat` 与还原前一致。变异由 `trellis-check` 执行。

### 交付物

- 契约：`app/chat/events.py`（`AgentEventType.UI_ACTION`）、`app/api/schemas/sse.py`（`MessageType.UI_ACTION`）、`docs/spec/openapi.yaml`（`SSEFrame.type` 五值 + meta 描述）
- 重放：`app/chat/runs.py::_mark_replayed`（`dataclasses.replace` 重建 frozen 实例，帧数 1:1，不跳帧）
- 前端：`shared/src/hooks/useAgentChat.ts`（`UiAction` 接口、`meta` 扩字段、`onUiAction` + ref、`case 'ui_action'`、`replayed` 忽略）、`shared/src/index.ts`（导出类型）
- 接线：`client/src/components/AgentChat.tsx`（`useNavigate` + `isInternalPath` 守卫 + 「标记 → navigate → 提示」）
- 测试：后端 3 文件、前端 4 文件

### 与定案的偏差（已回写 design.md）

1. `onUiAction` 用**单对象** `({action, params, path, label})` 而非位置参数——原签名装不下 `path`，四个位置参数更易错位。
2. `AgentChatProvider` 现在依赖 `useNavigate`，**必须在 Router 内渲染**。生产侧唯一挂载点 `ClientLayout` 天然在内；测试须包 `MemoryRouter`（`agent.conflict` / `agent.notice` 已补）。该约束已写进 `frontend/component-guidelines.md`。

### 顺手修掉的 spec 漂移

实现让 8 处 spec 说法失效，全部已改：
`agent-guidelines.md`（内部六值/wire 五值 + `ui_action` meta 契约 + 「只加枚举不加样本等于没测」）、`contract-tests.md`（五值 + 3 行错误矩阵）、`agent-ui-actions.md`（状态行、测试文件路径纠正）、`GLOSSARY.md`（`AgentEvent` 词条、`Replayed frame` 限定「仅 `ui_action`」）、`guides/cross-layer-thinking-guide.md`（四值→五值）、`frontend/component-guidelines.md`（Router 挂载约束）。
