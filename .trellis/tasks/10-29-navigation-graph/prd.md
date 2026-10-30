# 图后路由链与 `navigation_emitter`

## Goal

让 Domain agent 能表达「跳转到某页」的意图，由图的一条**确定性后路由边**交给纯函数节点翻译成 `ui_action` 发出。

**阻塞**：依赖 `ui-action-event` 先完成（事件通道必须已存在）。

## Background

现状 `app/agent/graph.py` 是单次路由无环：`START → gateway_router → 单个 Domain agent → END`。`_route_from_gateway` 对非法 `route_target` 直接 `ValueError`。

本任务加一条后路由边，**不改 ReAct 内部、不改 gateway 的输出契约**（仍是单标签 `{"route_target": str}`）。

## Requirements

- `AgentState` 新增 `navigation_intent` 字段（可选），承载 `{action, params}`
- 新增 `request_navigation` 工具：**纯 state 写入，零 IO，不发事件、不调 LLM**；参数经 Pydantic 校验，非法值返回错误 dict 且不写 state
- 工具通过 LangGraph `Command(update={"navigation_intent": ..., "messages": [ToolMessage(...)]})` 写 state。**必须带 ToolMessage**，实测只写 intent 会抛 `ValueError`。**不是**返回普通 dict；**也不走** `emit_pending_action_*` ContextVar（那是 PendingAction 持久化通道）
- **嵌套图回传**：`create_agent` 是嵌套图，`Command` 只写内层 state。`run_domain_agent` 必须显式把 `navigation_intent` 放进返回值，否则外层条件边永远读不到（探针实测，见 [design.md](./design.md) D1）
- 工具注册到**全部三个 Domain agent**（search / discover / recommend）：纯导航请求（「打开我的收藏」）会被路由到 `search_agent`，那里也必须有工具。**写工具**的权限边界不变，仍只在 `recommend_agent`
- 新增 `navigation_emitter` 节点：**纯函数**，读 intent → 白名单映射成 path+query → `emit_ui_action` → 返回 `{"navigation_intent": None}` 清空
- `navigation_emitter` **不产 answer 文本**（静默），不挂 LLM / prompt / 业务工具
- 图加条件边：任一 Domain agent 结束后，`navigation_intent` 非空则进 emitter，否则直接 END
- admin 路径不受影响
- 一期 5 个 action 白名单，服务端构造 URL，**不做自由 path**

### action 白名单

| action | 参数 | 目标 |
|---|---|---|
| `open_anime_index` | `q?` `tags?` `year?` `weekday?` `sort?` `order?` `page?` | `/anime?...`（`tags` → 重复 `tag` 键） |
| `open_schedule` | `year?` `quarter?` `tab?` | `/schedule?...` |
| `open_subject` | `subjectId`（必填） | `/subject/{id}` |
| `open_collections` | `tab?` `page?` | `/my-collections?...` |
| `open_profile` | 无 | `/profile` |

- `open_subject` 的 `subjectId` 必须是**前序工具已解析的真实 ID**；工具不接受标题字符串。**emitter 额外做一次权威回查**（`GET /subjects/{id}`），回查失败则不发事件、只清空 intent——只校验 `int > 0` 挡不住编造的 ID

## Acceptance Criteria

- [ ] `navigation_intent` 为空时不进 emitter，直接 END
- [ ] 三个 Domain agent 均注册了 `request_navigation`；`admin_agent` 仍无
- [ ] 白名单外 action 被拒绝；`open_subject` 缺 `subjectId` 被拒绝
- [ ] 参数非法（year 越界、sort 非枚举值）时工具返回错误且不写 state
- [ ] emitter 执行后 `navigation_intent` 清空，下一轮不残留
- [ ] emitter 不产生任何 `answer` 事件
- [ ] `open_subject` 回查失败时不发 `ui_action`，且 intent 仍被清空
- [ ] `ui_action.meta` 含 `path` 与 `label`（前端直接 `navigate(path)`，不重复实现映射）
- [ ] 服务端构造的 URL 与前端路由实际参数名一致（对照 `AnimeIndex` / `Schedule` / `MyCollections` 的 `useSearchParams` 键名）
- [ ] `uv run pytest` 全绿，新增 `test_navigation_emitter.py` / `test_graph_post_routing.py` / `test_request_navigation_tool.py` / `test_run_domain_agent.py`（锁嵌套图回传）

## Out of Scope

- 不在 `recommend_agent` 做写入门控与复合指令编排（child `composite-write-navigate`）
- 不做导航的 PendingAction 确认
- 不让 emitter 调 LLM 生成「已为你打开」之类的话术
- 不扩展到 5 个之外的 action
