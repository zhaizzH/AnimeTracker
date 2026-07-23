# Agent Chat SSE 流式事件过滤修复

## 问题

`POST /api/chat/stream` 返回的 SSE 流中，Router 节点（`user_router`）的 LLM 意图短文本（如 `"search"`）也被当成 `event: token` 推送给前端，导致回复中出现重复文本。

实际输出：
```
searchsearch正在搜索"咒术回战"...
```

期望输出：
```
正在搜索"咒术回战"...
```

## 根因

`ChatService.event_stream` 监听所有 `on_chat_model_stream` 事件，未按来源节点（`langgraph_node`）过滤。Router 节点的 LLM 输出本是意图分类用，不应暴露给用户。

## 方案

在 `event_stream` 的 `on_chat_model_stream` 处理分支中，检查事件的 `metadata.langgraph_node`，**只推送子代理节点**（search/discover/recommend）的 token。Router 节点（user_router/admin_router/denied）的输出自动跳过。

### 改动范围

单个文件：`backend/agent/app/service/chat.py`

```python
# 添加一个前缀集合
_SUB_AGENTS = {"search", "discover", "recommend"}

# 在 on_chat_model_stream 分支开头过滤
langgraph_node = event.get("metadata", {}).get("langgraph_node", "")
if langgraph_node not in _SUB_AGENTS:
    continue
```

### 原理

LangGraph `astream_events` v2 在每个事件中携带 `metadata.langgraph_node` — 标明当前是在哪个节点内触发的 LLM 调用。子节点（sub-agent）作为子图运行时，其内部 LLM 事件仍标记为父图中的节点名 `search`/`discover`/`recommend`，所以只需过滤顶层节点即可。

## 影响范围

- SEO 级变更：无影响
- Router 节点输出的 token 不会再推到前端
- sub-agent 节点的 LLM token 推流不受影响
- metadata/done/error 事件不受影响

## 相关文件

- `backend/agent/app/service/chat.py` — 唯一需要修改的文件
