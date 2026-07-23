# SSE 流式事件过滤 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 过滤 SSE 流中的 Router 节点 LLM token，只推送 sub-agent（search/discover/recommend）节点的输出

**Architecture:** 在 `ChatService.event_stream` 的 `on_chat_model_stream` 处理分支中，通过 `metadata.langgraph_node` 判断事件来源节点，非 sub-agent 节点的 token 直接跳过

**Tech Stack:** FastAPI, LangGraph, Python 3.12+

---

### Task 1: 在 chat.py 中添加 SSE 事件过滤

**Files:**
- Modify: `backend/agent/app/service/chat.py:64-76`

**Interfaces:**
- 无新增接口。`event_stream` 内部逻辑变更，对外行为不变（SSE 事件格式不变，只是 token 事件减少）

- [ ] **Step 1: 定位要修改的区域**

文件 `backend/agent/app/service/chat.py`，`event_stream` 函数中 `on_chat_model_stream` 处理分支，当前代码：
```python
if kind == "on_chat_model_stream":
    chunk = event["data"]["chunk"]
    if hasattr(chunk, "content") and chunk.content:
        full_content += chunk.content
        yield f"event: token\ndata: {json.dumps({'content': chunk.content})}\n\n"
```

- [ ] **Step 2: 添加 langgraph_node 过滤**

修改为：
```python
_SUB_AGENTS = {"search", "discover", "recommend"}

# ... 在 event_stream 函数内部 ...

if kind == "on_chat_model_stream":
    langgraph_node = event.get("metadata", {}).get("langgraph_node", "")
    if langgraph_node not in _SUB_AGENTS:
        continue
    chunk = event["data"]["chunk"]
    if hasattr(chunk, "content") and chunk.content:
        full_content += chunk.content
        yield f"event: token\ndata: {json.dumps({'content': chunk.content})}\n\n"
```

- [ ] **Step 3: 验证改动**

```bash
cd backend/agent
# 语法检查
python -c "from app.service.chat import ChatService; print('OK')"
```

Expected: 无报错，输出 `OK`

- [ ] **Step 4: 运行现有测试**

```bash
cd backend/agent
pytest -x -q
```

Expected: 全部通过

- [ ] **Step 5: Commit**

```bash
git add backend/agent/app/service/chat.py
git commit -m "fix(chat): 过滤 SSE 流中 Router 节点的 LLM 输出，只推送 sub-agent 的 token"
```
