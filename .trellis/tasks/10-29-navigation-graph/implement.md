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
   - 工厂签名 `build_request_navigation_tool(gated: bool = False)`，门控在工具内部**延迟** `get_turn_state()`（child 4 用）
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

## 不做

- 不在 recommend_agent 做写入门控（child 4；工具本身三节点都注册，属本 child）
- 不做自由 path
- 不让 emitter 调 LLM
