# 设计补充：图后路由链与 `navigation_emitter`

> 承接 `prd.md` / `implement.md`。**D1/D2 修正了 spec §4 的两处机制错误**，均有探针实测证据。

## D1 `navigation_intent` 必须显式回传出 Domain agent（修正 spec §4）

### 实测

`run_domain_agent`（`app/agent/run.py`）内部用 `create_agent(...)` 建的是**嵌套图**。
工具的 `Command(update=...)` 只写进**内层** state。探针（嵌套图 + 条件边）结果：

```
inner latest navigation_intent: {'action': 'open_profile'}   # 内层有
outer final: None                                            # 外层没有
EMITTER 未执行
```

原因：`run_domain_agent` 只 `return {"result": text, "messages": [AIMessage(...)]}`，
内层的 `navigation_intent` 从未回传。spec §4「图的条件边读得到」在现状下不成立。

### 定案

`run_domain_agent` 显式回传：

```python
text = stream["streamed_text"]
return {
    "result": text,
    "messages": [AIMessage(content=text)],
    "navigation_intent": stream.get("navigation_intent"),
}
```

`agent_stream`（`app/agent/runtime.py`）已经在 `stream_mode=["messages","values"]` 里收集
`latest_state`，只需在返回 dict 里补一个键：

```python
return {
    "streamed_text": ...,
    "streamed_thinking": ...,
    "navigation_intent": latest_state.get("navigation_intent"),
}
```

**外层图的 `navigation_emitter` 位置不变**——它是外层节点，读的是外层 state。
不需要把 emitter 挪进 Domain agent，也不改 ReAct 循环。

同一探针补上回传后：

```
EMITTER saw {'action': 'open_profile'}
outer final: None 好的
```

### 为什么不是「外层直接读内层返回值」

LangGraph 节点返回值即 state patch，没有别的通道。要么显式回传，要么改用
`Command(graph=Command.PARENT)` 让工具跨层写——后者会把工具与图结构耦合，
且内层 `create_agent` 的 state schema 是独立编译的，跨层写不在其契约内。显式回传最直白。

## D2 工具必须返回带 `ToolMessage` 的 `Command`（修正 spec §4.1）

### 实测

只写 `Command(update={"navigation_intent": ...})` 直接抛：

```
ValueError: Expected to have a matching ToolMessage in Command.update for tool
'request_navigation', got: []. Every tool call in the message history MUST have a
corresponding ToolMessage.
```

### 定案

```python
from langchain.tools import InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command

return Command(update={
    "navigation_intent": {"action": action, "params": params},
    "messages": [ToolMessage(
        content=json.dumps({"ok": True, "action": action}, ensure_ascii=False),
        tool_call_id=tool_call_id,
    )],
})
```

- 参数 `tool_call_id: Annotated[str, InjectedToolCallId]` 注入，**不由模型提供**
- 非法参数走**同一形态**返回错误，只是不写 `navigation_intent`：
  `Command(update={"messages": [ToolMessage(content=json.dumps({"error": True, "message": ...}), ...)]})`
- **不用 `@tool_call_status` 装饰**：导航工具不是业务调用，不需要在工具面板显示
  「正在调用 请求导航」。`build_tool_status_middleware` 对未注册名直接透传
  （`middleware.py` 里 `if tool_name not in _REGISTERED: return await handler(request)`），
  不装饰即可静默。

## D3 白名单映射：单一事实源，键名对照实测

新建 `app/agent/client/navigation.py`（工具 + Pydantic 模型）与
`app/agent/navigation_emitter.py`（外层图节点，非 Domain agent，故不放 `client/`）。

按 `directory-structure.md`「新 Agent 工具按最小权限放到 client/admin 对应节点」，
工具属 client 侧；emitter 是图级节点，与 `graph.py` 同层。

### 键名对照（已逐个查源码）

| action | path | 参数 → query 键 | 依据 |
|---|---|---|---|
| `open_anime_index` | `/anime` | `q` / `tag`（**多值**，重复 append）/ `page` / `sort` / `order` / `year` / `weekday` | `AnimeIndex.tsx` + child 1 改造 |
| `open_schedule` | `/schedule` | `year` / `quarter` / `tab` | `Schedule.tsx:19-21` |
| `open_subject` | `/subject/{id}` | 无 query | `router.tsx` `subject/:id` |
| `open_collections` | `/my-collections` | `tab` / `page` | `MyCollections.tsx:18-19` |
| `open_profile` | `/profile` | 无 | `router.tsx` |

**参数域（Pydantic 卡边界，非法即拒）**：

- `open_anime_index`：`q: str|None`（strip 后非空才带）、`tags: list[str]|None`（→ 重复 `tag` 键）、
  `year: int|None`（`1900..2100`）、`weekday: int|None`（`0..6`）、
  `sort: Literal["score","air_date","rank","collection_total"]|None`、
  `order: Literal["asc","desc"]|None`、`page: int = 1`（`>=1`）
- `open_schedule`：`year: int|None`、`quarter: Literal["spring","summer","autumn","winter"]|None`、
  `tab: str|None`（`"0".."6"`，对应 `Schedule` 的 weekday tab）
- `open_subject`：`subject_id: int`（必填，`>0`，别名 `subjectId`）
- `open_collections`：`tab: Literal["all","1","2","3","4","5"] = "all"`、`page: int = 1`
- `open_profile`：无参数

**命名不一致处理**：工具入参统一 snake_case（`subject_id`、`tags`），
`meta.params` 下发时也用 snake_case；URL query 键名由 emitter 的映射表决定（`tags`→`tag`）。
前端不读 params 构造 URL（见 `ui-action-event/design.md` D4），所以不存在两端命名漂移。

**默认值不写入 URL**：`sort=score`、`order=desc`、`page=1`、`tab=all` 缺省时不出现在 query 里。

> 前三个与前端取值等价：`AnimeIndex` 的 `FILTER_DEFAULTS` 只含 4 个筛选键（不含 `page`），
> `page` 由 `params.get('page') ?? 1` 派生。注意 `AnimeIndex.nav()` 自己**总是**写 `page`
> （用户操作后地址栏会多一个 `page=1`），而 emitter 在 `page=1` 时不写——**URL 形态不同但渲染与请求等价**，
> 不是不一致。`tab=all` 由 `_collections` 单独判断。

**星期两套约定相反，必须在工具 docstring 里写明**（否则模型按一套填另一套，整体错一天且 Pydantic 不报错）：

| 参数 | 约定 | 依据 |
|---|---|---|
| `open_anime_index.weekday` | **0=周日 … 6=周六** | `AnimeIndex.tsx` 的 `WEEKDAYS` 索引；后端 `airWeekday` 口径 |
| `open_schedule.tab` | **0=周一 … 6=周日** | `Schedule.tsx:11-13` 的 `WEEK` 下标，`tabToWeekday(i) = (i+1)%7` |

### `path` 与 `label` 由 emitter 生成

`emit_ui_action` 的 meta：

```python
{
    "action": intent["action"],
    "params": intent["params"],
    "path": path,      # 前端直接 navigate(path)，不重复实现映射
    "label": label,    # 浮层系统提示文案，固定模板非模型生成
}
```

`label` 模板（白名单固定，不含自由文本拼接以外的模型输出）：

| action | 模板 |
|---|---|
| `open_anime_index` | `「番剧索引」` + 有 year 时 ` · {year} 年` + 有 q 时 ` · 「{q}」` |
| `open_schedule` | `「追番日程」` + 有 year/quarter 时追加 |
| `open_subject` | `「{条目名}」`（条目名来自 D4 的回查结果） |
| `open_collections` | `「我的收藏」` + tab 非 all 时 ` · {想看/看过/在看/搁置/抛弃}` |
| `open_profile` | `「个人中心」` |

前端显示为 `⚡ 已跳转到{label}`。

## D4 `open_subject` 必须权威回查，编造的 ID 不跳

工具只校验 `int > 0`，**真正的保证在 emitter**：

```python
if intent["action"] == "open_subject":
    detail = business.request("GET", f"/api/client/subjects/{subject_id}")
    if not isinstance(detail, dict) or detail.get("error"):
        return {"navigation_intent": None}   # 清空但不发事件
    label_name = detail.get("name") or ...
```

- 回查失败 → **不发 `ui_action`**，只清空 intent。用户看到的是前序 Domain agent 的回答，
  不会白屏跳 404。
- 工具本身保持**零 IO**（spec §4.1 不变），IO 集中在 emitter——它本来就要构造 URL，
  是「导航是否真的成立」的最后一个确定性关口。
- 理由：父任务验收「模型不得编造 ID」。只校验类型挡不住 `subjectId=999999`；
  维护「本回合已解析 ID 白名单」要给 search/resolution 全链路埋点，成本远高于一次回查。

emitter 因此需要 `business` 依赖：`build_navigation_emitter(dependencies)` 工厂，
与 `build_search_agent(dependencies)` 同形态。

## D5 图条件边与 state 清理

```python
graph.add_node("navigation_emitter", build_navigation_emitter(dependencies))
for node in ("search_agent", "discover_agent", "recommend_agent"):
    graph.add_conditional_edges(node, _route_after_domain,
                                {"navigation_emitter": "navigation_emitter", END: END})
graph.add_edge("navigation_emitter", END)
# admin_agent → END 不动
```

- `_route_after_domain`：`state.get("navigation_intent")` 非空 → emitter，否则 END
- emitter 返回 `{"navigation_intent": None}` **无论是否发出事件**（含 D4 回查失败分支），
  保证不残留
- `AgentState` 加 `navigation_intent: dict | None`；`service.py::build_initial_state`
  显式初始化为 `None`，避免上一轮残留（虽然 state 每请求重建，显式初始化更符合既有风格）
- **事件发出时机**：emitter 是外层图节点，经实测 `ContextVar` 的 event sink 在节点内可见
  （`streaming.py` 的 `set_event_sink(_QueueEventSink())` 包住整个 `astream`），
  所以 `emit_event(AgentEvent(type=UI_ACTION, meta=...))` 会正常入队并被 `serialize_agent_event` 序列化

新增 `emit_ui_action` 到 `app/chat/event_sink.py`，与 `emit_answer_delta` 等同层：

```python
def emit_ui_action(*, action: str, params: dict, path: str, label: str) -> None:
    emit_event(AgentEvent(type=AgentEventType.UI_ACTION,
                          meta={"action": action, "params": params, "path": path, "label": label}))
```

meta 必非空 → 不会被 `exclude_none` 剔除（见 `ui-action-event/design.md` D2）。

## D6 与 child 4 的接缝

本 child 把 `request_navigation` 注册到**三个 Domain agent**，**不做任何写入门控**。
门控在 child 4 以「构造参数 + turn-bag」形式加入（见 `composite-write-navigate/design.md` D2）。

容许 child 4 不改**注册点**，但**不预留参数位**（2026-10-30 修正）：

```python
def build_request_navigation_tool():   # 无 gated 参数
```

初稿写的是 `build_request_navigation_tool(*, gated: bool = False)`，实现时发现
「保留一个调用期不读的开关」比「三行改动」更危险：child 4 传 `gated=True` 会**静默不生效**。
所以本 child 直接不传参数；child 4 落地时加回 `gated` 参数与门控 body（并确保门控在
**工具调用时**读 turn-bag，不是工厂构造期定值）。

**注意**：`build_search_agent` / `build_discover_agent` / `build_recommend_agent` 三个工厂
都要加这一行注册，且 recommend 的调用点在 child 4 会再改一次——这是预期的，
不要在 child 3 提前把 recommend 的门控写死。

## 测试清单（修订）

- `test_request_navigation_tool.py`
  - 非法 action / 缺 `subjectId` / `year` 越界 / `sort` 非枚举 / `weekday=7` → 返回错误，**state 无 `navigation_intent`**
  - 合法调用 → 返回 `Command`，`update` 里同时有 `navigation_intent` 与 `messages`
  - 走真实 `create_agent` 跑一遍，断言**不抛 ValueError**（锁 D2 的 ToolMessage 要求）
- `test_navigation_emitter.py`
  - 5 个 action 的 path/label 映射正确，默认值不出现在 query
  - `tags` → 重复 `tag` 键
  - `open_subject` 回查失败 → 不发事件且 intent 清空
  - 执行后 `navigation_intent` 为 None；不产生任何 `answer` 事件
- `test_graph_post_routing.py`
  - 空 intent 直接 END
  - **三个 Domain agent 的 intent 都能到达 emitter**（锁 D1 的回传，不能只测 emitter 本身）
  - admin 路径不经过 emitter
- `test_run_domain_agent.py`（新增或扩充）
  - 内层工具写 `navigation_intent` 后，`run_domain_agent` 返回值里带该字段

## 不做

- 不做写入门控（child 4）
- 不做自由 path
- 不让 emitter 调 LLM
- 不改 gateway 的输出契约（仍单标签 `route_target`）
- 不把 emitter 放进 `client/` 或命名为 `navigate_agent`
