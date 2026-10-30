# Agent 驱动 UI：导航意图、图后路由与 `ui_action` 事件

> **状态**：§4.1–§6（SSE 通道、`request_navigation` 工具契约、重放打标、Java 透传）**已实现**（`10-29-ui-action-event`，2026-10-30）。**尚未实现**：图后路由边与 `navigation_emitter` 节点（`10-29-navigation-graph`）、写入后导航门控（`10-29-composite-write-navigate`）——`app/agent/graph.py` 当前仍是单次路由无环。
> 前置阅读：[Agent 编排与流式协议](./agent-guidelines.md)、[Agent 安全写操作](./write-operations.md)、[ADR 0001](../adr/0001-agent-write-two-phase-preview-confirm.md)。

## 1. 目标与非目标

**目标**：用户用自然语言完成「需要手动点击多次」的**只读页面操作**——跳页、带筛选跳页、打开某条目详情。页面真的变化，用户看得见。

**非目标**（本设计刻意排除）：
- 不代填表单、不代点提交。改密码 / 改邮箱 / 换头像属账户凭据操作，永不进 agent。
- 不做写入类 UI 自动化。写操作仍只走 ADR 0001 的 `preview → confirm → execute`。
- 不在聊天面板内嵌目标页面预览。

## 2. 术语

新增两个词，已同步 [.trellis/spec/GLOSSARY.md](../GLOSSARY.md)：

- **NavigationIntent**：Domain agent 写入 state 的结构化跳转意图，只表达「去哪 + 带什么参数」，不含 URL。
- **UI action**：导航节点发到 wire 上的事件，前端收到后执行路由跳转。**可逆、无持久副作用**，因此不走 PendingAction。

## 3. 图结构：后路由链

现状是 `START → gateway_router → 单个 Domain agent → END`，单次路由无环。本设计加一条**确定性后路由边**，不改 ReAct 内部：

```
START ─┬─ ADMIN → admin_agent → END
       └─ gateway_router ─┬─ search_agent ────┐
                          ├─ discover_agent ──┼─► [navigation_intent 非空?]
                          └─ recommend_agent ─┘        │
                                              是 ──────┴─────► navigation_emitter → END
                                              否 ────────────────────────────────► END
```

**为什么后路由而不是 gateway 拆意图**：gateway 目前是单标签分类器，输出 `{"route_target": str}`。让它输出「写 + 导航」的数组会把分类问题变成规划问题，JSON 解析错误面扩大，且 `_resolve_routing_result` 的全部校验要重写。后路由用**图边**表达顺序，模型无法颠倒「先写后导航」。

**为什么不让 Domain agent 自己调导航工具**：破坏「路由即工具权限边界」这一既有不变量（`admin_agent` 无 RAG、`search_agent` 无写工具）；且 ReAct 循环内模型可能在写入完成前就导航。

## 4. 三个组件的职责

### 4.1 `request_navigation` 工具（纯 state 写入，零 IO）

注册到**全部三个 Domain agent**（search / discover / recommend）。只做一件事：校验参数 → 写 `state["navigation_intent"]`。**不发事件、不跳页、不调 LLM**。

> **为什么不是只给 recommend**：纯导航请求（「打开我的收藏」）会被 gateway 路由到 `search_agent`，那里若无工具就失败。导航是无副作用的只读意图，权限边界真正在**写工具**上，不在导航工具上。

**写 state 的机制**：用 LangGraph `Command(update=...)`，且 `update` 里**必须同时带一条 `ToolMessage`**：

```python
Command(update={
    "navigation_intent": {...},
    "messages": [ToolMessage(content=json.dumps({"ok": True}), tool_call_id=tool_call_id)],
})
```

实测（2026-10-29 探针）：只写 `navigation_intent` 会抛 `ValueError: Expected to have a matching ToolMessage in Command.update`，工具节点直接失败。`tool_call_id` 由 `InjectedToolCallId` 注入，不由模型提供。

普通工具返回值会变成 `ToolMessage` 内容、**不进 state**，图的条件边读不到。也**不走** `emit_pending_action_*` ContextVar——那是 PendingAction 持久化通道（SSE 收尾落 Redis，TTL 600s）；`navigation_intent` 只在单次图内活。

**嵌套图必须显式回传**：`run_domain_agent` 内的 `create_agent` 是嵌套图，工具的 `Command` 只写内层 state。实测外层图的 `navigation_intent` 仍为 `None`，条件边永远走不到 emitter。因此 `agent_stream` 返回 dict 增加 `navigation_intent=latest_state.get(...)`，`run_domain_agent` 在返回值里带上该字段。详见 [navigation-graph/design.md](../../tasks/10-29-navigation-graph/design.md) D1。

约束：
- `open_subject` 的 `subjectId` 必须是**前序工具已解析出的真实 ID**（来自 `subject_resolution` 或 RAG 候选）。工具不接受标题字符串——标题解析属于原 Domain agent 的职责，且必须经权威回查。
- 参数经 Pydantic 校验，非法值直接返回错误 dict，不写 state。

### 4.2 `navigation_emitter` 节点（纯函数，非 Domain agent）

按 GLOSSARY 对 `Domain agent` 的定义（检索 / 发现 / 推荐三个面向用户的图节点），本节点**不是** Domain agent，不挂 LLM、不挂 prompt、不注册业务工具。

```
读 state["navigation_intent"]
  → 白名单映射成 path + query
  → emit_ui_action(action, params)
  → 返回 {"navigation_intent": None}   # 清空，防止下一轮重发
```

**静默**：不产 `answer` 文本。理由见 §6 错误矩阵——「已为你打开…」在导航尚未发生时说出口等于撒谎；若前序节点已回答，用户看到两段割裂文本。

**`open_subject` 在此做权威回查**：工具只校验 `int > 0` 挡不住编造的 ID。emitter 调 `GET /api/client/subjects/{id}`，回查失败则**不发事件**、只清空 intent；成功时条目名用于 `label`。工具因此保持零 IO，IO 集中在 emitter 这个最后的确定性关口。emitter 用 `build_navigation_emitter(dependencies)` 工厂拿 `business`。

**下发的 meta 含 `path` 与 `label`**：`{"action", "params", "path", "label"}`。前端直接 `navigate(meta.path)`，不重复实现 action→URL 映射；`label` 按白名单固定模板生成（非模型自由文本），用于浮层系统提示 `⚡ 已跳转到…`。

### 4.3 前端执行

`useAgentChat.ts` 的 `dispatch` switch 增加 `case 'ui_action'`：不写正文、不进 `tools` 列表，调用注入的 `onUiAction` 回调。回调由 `AgentChat.tsx` 提供，内部用 `react-router` 的 `navigate()`。

**`AIAssistantFloat.tsx` 的关闭逻辑必须改**：当前 `useEffect(() => setOpen(false), [location.key])` 在任何路由变化时关面板。agent 导航会触发它，聊天界面随即消失——这会让整个特性失效。改为：agent 发起的导航（带标记）不关面板，用户手动点导航链接仍关。

具体接口由 [frontend-url-state/design.md](../../tasks/10-29-frontend-url-state/design.md) 定义：模块级 `markAgentNavigation()`（一次性标记）与 `showNavHint(label)`（浮层内系统提示，本地瞬时状态、不进会话历史）。调用顺序固定为「标记 → `navigate` → 提示」，反了面板会先被关掉。

## 5. 一期 action 白名单（5 个）

全部只读展示页，服务端构造 path，模型只选 action 与参数。

| action | 参数 | 目标 |
|---|---|---|
| `open_anime_index` | `q?` `tags?` `year?` `weekday?` `sort?` `order?` `page?` | `/anime?...` |
| `open_schedule` | `year?` `quarter?` `tab?` | `/schedule?...` |
| `open_subject` | `subjectId`（必填，须已解析） | `/subject/{id}` |
| `open_collections` | `tab?` `page?` | `/my-collections?...` |
| `open_profile` | 无 | `/profile` |

**前置改造（阻塞项）**：`frontend/client/src/pages/AnimeIndex.tsx` 的 `sort` / `order` / `year` / `weekday` 当前是 `useState`，只有 `q` / `tag` / `page` 在 `useSearchParams`。**URL 表达不出年份筛选**，`open_anime_index(year=2022)` 无法实现。必须先把这四个字段归一化到 URL——与 `Schedule.tsx`、`MyCollections.tsx` 既有做法对齐，也落实该文件注释里已写的「以 URL 为唯一来源」原则。

**不做自由 path**：模型可拼出 `/admin`、`javascript:` 或错误 path 导致白屏。枚举让服务端独占 URL 知识，与 `RetrievalQuery` 用 Pydantic 卡字段边界同理。

## 6. SSE 契约变更（7 处，缺一不可）

`ui_action` 是**跨层契约变更**，不是「加个事件」。两层枚举 + 契约测试的传递断言意味着漏任何一处都会红：

| 文件 | 改动 |
|---|---|
| `app/chat/events.py` | `AgentEventType` 加 `UI_ACTION = "ui_action"`；`AgentEvent` 已有 `meta: dict` 可承载参数，不新增字段 |
| `app/api/schemas/sse.py` | `MessageType` 加 `UI_ACTION` |
| `app/api/sse.py` | `serialize_agent_event` 走既有 `MessageType(event.type.value)` 即可，无需特判；确认 `meta` 不被剔除 |
| `app/chat/runs.py` | **`subscribe()` 重放缓存段给 `UI_ACTION` 补 `meta.replayed=true`**（不跳帧，原因见下）；实时订阅段不打标 |
| `frontend/packages/shared/src/hooks/useAgentChat.ts` | switch 加 `case 'ui_action'`，走 `onUiAction`，不落正文 |
| `docs/spec/openapi.yaml` | `SSEFrame` 的 `type` 枚举加值；`/api/client/agent/stream` 描述更新 |
| `backend/agent/tests/contracts/test_sse_contract.py` | 契约 enum 加值；`test_all_serializable_event_types_are_covered` 与 `test_message_type_matches_agent_event_type` 靠传递断言自动生效 |

**Java 透传已实测，无需改动**：`AgentSseResponseWriter.java` 是逐行原样转发（`writerRef[0].write(line + "\n")`），不解析 JSON、无类型白名单。待办关闭。

**契约测试要补样本**：`tests/contracts/test_sse_contract.py` 的 `_sample_events()` 必须补一个带完整 meta 的 `UI_ACTION` 事件——传递断言只对被采样的类型生效，只加枚举不加样本会漏掉序列化路径覆盖。另注意 `meta=event.meta or None` + `exclude_none=True` 意味着**空 meta 会被剔除**，`ui_action` 的 meta 必须非空。

**重放不过滤，改打标（2026-10-29 修正）**：原方案「重放段跳过 `UI_ACTION`」有游标错位 bug——前端 `after` 是**已收到的帧数**，后端 `start` 是 `run.events` 的**下标**，跳帧后两者不再对位。反例：`events=[answer, ui_action, answer, answer]`，重连收 3 帧 `frames=3`，再重连 `after=3` 会从 `events[3:]` 开始，最后一条 answer 被重放第二次，正文重复。

定案：**重放段照常下发 `ui_action`，但补 `meta.replayed=true`；前端见到该标记直接忽略**。帧数与缓冲下标保持 1:1，游标天然对齐，且保留可回溯性。语义细化为「重放帧仍下发，执行权在前端」。

写入侧仍然不动：若在 `_drive()` 就不入缓冲，改的是写入路径，保护错了对象。详见 [ui-action-event/design.md](../../tasks/10-29-ui-action-event/design.md) D1。

## 7. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| `navigation_intent` 为空 | 直接 END，不进 `navigation_emitter` |
| `open_subject` 的 `subjectId` 未解析/不存在 | `request_navigation` 返回错误，不写 state；不得让模型编 ID |
| 参数非法（year 越界、sort 非枚举） | Pydantic 拒绝，工具返回错误 dict |
| 复合指令「写入 + 导航」 | 写入走完 ADR 0001 两阶段后才到 `navigation_emitter`；用户未确认则导航不发生 |
| 导航事件发出但前端已离开会话 | 前端 `onUiAction` 自行判断，服务端不重试 |
| `meta.path` 非站内路径 | 前端只接受以 `/` 开头且不以 `//` 开头的值，其余丢弃（防 `javascript:` / 外链的廉价兜底） |
| 写入类 pending 存在时的导航请求 | 见 child 4：门控读**本回合 turn-bag** 而非 state——state 里的 `pending_action` 是回合开始时的快照，写成功后不会更新，读它会拦掉唯一该放行的那次导航 |
| 断线重连（`subscribe(after=cursor)`） | 重放段 `ui_action` 带 `meta.replayed=true`，前端忽略，**不重复导航**；帧数与缓冲下标 1:1，游标不错位 |
| `navigation_emitter` 执行后 | 清空 `navigation_intent`，下一轮不残留 |
| 用户手动点导航链接 | 浮层照常关闭（仅 agent 导航不关） |

## 8. Good / Base / Bad Cases

- **Good**：「把《孤独摇滚》加入想看，然后打开我的收藏」→ `recommend_agent` 出预览 → 用户确认 → 写成功 → `request_navigation` 写 state → `navigation_emitter` 发 `ui_action` → 前端跳 `/my-collections`，浮层保持打开。
- **Base**：「给我看 2022 年的番」→ 单轮 `search_agent` + `request_navigation` → 跳 `/anime?year=2022`。依赖 §5 前置改造已完成。
- **Bad**：让 gateway 输出 `{"steps":[...]}` 拆意图；把导航工具塞进 `search_agent`；`navigation_emitter` 调 LLM 生成「已为你打开」；在 `_drive()` 里丢掉 `ui_action` 导致无法回溯。

## 9. Tests Required

- `tests/agent/test_navigation_emitter.py`：纯函数映射、白名单外 action 拒绝、`subjectId` 必填、执行后清空 state、不产 answer 文本。
- `tests/agent/test_graph_post_routing.py`：`navigation_intent` 非空才走 emitter；三个 Domain agent 都能到达；admin 路径不受影响。
- `tests/agent/test_request_navigation_tool.py`：参数校验、非法值不写 state、复合指令下写入未完成时不发导航。
- `tests/chat/test_runs_replay.py`：重放段 `ui_action` 带 `replayed` 标记且**帧数与缓冲一致**，实时段不打标；连续两次重连用前端口径的 `after` 不重复不遗漏；缓冲截断 warning 行为不回归。
- `tests/agent/test_run_domain_agent.py`：内层工具写 `navigation_intent` 后，`run_domain_agent` 返回值带该字段（锁嵌套图回传）。
- `tests/api/test_sse_serialization.py` + `tests/contracts/test_sse_contract.py`：五值 wire 枚举、`meta` 保留、结束帧形态不变。
- 前端：`useAgentChat.uiAction.test.tsx`（事件不进正文/工具列表、回调被调）、`AIAssistantFloat` 的 agent 导航不关面板、`AnimeIndex` 筛选 URL 归一化回归。

## 10. Wrong vs Correct

### Wrong

```python
# 导航节点里再调一次模型
def navigation_emitter(state):
    llm = factory.create(slot=...)
    return llm.invoke(f"用户想去 {state['navigation_intent']}，说点什么")
```

```python
# 在写入侧丢弃事件，以为这样就不会重复导航
async for event in events:
    if event.type is AgentEventType.UI_ACTION:
        continue  # 错：失去回溯能力，且改错了路径
    run.events.append(event)
```

```python
# 重放段跳过事件：帧数与 run.events 下标错位，前端 after 游标失准
for event in run.events[start - run.buffer_start:]:
    if event.type is AgentEventType.UI_ACTION:
        continue  # 错：后续重连会重复或遗漏其它事件
    yield event
```

```python
# 工具只写 state 不带 ToolMessage
return Command(update={"navigation_intent": {...}})  # 错：ValueError，工具节点失败
```

### Correct

```python
# 纯函数：语义已在前序节点决定，这里只剩「意图 → URL」
def navigation_emitter(state):
    intent = state.get("navigation_intent")
    if not intent:
        return {}
    emit_ui_action(action=intent["action"], params=intent["params"])
    return {"navigation_intent": None}
```

```python
# 重放段打标，实时段放行；帧数与缓冲下标始终 1:1
for event in run.events[start - run.buffer_start:]:
    if event.type is AgentEventType.UI_ACTION:
        yield self._with_run_id(run, self._mark_replayed(event))
        continue
    yield self._with_run_id(run, event)
```

```python
# 工具写 state 必须同时补 ToolMessage
tool_call_id: Annotated[str, InjectedToolCallId]
return Command(update={
    "navigation_intent": {"action": action, "params": params},
    "messages": [ToolMessage(content=json.dumps({"ok": True}), tool_call_id=tool_call_id)],
})
```
