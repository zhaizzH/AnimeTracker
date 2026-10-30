# 执行计划：图后路由链与 `navigation_emitter`

**前置**：`ui-action-event` 已归档（事件通道可用）。

> **2026-10-29 修订**：两处机制错误经探针实测后修正——
> (1) 工具必须返回带 `ToolMessage` 的 `Command`，否则 `ValueError`；
> (2) 嵌套图的 `navigation_intent` 必须由 `run_domain_agent` 显式回传，否则外层条件边永远读不到。
> 以 [design.md](./design.md) D1/D2 为准。另新增 D4：`open_subject` 在 emitter 做权威回查。

## 切片 1：state 与工具

文件：`app/agent/state.py`、新文件 `app/agent/client/navigation.py`

1. `AgentState` 加 `navigation_intent: dict | None`；`service.py::build_initial_state` 显式初始化 `None`
2. `request_navigation(action, params, ..., tool_call_id: Annotated[str, InjectedToolCallId])` 工具：
   - Pydantic 模型校验 action ∈ 白名单、params 各字段类型与取值域（取值域见 design D3）
   - `open_subject` 强制要求 `subjectId: int > 0`
   - 非法 → `Command(update={"messages": [ToolMessage(content=json.dumps({"error": True, ...}), ...)]})`，**不写 state**
   - 合法 → `Command(update={"navigation_intent": {...}, "messages": [ToolMessage(...)]})`
     **两者都必须带 ToolMessage**，否则工具节点抛 `ValueError`
   - 零 IO、不发事件、不调 LLM；**不加 `@tool_call_status`**（不在工具面板显示）
   - 工厂签名 `build_request_navigation_tool()`——**不预留 `gated` 参数位**。留一个调用期不读的开关会让 child 4 传 `gated=True` 却静默不生效；child 4 落地时加回参数与门控 body（详见 [design.md](./design.md) D6）
3. `run_domain_agent` / `agent_stream` 增加 `navigation_intent` 回传（design D1，**不做这步整条链无效**）

**TDD**：非法 action / 缺 subjectId / year 越界三种否定用例先红。

## 切片 2：emitter 节点

新文件：`app/agent/navigation_emitter.py`（图级节点，非 Domain agent，不放 `client/`）；
工厂 `build_navigation_emitter(dependencies)`，需要 `business` 做 `open_subject` 回查。

```python
def navigation_emitter(state):
    intent = state.get("navigation_intent")
    if not intent:
        return {}
    if intent["action"] == "open_subject":
        detail = business.request("GET", f"/api/client/subjects/{intent['params']['subject_id']}")
        if not isinstance(detail, dict) or detail.get("error"):
            return {"navigation_intent": None}   # 回查失败：不发事件，但仍清空
    path, label = build_path_and_label(intent)
    emit_ui_action(action=intent["action"], params=intent["params"], path=path, label=label)
    return {"navigation_intent": None}
```

`emit_ui_action` 新增到 `app/chat/event_sink.py`，meta 含 `action/params/path/label`（必非空，否则被 `exclude_none` 剔除）。

- 纯函数，不挂 LLM / prompt / 业务工具
- **不产 answer 文本**
- URL 构造在服务端完成，键名必须与前端 `useSearchParams` 实际键名一致：
  - `AnimeIndex`：`q` / `tag`（多值）/ `page` + child 1 迁入的 `sort` / `order` / `year` / `weekday`
  - `Schedule`：`year` / `quarter` / `tab`
  - `MyCollections`：`tab` / `page`

## 切片 3：图条件边

文件：`app/agent/graph.py`

1. `graph.add_node("navigation_emitter", navigation_emitter)`
2. 三个 Domain agent 的 `add_edge(x, END)` 改为 `add_conditional_edges(x, _route_after_domain, {"navigation_emitter": ..., END: ...})`
3. `_route_after_domain`：`navigation_intent` 非空 → `"navigation_emitter"`，否则 `END`
4. `navigation_emitter → END`
5. admin 路径不动

## 切片 4：前端接上跳页

属 `ui-action-event` 的 D3/D4，本 child 不重复做：
`AgentChat.tsx` 的 `onUiAction` = `markAgentNavigation()` → `navigate(meta.path)` → `showNavHint(label)`。
前端**不**自己构造 path。

## 测试

- `tests/agent/test_request_navigation_tool.py`：参数校验、非法不写 state
- `tests/agent/test_navigation_emitter.py`：5 个 action 的 path/label 映射、默认值不进 query、`tags`→重复 `tag` 键、`open_subject` 回查失败不发事件、执行后清空、无 answer 事件
- `tests/agent/test_graph_post_routing.py`：空 intent 直接 END、**三个 Domain agent 的 intent 都能到达 emitter**（锁 D1 回传）、admin 不变
- `tests/agent/test_run_domain_agent.py`：内层写入的 `navigation_intent` 出现在 `run_domain_agent` 返回值里

## 验证

```bash
cd backend/agent && uv run pytest
```

## 公共测试缝（已确认，开工前定）

基线：`cd backend/agent && uv run pytest -q` → **867 passed**；`tests/contracts` 154 passed（2026-10-30 实测）。

| 缝 | 位置 | 能捕获 | 捕获不到 |
|---|---|---|---|
| 图入口/路由 | `tests/agent/test_capability_route.py::test_user_entry_routes_to_gateway_router`（已存在） | `_route_from_entry` 的 admin/user 分流不被新边破坏 | 新条件边本身 |
| 条件边 | **新** `tests/agent/test_graph_post_routing.py`（无既有可扩） | intent 为空直连 END；**三个 Domain agent 各自都能到达 emitter**；admin 不经 emitter | 真实模型是否会调工具 |
| emitter 纯函数 | **新** `tests/agent/test_navigation_emitter.py` | 5 个 action 的 path/label 映射、默认值不进 query、`tags`→重复 `tag`、`open_subject` 回查失败不发事件、清空 intent、不产 answer | —— |
| 工具参数校验 | **新** `tests/agent/test_request_navigation_tool.py` | 白名单外拒绝、缺 `subjectId` 拒绝、取值域越界拒绝、非法不写 state | 模型是否按 prompt 选对 action |
| 嵌套图回传 | **新** `tests/agent/test_run_domain_agent.py` | 内层工具写的 `navigation_intent` 出现在 `run_domain_agent` 返回值里（**锁 design D1，不做这步整条链静默失效**） | 真实 `create_agent` 完整 ReAct 循环 |
| prompt 包含新工具说明 | `tests/agent/test_client_prompt_contract.py`（已存在） | 三个 Domain prompt 提到 `request_navigation` | 模型遵循程度 |

**选新的理由**：`test_capability_route.py` 只管「entry/gateway 选哪个节点」，没有图结构断言；
而本任务改的正是图的边——用建图后的真实 `graph.astream` 跑短路径，比 mock 节点更真。
新建三个文件是因为职责不同（图 / emitter / 工具），混一个文件会让定位变慢。

**必须遵守的断言强度**：
- 三个 Domain agent 各一条用例，不能只测一个——漏注册一个就少一整条能力，而单点测试发现不了。
- `test_run_domain_agent.py` 必须走真实 `create_agent` + 假模型返回 `tool_calls`，不能手写 state 注入。
- emitter 的「不发事件」断言前，先用同一条路径证明**合法 intent 确实发了事件**（正向基线）。

## 不做

- 不在 recommend_agent 做写入门控（child 4；工具本身三节点都注册，属本 child）
- 不做自由 path
- 不让 emitter 调 LLM
