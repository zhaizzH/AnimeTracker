# 优化项 2: PendingAction 生命周期文档化

> 父任务：[`10-20-agent-module-optimization`](../10-20-agent-module-optimization/prd.md)
> **方案变更**：从「PendingActionLifecycle 类抽象」改为「三层同步设计显性化文档」——零代码改动，零风险。

## Goal

在 `backend/agent/app/chat/pending_action.py` 顶部加一段 ≤ 15 行的模块 docstring，把「ContextVar → Redis → LangGraph state」三层同步设计意图写下来，让未来的维护者**不用再问「这三层是怎么串起来的」**。

**本任务不改任何代码、不改任何测试**。这是纯文档化工作，把演化产物变成已记录的设计。

## Background · 为什么从「抽象类」退缩到「文档化」

通读代码后发现：

1. `emit_pending_action_*` 三接口（`pending_events.py`）**已经是良好抽象**——三个动词 + ContextVar 缓冲，职责清晰
2. 真正缺的不是「再抽一层类」，而是**「设计意图没人写下来」**——三层同步的**时序**（emit → 流结束回调 → 落 Redis → 下次请求注入 state）散落在 `pending_events.py` / `streaming.py` / `chat_store.py` / `runtime.py` 四个文件里，没有任何一处讲完整链路
3. 完整抽象（封 emit + 流回调 + Redis）需要动 SSE 链路（`streaming.py`），**违反父任务「不动 SSE 协议」约束**

结论：**文档化 > 抽象化**。让现有良好设计被看见，比为了抽象而抽象更有价值。

## Scope

### In Scope

- 在 `backend/agent/app/chat/pending_action.py` 顶部添加模块 docstring，覆盖：
  - 三层同步架构（ContextVar / Redis / LangGraph state）
  - 每层职责（写缓冲 / 持久化 / 运行时视图）
  - 同步时序（emit → 流结束 → 持久化 → 下次请求注入）
  - 为什么这样设计（CQRS 风格的读写分离；ContextVar 解耦工具与 SSE；Redis 做事实源）
- 在 `backend/agent/app/chat/pending_events.py` 顶部补一句指向 `pending_action.py` 的引用，方便读者跳转

### Out of Scope

- **不改任何 Python 代码**（连注释里的错字都不改）
- **不动 `pending_events.py` 的函数签名或实现**
- **不动 `streaming.py` / `chat_store.py` / `runtime.py` / 任何 actions/*.py**
- **不改测试**
- **不写新的 lifecycle 类**

## Acceptance Criteria

- [ ] `pending_action.py` 顶部有 ≤ 15 行的模块 docstring，包含：
  - [ ] 三层名称（ContextVar / Redis / LangGraph state）
  - [ ] 每层一句话职责
  - [ ] 同步时序一段话讲清（工具 emit → SSE 流结束回调消费 ContextVar → 写 Redis → 下次请求从 Redis 反序列化注入 state）
  - [ ] 设计动机一句话（CQRS 读写分离 / 解耦工具与 SSE）
- [ ] `pending_events.py` 顶部加一行 `See app/chat/pending_action.py 顶部 docstring 了解三层同步设计` 的引导注释
- [ ] `uv run pytest` 仍然 668 passed, 0 xfailed（**零代码改动 → 测试必然全绿**）
- [ ] `git diff main..HEAD -- backend/` 只动 `pending_action.py` 和 `pending_events.py` 两个文件的 docstring

## Constraints

1. **零代码改动**：只允许改 docstring / 模块注释
2. **docstring 用中文**（与项目现有规范一致）
3. **行数限制**：`pending_action.py` 顶部 docstring ≤ 15 行（含空行），`pending_events.py` 引导注释 ≤ 2 行
4. **准确性**：docstring 必须与代码现状一致，**不许描述「理想设计」**——只能描述「现有实现」

## Related

- 父任务 PRD：`../10-20-agent-module-optimization/prd.md`
- 涉及文件：
  - `backend/agent/app/chat/pending_action.py`（PendingAction 类型定义 + 4 类判别联合）
  - `backend/agent/app/chat/pending_events.py`（ContextVar 缓冲 + emit_*）
  - `backend/agent/app/adapters/redis/chat_store.py`（Redis 持久化）
  - `backend/agent/app/agent/state.py`（LangGraph state 注入）
  - `backend/agent/app/chat/streaming.py`（流结束回调消费 ContextVar）
