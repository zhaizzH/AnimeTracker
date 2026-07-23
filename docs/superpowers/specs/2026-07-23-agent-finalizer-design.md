# Agent Finalizer 节点 — 回复格式化

## 问题

Sub-agent（search/discover/recommend）的输出太啰嗦：包含 emoji、表格、后续引导提问（"欢迎告诉我番剧名或ID"），信息呈现不简洁。

## 方案

在 LangGraph 尾部新增一个 **finalizer 节点**，sub-agent 的输出先经过 finalizer 格式化后再返回给用户。

### 架构变化

当前：
```
entry → router → sub-agent → END
```

改为：
```
                    ┌─ search →┐
entry → router → ──┼─ discover → finalizer → END
                   └─ recommend ┘

admin → admin_router → denied → END  （不变，不走 finalizer）
```

### 文件改动

| 文件 | 改动 |
|---|---|
| `app/graph/prompts.py` | 新增 `FINALIZER_PROMPT`（列表格式） |
| `app/graph/nodes.py` | 新增 `create_finalizer_node(llm)` |
| `app/graph/graph.py` | 注册 finalizer 节点，sub-agent → finalizer → END |
| `app/service/chat.py` | SSE 过滤改为只放行 `finalizer` 和 `denied` |

### Finalizer 节点逻辑

```python
def create_finalizer_node(llm):
    async def finalizer(state: AgentState) -> dict:
        prompt = FINALIZER_PROMPT.format(content=state.final_output)
        resp = await llm.ainvoke([SystemMessage(content=prompt)])
        return {"final_output": resp.content}
    return finalizer
```

读取 `state.final_output`（sub-agent 的原始输出），用 LLM 重新格式化后覆盖写入。

### Finalizer Prompt

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

### SSE 过滤变更

```python
# 改前：跳过 user_router
if node == "user_router":
    continue

# 改后：只放行 finalizer 和 denied
if node not in ("finalizer", "denied"):
    continue
```

### 影响

- 多一次 LLM 调用（额外 ~1-2 秒 + 少量 token）
- sub-agent 的 verbose 输出不再到前端，用户只看到 finalizer 的流式输出
- admin denied 路径不受影响
