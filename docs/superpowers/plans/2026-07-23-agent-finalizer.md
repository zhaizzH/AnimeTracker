# Agent Finalizer 节点 Implementation Plan
# 使用中文commit messages
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Agent Graph 尾部新增 finalizer 节点，格式化 sub-agent 的输出为列表式简洁回复

**Architecture:** sub-agent 的 `final_output` 传入 finalizer 节点，由 LLM 按 FINALIZER_PROMPT 重新格式化后覆盖输出；SSE 层只放行 finalizer 和 denied 节点的 token

**Tech Stack:** FastAPI, LangGraph, Python 3.12+

---

### Task 1: 新增 finalizer prompt + 节点工厂 + Graph 注册 + SSE 过滤

**Files:**
- Modify: `backend/agent/app/graph/prompts.py` — 新增 `FINALIZER_PROMPT`
- Modify: `backend/agent/app/graph/nodes.py` — 新增 `create_finalizer_node`
- Modify: `backend/agent/app/graph/graph.py` — 注册 finalizer 节点，sub-agent → finalizer → END
- Modify: `backend/agent/app/service/chat.py` — SSE 过滤改为只放行 `finalizer` 和 `denied`

**Interfaces:**
- Consumes: `AgentState.final_output`（sub-agent 原始输出的文本字符串）
- Produces: Finalizer 将格式化后的文本写回 `state.final_output`

- [ ] **Step 1: prompts.py — 新增 FINALIZER_PROMPT**

在 `prompts.py` 末尾追加：

```python
FINALIZER_PROMPT = """请用简洁的列表格式重新组织下面的信息：

规则：
- 每条信息用「序号. 名称 — 关键信息」的格式，一行一条
- 不要使用任何 emoji
- 不加开场白
- 结尾不要问后续问题
- 总条数较多时只列前 10 条并注明总数

原始信息：
{content}
"""
```

- [ ] **Step 2: nodes.py — 新增 create_finalizer_node**

在文件末尾追加：

```python
def create_finalizer_node(llm):
    """创建最终格式化节点：将 sub-agent 的输出重新组织为简洁列表"""
    async def finalizer(state: AgentState) -> dict:
        if not state.final_output.strip():
            return {}
        prompt = FINALIZER_PROMPT.format(content=state.final_output)
        resp = await llm.ainvoke([SystemMessage(content=prompt)])
        return {"final_output": resp.content}
    return finalizer
```

同时更新文件顶部的 import，添加 `FINALIZER_PROMPT`：
```python
from app.graph.prompts import ROUTER_PROMPT, ADMIN_DENIED_PROMPT, FINALIZER_PROMPT
```

- [ ] **Step 3: graph.py — 注册 finalizer 节点并修改边**

注册节点。在 `builder.add_node("recommend", ...)` 之后添加：
```python
builder.add_node("finalizer", create_finalizer_node(llm))
```

修改所有 sub-agent 的终点，从 `END` 改为 `finalizer`。将循环：
```python
for agent in ("search", "discover", "recommend", "denied"):
    builder.add_edge(agent, END)
```

改为：
```python
for agent in ("search", "discover", "recommend"):
    builder.add_edge(agent, "finalizer")
builder.add_edge("finalizer", END)
builder.add_edge("denied", END)
```

同时添加 import。现有 import 行已包含 `create_sub_agent_node, create_role_router`，修改为：
```python
from app.graph.nodes import (
    create_entry_node, create_user_router, create_admin_router,
    create_denied_node, create_sub_agent_node, create_role_router,
    create_finalizer_node,
)
```

- [ ] **Step 4: chat.py — 修改 SSE 过滤条件**

将当前过滤条件：
```python
if event.get("metadata", {}).get("langgraph_node", "") == "user_router":
    continue
```

改为：
```python
node = event.get("metadata", {}).get("langgraph_node", "")
if node not in ("finalizer", "denied"):
    continue
```

- [ ] **Step 5: 验证语法**

```bash
cd backend/agent
python -c "from app.graph.graph import create_router_graph; print('OK')"
```

Expected: 无报错，输出 `OK`

- [ ] **Step 6: 运行测试**

```bash
cd backend/agent
pytest -x -q 2>&1 | tail -5
```

Expected: 所有测试通过

- [ ] **Step 7: Commit**

```bash
git add backend/agent/app/graph/prompts.py \
       backend/agent/app/graph/nodes.py \
       backend/agent/app/graph/graph.py \
       backend/agent/app/service/chat.py
git commit -m "feat(agent): 新增 finalizer 节点格式化 sub-agent 输出"
```
