# 技术设计：Agent 驱动 UI

> 完整契约见 [.trellis/spec/backend/agent-ui-actions.md](../../spec/backend/agent-ui-actions.md)。本文件只记 tradeoff 与跨 child 的边界，不复制 spec 全文。

## 核心权衡

### 1. 后路由链，而非 gateway 拆意图

**选**：Domain agent 结束后按 `navigation_intent` 是否非空走条件边。

**否掉**：
- gateway 输出 `{"steps":[...]}` —— 把单标签分类器变成规划器，`_resolve_routing_result` 的全部 JSON 校验要重写，错误面扩大
- 导航工具塞进现有 Domain agent —— 破坏「路由即工具权限边界」；ReAct 循环内模型可能在写入完成前导航

**代价**：图从单跳变两跳，`graph.py` 的条件边逻辑变复杂；但每跳仍是无环的。

### 2. `navigation_emitter` 是纯函数，不是 Domain agent

**选**：读 state → 白名单映射 → emit → 清空。零 LLM、零 prompt、零 answer 文本。

**理由**：导航语义在前序节点已决定完，这里只剩「意图 → URL」的翻译，没有需要语言理解的部分。用 LLM 只会引入拼错 path 的风险。

**命名**：按 GLOSSARY 对 `Domain agent` 的定义（检索/发现/推荐三个面向用户的节点），它不叫 `navigate_agent`，避免暗示它有对话能力。

**静默的理由**：「已为你打开…」在前端尚未跳转时说出口等于撒谎；且前序节点已回答，再补一句会让用户看到两段割裂文本。

### 3. 重放过滤放读取侧，不放写入侧

**选**：`ui_action` 仍入 `run.events` 缓冲，`subscribe(after=cursor)` 重放旧帧时按类型跳过。

**否掉**：`_drive()` 里就不入缓冲 —— 改的是写入路径，而需要保护的是**重放语义**。且会失去「当时发生了什么」的可回溯性。

**否掉**：前端按 `action_id` 去重 —— 把不变量分散到每个消费者，且需要跨会话唯一的 id，多一个状态要维护。

### 4. 固定 action 枚举，不做自由 path

模型只选 action + 参数，服务端构造 URL。自由 path 下模型可拼出 `/admin`、`javascript:` 或错误 path 导致白屏。与 `RetrievalQuery` 用 Pydantic 卡字段边界同理。

### 5. 前端浮层复用，不新建

`AIAssistantFloat`（97 行）已挂在 `ClientLayout`，会话 hook 复用 `AgentConversation`。唯一障碍是 `useEffect(() => setOpen(false), [location.key])`。改造点是**加一个「agent 发起」标记**，不是重写组件。

## 跨 child 边界

```
child 1 (frontend-url-state)     child 2 (ui-action-event)      child 3 (navigation-graph)
┌─────────────────────────┐      ┌──────────────────────┐       ┌────────────────────┐
│ URL 能表达全部筛选       │      │ 事件能从前端收到      │       │ 图能产生事件        │
│ 浮层提供「agent 导航」标记│─────▶│ onUiAction 回调注入点 │◀──────│ emit_ui_action     │
└─────────────────────────┘      └──────────────────────┘       └────────────────────┘
        独立可交付                        │                              │
                                          └──────────┬─────────────────┘
                                                     ▼
                                        child 4 (composite-write-navigate)
                                        写入完成后才调 request_navigation
```

- child 1 与 child 2 **可并行**，无代码交叠（一个纯前端页面/浮层，一个跨层事件通道）
- child 3 必须等 child 2（没有事件通道，emitter 无处可发）
- child 4 必须等 child 3（工具与图都得先在）
- child 1 即使后面三个都不做也有独立价值：筛选可分享、刷新不丢状态

## 后补：两处机制级修正

### A. 工具写 state 用 `Command`，不走 ContextVar

初稿写「`request_navigation` 返回 `{"navigation_intent": ...}`」。**这是错的**：普通工具返回值会变成 `ToolMessage` 内容，不会进 state。现有写工具走 `emit_pending_action_*` ContextVar 是因为 PendingAction 需要 SSE 收尾时落 Redis；`navigation_intent` 只在图内活、无需持久化，因此用 LangGraph 的 `Command(update={"navigation_intent": ...})` 即可，且能被图的条件边读到。

### B. 纯导航请求的归属节点

初稿把 `request_navigation` 只给 `recommend_agent`，则「打开我的收藏」这类**无写入**导航会被 gateway 路由到 `search_agent`（那里没工具）而失败。

**选**：`request_navigation` 注册到**全部三个 Domain agent**；`recommend_agent` 额外受「写入未完成不得导航」的硬约束。

**理由**：导航是无副作用的只读意图，不存在「谁有权导航」的边界问题——真正的权限边界在**写工具**上，那条不变量不动。把导航限死在 recommend 反而制造了「纯导航请求必须被误判为推荐意图」的新问题。

**对 child 4 的影响**：child 4 不再是「给 recommend 注册工具」，而是「给 recommend 增加写入门控 + prompt」。child 3 负责三节点通用注册。

## 关键风险

| 风险 | 缓解 |
|---|---|
| SSE 两层枚举漏改一处 → 契约测试红 | spec §6 已列 7 处清单；契约测试的传递断言会兜住 |
| Java 透传若有类型白名单 → 事件被吞 | child 2 的验收里含人工核对 `AgentSseResponseWriter.java` |
| 服务端构造的 query 键名与前端不一致 → 跳转后筛选不生效 | child 3 验收明确要求对照三个页面的 `useSearchParams` 键名 |
| 复合指令在预览阶段就导航 | child 4 验收含「取消则不导航」「过期则不导航」两条否定用例 |
| 浮层标记位被用户普通导航误触发 | child 1 要求「未标记时照旧关闭」不回归 |
