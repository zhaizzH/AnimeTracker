# 跨 child 决策记录（2026-10-29 第二轮问答）

> 承接 `design.md`（第一轮 tradeoff）。本轮对四个 child 逐一过细节，
> **推翻了 spec 与 implement.md 中的三处机制设计**，均有探针或源码证据。
> 各 child 的完整方案见各自 `design.md`；本文件只是索引与结论对照。

## 结论对照表

| # | 议题 | 原方案 | 定案 | 证据 |
|---|---|---|---|---|
| D1 | 重放防重复导航 | `subscribe()` 重放段**跳过** `UI_ACTION` | 重放段**照发但补 `meta.replayed=true`**，前端忽略 | 跳帧使前端 `after`（已收帧数）与后端 `run.events` 下标错位，二次重连会重复/遗漏其它事件 |
| D2 | 工具写 state | `Command(update={"navigation_intent": ...})` | `update` 必须同时带 `ToolMessage` | 探针：`ValueError: Expected to have a matching ToolMessage in Command.update` |
| D3 | 外层图读 intent | 「条件边直接读得到」 | `run_domain_agent` 必须**显式回传**该字段 | 探针：`create_agent` 是嵌套图，内层有 intent、外层为 `None`，emitter 不执行 |
| D4 | 写入门控信号 | 读 `state["pending_action"].type` | 读**本回合 TurnState**（ContextVar 共享可变事实） | state 的 pending 是回合开始时的快照，写成功后不更新，会拦掉唯一该放行的导航 |
| D5 | `open_subject` 防编造 ID | 「必须是前序工具已解析的真实 ID」（无强制机制） | emitter 做一次 `GET /subjects/{id}` 回查，失败不发事件 | 只校验 `int > 0` 挡不住 `subjectId=999999` |
| D6 | 前端如何跳页 | 前端按 action+params 构造 URL | 服务端 `meta.path` 直接下发，前端 `navigate(path)` | 避免白名单/键名知识复制两份 |
| D7 | V1 系统提示归属 | 三个 child 都没认领 | `frontend-url-state` 做 UI + 两个 setter，`ui-action-event` 只调用 | 浮层组件在 child 1，UI 归它可避免抢文件 |

## 探针记录

三个探针均在 `backend/agent` 下用真实 `langgraph` / `langchain` 跑通，非纸面推断：

1. **Command 工具**：`create_agent` + 自定义 `wrap_tool_call` middleware。
   结论：middleware 能看到 `Command` 并透传；`update` 无 `ToolMessage` 时工具节点抛 `ValueError`。
2. **嵌套图 state 传播**：外层 `StateGraph` + 内层 `create_agent`，复刻 `run_domain_agent` 的返回形态。
   结论：内层 `latest_state` 有 `navigation_intent`，外层无；补回传后条件边正常进入 emitter。
3. **节点内 emit**：`set_event_sink` 包住 `astream`，节点内 `emit_event`。
   结论：ContextVar 在节点内可见，事件正常入队 → `navigation_emitter` 用 `emit_ui_action` 可行。

## 需要同步更新的既有文档

- `spec/backend/agent-ui-actions.md`：§4.1（Command + ToolMessage + 嵌套回传）、
  §4.2（emitter 回查、meta.path/label）、§4.3（浮层 setter 与调用顺序）、
  §6（重放打标、Java 已实测、契约样本）、§7 错误矩阵、§9 测试清单、§10 Wrong/Correct
- `spec/GLOSSARY.md`：新增 `navigation_emitter` / `Replayed frame` / `TurnState`
- 四个 child 的 `prd.md` 与 `implement.md`：被推翻的句子已就地改写，并各加一份 `design.md`

## 落地顺序提醒

1. `frontend-url-state`（纯前端，独立价值）与 `ui-action-event`（通道）可并行
2. `navigation-graph` 依赖 2；**D3 的回传不做，整条链无效**——这是最容易漏的一步
3. `composite-write-navigate` 依赖 3；工具工厂的 `gated` 开关在 child 3 就要预留，
   且 turn 状态必须**调用时**读取，不能工厂构造期定值

## 新增风险

| 风险 | 缓解 |
|---|---|
| `TurnState` 与 `pending_action_collector` 的 ContextVar 安装点不一致 | 两者都在 `ChatRunManager._drive` 内 set/reset，同一 Token 纪律 |
| `PreviewableAction` 加打标后返回 dict 被改动 | 验收含「三条链路返回 dict 不变」 |
| Managed prompt 只改本地文件，线上 Redis 未更新 | 已写进 child 4 验收清单 |
| 前端 `meta.path` 被污染成外链/`javascript:` | 只接受 `/` 开头且非 `//` 开头，其余丢弃 |
