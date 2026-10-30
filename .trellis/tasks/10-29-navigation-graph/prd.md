# 图后路由链与 `navigation_emitter`

> **状态：已完成**（2026-10-30）。10 条 AC 全部达标，详见文末「验收证据」。

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

- [x] `navigation_intent` 为空时不进 emitter，直接 END
- [x] 三个 Domain agent 均注册了 `request_navigation`；`admin_agent` 仍无
- [x] 白名单外 action 被拒绝；`open_subject` 缺 `subjectId` 被拒绝
- [x] 参数非法（year 越界、sort 非枚举值）时工具返回错误且不写 state
- [x] emitter 执行后 `navigation_intent` 清空，下一轮不残留
- [x] emitter 不产生任何 `answer` 事件
- [x] `open_subject` 回查失败时不发 `ui_action`，且 intent 仍被清空
- [x] `ui_action.meta` 含 `path` 与 `label`（前端直接 `navigate(path)`，不重复实现映射）
- [x] 服务端构造的 URL 与前端路由实际参数名一致（对照 `AnimeIndex` / `Schedule` / `MyCollections` 的 `useSearchParams` 键名）
- [x] `uv run pytest` 全绿，新增 `test_navigation_emitter.py` / `test_graph_post_routing.py` / `test_request_navigation_tool.py` / `test_run_domain_agent.py`（锁嵌套图回传）

## Out of Scope

- 不在 `recommend_agent` 做写入门控与复合指令编排（child `composite-write-navigate`）
- 不做导航的 PendingAction 确认
- 不让 emitter 调 LLM 生成「已为你打开」之类的话术
- 不扩展到 5 个之外的 action

## 验收证据（2026-10-30）

### 门禁结果

| 门禁 | 结果 |
|---|---|
| `cd backend/agent && uv run pytest -q` | **899 passed**（基线 867，+32） |
| `cd backend/agent && uv run pytest tests/contracts -q` | 156 passed（154+2，见下） |
| `cd backend/agent && uv run ruff check .` | All checks passed |

契约 154→156 不是削弱：`test_http_contract.py` 对 `CALL_SITES` 有两处参数化，新增 1 个出站调用点各 +1。

### AC → 测试映射

| 验收项 | 测试 |
|---|---|
| intent 空不进 emitter 直接 END | `test_no_intent_goes_straight_to_end` |
| 三个 Domain agent 都注册、admin 仍无 | `test_each_domain_agent_reaches_emitter[search_agent/discover_agent/recommend_agent]`（parametrize，各自独立断言）、`test_admin_path_never_touches_emitter` |
| 白名单外 action / 缺 `subjectId` 拒绝 | `test_unknown_action_is_rejected_without_writing_state`、`test_open_subject_requires_subject_id` |
| 参数非法不写 state | year 越界 / sort 非枚举 / weekday=7 / `open_profile` 带参 四例 |
| emitter 执行后清空 | 每个 `_single_action` 断言 `result == {"navigation_intent": None}` |
| 不产 answer | `test_emitter_never_emits_answer_text` |
| 回查失败不发事件且清空 | `test_open_subject_lookup_failure_emits_nothing_but_clears_intent`（`{"error":True}` / `None` / `"boom"` 三形态） |
| meta 含 `path` + `label` | `test_open_profile_maps_to_profile_page` 等全量 meta 断言 |
| URL 键名与前端一致 | **人工逐项核对**（见下），无自动化交叉检查 |
| pytest 全绿 + 四个新文件 | 899 passed；四文件 29 用例 |

### 变异验证（由 trellis-check 执行，均已还原并 sha1 校验）

| 变异 | 转红 |
|---|---|
| 删 `run.py` 的 `navigation_intent` 回传 | `test_run_domain_agent.py::test_navigation_intent_written_by_nested_tool_is_relayed`（`KeyError`）**且** `test_each_domain_agent_reaches_emitter` 三条全红 → **证明图测试走真实 Domain agent 路径，不是 mock 节点** |
| 删 `search.py` 的工具注册 | **只有** `[search_agent]` 红（4 passed / 1 failed）→ 注册缺失能精确定位到具体 agent |
| 工具注册进 `admin/agent_node.py` | `test_admin_path_never_touches_emitter` 红 |

### 键名对照（人工核对，逐项）

| emitter path | 前端读取点 | 结论 |
|---|---|---|
| `/anime?q&tag(多值)&page&sort&order&year&weekday` | `AnimeIndex.tsx` q/tag/派生 4 字段 | 全对齐 |
| `/schedule?year&quarter&tab` | `Schedule.tsx:18-20` | 键名对齐；`tab` 语义见下 |
| `/subject/{id}` | `router.tsx` `subject/:id` | ✓ |
| `/my-collections?tab&page` | `MyCollections.tsx:11-19`（TABS key `all`/`1`..`5`） | 完全匹配 |
| `/profile` | `router.tsx` | ✓ |

**星期两套约定相反**（已在工具 docstring 写明，否则模型按一套填另一套会整体错一天且 Pydantic 不报错）：

| 参数 | 约定 | 依据 |
|---|---|---|
| `open_anime_index.weekday` | 0=周日 … 6=周六 | `AnimeIndex.tsx` 的 `WEEKDAYS` 索引 |
| `open_schedule.tab` | 0=周一 … 6=周日 | `Schedule.tsx:11-13`，`tabToWeekday(i)=(i+1)%7` |

### 交付物

- `app/agent/client/navigation.py`（新）：`build_request_navigation_tool()`，Pydantic 卡 5 个 action 参数域，返回带 `ToolMessage` 的 `Command`，零 IO
- `app/agent/navigation_emitter.py`（新）：纯函数节点 + `open_subject` 权威回查
- `app/agent/graph.py`：三个 Domain agent 改条件边 + emitter 节点
- `app/agent/run.py` + `runtime.py`：**D1 嵌套图回传**（不做这步整条链静默失效）
- `app/chat/event_sink.py`：`emit_ui_action`（生产者，上个子任务只到消费端）
- `app/agent/state.py` + `chat/service.py`：`navigation_intent` 字段与初始值
- 三个 Domain prompt：只加「可调用 `request_navigation` + 参数域 + 严禁编造 ID」基础说明，**不含** child 4 的「先写后导航」

### 与定案的偏差

`build_request_navigation_tool` **没有** `gated` 参数（design D6 原本写了保留参数位）。实现时判定：
留一个调用期不读的开关，会让 child 4 传 `gated=True` 却静默不生效，比三行改动更危险。
已在 child 4 的 `design.md` / `implement.md` 记明：本 child 只加回参数与门控 body。
