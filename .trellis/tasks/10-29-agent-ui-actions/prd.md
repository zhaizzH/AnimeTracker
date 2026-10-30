# Agent 驱动 UI：自然语言导航与图后路由

## Goal

让用户用自然语言完成「需要手动点击多次」的**只读页面操作**——跳页、带筛选跳页、打开某条目详情。页面真的变化，用户看得见，且聊天面板不消失。

技术形态已定稿，见 [.trellis/spec/backend/agent-ui-actions.md](../../spec/backend/agent-ui-actions.md)：图后路由链 + `navigation_emitter` 纯函数节点 + `ui_action` SSE 事件 + 前端筛选 URL 归一化。

## Background

现有 Agent 只能调后端 API（读目录、写收藏），**没有任何驱动前端 UI 的通道**。`/agent` 是独立路由，跳走即卸载聊天组件；`AIAssistantFloat` 虽已挂在 `ClientLayout`，但在任何路由变化时强制关面板。

本任务只覆盖只读导航，**不代填表单、不代点提交**。账户凭据操作（改密码 / 改邮箱 / 换头像）永不进 agent。

## Child Tasks

| Child | 交付物 | 阻塞关系 |
|---|---|---|
| `frontend-url-state` | `AnimeIndex` 筛选 URL 归一化 + 浮层 agent 导航不关面板 | 无，可先做，独立有价值 |
| `ui-action-event` | `ui_action` 事件端到端打通（内部/wire/重放过滤/前端消费/openapi/契约测试） | 无，但前端消费依赖 child 1 的浮层改造才有意义 |
| `navigation-graph` | 图后路由链 + `request_navigation` 工具 + `navigation_emitter` 节点 + 5 个 action 白名单 | 依赖 child 2（事件通道必须先在） |
| `composite-write-navigate` | 复合指令「写入 + 导航」一回合完成，写入走 ADR 0001 两阶段后才导航 | 依赖 child 3 |

## Cross-Child Acceptance Criteria

- [ ] 用户说「给我看 2022 年的番」→ 跳到 `/anime?year=2022`，筛选真的生效，聊天浮层保持打开
- [ ] 用户说「打开我的收藏，在看那一页」→ 跳 `/my-collections?tab=3`
- [ ] 用户说「打开《孤独摇滚》详情页」→ `subjectId` 经权威解析后跳 `/subject/{id}`，模型不得编造 ID
- [ ] 用户说「把这部加入想看，然后打开我的收藏」→ 先出预览 → 用户确认 → 写成功 → 才导航；未确认则不导航
- [ ] SSE 断线重连后**不重复导航**（重放段跳过 `ui_action`）
- [ ] 全部既有测试不回归：`cd backend/agent && uv run pytest`；`cd backend/business && mvn -B clean test`；前端测试基线

## Constraints

- **SSE 是两层枚举**：内部 `AgentEventType`（五值含 END）→ wire `MessageType`（四值）。加 `ui_action` 必须同时改 7 处，漏一处契约测试即红。清单见 spec §6。
- **路由即工具权限边界**这一既有不变量不得破坏：`admin_agent` 无 RAG、`search_agent` 无写工具。导航不得塞进现有 Domain agent。
- `navigation_emitter` 是**纯函数**，不挂 LLM、不挂 prompt、不产 answer 文本。
- `open_subject` 的 `subjectId` 必须来自前序工具已解析的真实 ID，工具不接受标题字符串。
- 不做自由 path，只用固定 action 枚举，服务端构造 URL。
- `navigation_intent` 执行后必须清空，不残留到下一轮。

## Out of Scope

- RAG 外部语料（萌娘百科）那条线，本任务完全冻结，不在此交付。
- 前端内嵌目标页面预览。
- 除 5 个白名单 action 之外的任何页面跳转。
- 导航的 PendingAction 确认（导航可逆、无持久副作用，刻意不走两阶段）。
