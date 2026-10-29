# 技术设计：chat run 解耦

> 关联 PRD：[prd.md](./prd.md)。方向 A（生产端与请求解耦）+ 重连同一 run（B）+ Task + Redis 状态标记（B）。
> 2026-10-23 经 `/grill-me` 拷问（Q1–Q14）修订，关键修正见 [decisions.md](./decisions.md) D3–D10。核心修正：stop 改为逻辑停止（物理取消在同步节点架构下不存在）；消息顺序改由 per-session persist future 保证；部分答案用文本前缀标记。

## 1. 设计目标

把「一次对话生成」从「一次 HTTP 请求」里拆出来，成为一个**有自己生命周期的 run**：

- **run**：跑完 workflow、产出事件、落库。生命周期 = `asyncio.Task`，只有进程关闭才取消。
- **订阅者**：HTTP SSE 响应。可以有 0 个（用户已刷新）或 1+ 个（重连）。断连 = 退订，不取消 run。

这样 `stream_agent_events` 的收尾（`on_answer_completed` / `on_pending_action`）由 **run 任务读到末尾**来保证，而不是由「有人在读」保证——直接消灭 PRD 里的根因 1 与 2，不需要把收尾逻辑挪进 `finally`。

## 2. 新增模块

### 2.1 `app/chat/runs.py`

```python
class RunStatus(str, Enum):
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ChatRun:
    run_id: str
    session_id: str
    user_id: int
    status: RunStatus
    events: list[AgentEvent]        # 全量缓冲，供重连回放
    buffer_start: int               # 缓冲截断后第一条事件的序号（Q14）
    subscribers: set[asyncio.Queue[AgentEvent | None]]
    task: asyncio.Task | None
    persist_future: asyncio.Future  # D4: 持久化完成信号

class ChatRunManager:
    def __init__(self, store: ChatStore, ttl_seconds: int = 900): ...
    async def start(self, *, session_id, user_id, events: AsyncIterator[AgentEvent]) -> ChatRun
    def get(self, run_id: str) -> ChatRun | None
    def active_for_session(self, session_id: str) -> ChatRun | None  # 只认 RUNNING（D8）
    async def stop(self, run_id: str) -> bool  # 逻辑停止（D3）：标记 cancelled，立即返回
    async def subscribe(self, run_id: str, *, after: int = 0) -> AsyncIterator[AgentEvent]
    async def shutdown(self) -> None  # cancel + gather + 10s 超时（D9）
```

要点：

- `start()` 在 `create_task` **之前** `set_event_sink(...)` + `set_pending_action_collector()`（Q3：contextvar 在 create_task 时拷贝，`_drive` 内部继承）。token 传进 `_drive`，finally 里 `reset`。
- `start()` 在 service 层 `save_message("user", ...)` 之前 `await asyncio.wait_for(prev.persist_future, timeout=5.0)`（D4），超时降级继续。
- `_drive()` 内部 `async for event in events:` → 累积 `aggregated_answer` / `used_tools` → 追加 `events` 缓冲 → 广播。结束时写入 Redis 终态，resolve `persist_future`。
- **stop（D3）**：标记 `status=cancelled`，合成未闭合工具的 `state=end, result=aborted` 帧 + END 帧广播，立即返回。**不 cancel 底层 task**（同步节点架构下 cancel 无效，见 D3）。底层 task 自然跑完后落库部分答案（带 D5 前缀）。
- **封存（D6）**：stop 后事件缓冲定格，之后产出的事件丢弃。`_drive` 继续消费（为落库），但不再对外可见。
- 缓冲上限：事件数 2000 / 字节 1MB。超限后 `buffer_start` 前移；`subscribe(after)` 检测 `after < buffer_start` 时先发 STATUS 提示帧（Q14）。
- `subscribe(after)`：先回放 `events[after:]`，然后挂 `asyncio.Queue` 持续推送；run 终态时推 `None` 哨兵。**订阅者退出（GeneratorExit）只做退订**，绝不 cancel run task。
- `active_for_session`（D8）：只认 `status=RUNNING`。cancelled 不算 active。
- `shutdown()`（D9）：cancel 所有 run task + `gather(return_exceptions=True)`，外包 `asyncio.wait_for(timeout=10s)`。超时打日志放弃。
- **stale 收敛（D9）**：懒加载。`active_for_session` / `get` 读到 `status=running` 但内存无 run → 收敛 `failed` + 补写「生成已中断」。

### 2.2 Redis run 状态（不用新表，复用既有 Redis）

| key | 值 | TTL |
|---|---|---|
| `agent:run:{run_id}` | hash: `session_id` / `user_id` / `status` / `updated_at` / `event_count` | 900s |
| `agent:session_runs:{session_id}` | 最近 run_id（字符串） | 900s |

进程重启后，`RUNNING` 的 run 无法恢复执行。**懒加载收敛**（D9）：`active_for_session` / `get` 读到 `status=running` 且内存无此 run → 收敛为 `failed` 并补一条「生成已中断」assistant 消息。不做启动时扫描。

## 3. 改动点

### 3.1 `app/chat/service.py`

新增 `start_run(...) -> ChatRun`：原 `stream_chat(...)` 的 prepare 逻辑（落 user 消息、读 history、读 pending_action、构造 initial_state）保持不动，末尾改为交给 manager：

```python
async def start_run(self, *, session_id, content, user_id, role, token="") -> ChatRun:
    events = await self._prepare_events(...)   # 原 stream_chat 的 body，返回 AsyncIterator
    return await self.runs.start(
        session_id=session_id, user_id=user_id, events=events,
    )
```

保留 `stream_chat` 作为薄壳（内部 `start_run` 后 `subscribe`），避免破坏既有测试。

### 3.2 `app/api/chat.py`

| 方法 | 路径 | 语义 |
|---|---|---|
| `POST` | `/stream` | 启动 run，**订阅并推送**；SSE 的第一帧 meta 带 `run_id`，客户端存下用于重连 |
| `GET` | `/runs/{run_id}/stream?after=N` | 重连订阅同一 run，从第 N 个事件起推送 |
| `GET` | `/sessions/{session_id}/run` | 返回该会话当前/最近的 run 状态（`run_id` + `status`），供刷新后决策 |

- `POST /stream` 的既有响应契约（media type、header、唯一 `is_end` 帧）不变 → R4 不回归。
- `GET /runs/{run_id}/stream` 的 `run_id` 必须校验归属：run 的 `user_id` 与 JWT 一致，否则 404（不暴露存在性）。

### 3.3 `app/api/sse.py`

`create_sse_response` 保持签名不变；新增 `run_id` 注入通过 `AgentEvent.meta`（已有字段），不新增参数。

### 3.4 `app/chat/streaming.py`

**尽量不改**。只做一处加固：`finally` 里的 `producer.cancel()` 语义在 run 化之后应只在「run 任务自身被取消」时发生。因为 run 任务现在是唯一消费者，这一行天然正确——**保留即可，但要加注释说明其触发条件已从「客户端断连」变为「进程关闭」**。

另加：`on_answer_completed` 之前合成工具终态（见 §4.2）。

### 3.5 `main.py`

- lifespan 里创建 `ChatRunManager`，`app.state.chat_runs = manager`。
- 关闭时 `await manager.shutdown()`：取消所有 run task 并等待，保证 event sink / contextvar 清理。

### 3.6 前端 `packages/shared/src/hooks/useAgentChat.ts`

- `send()` 记录首个 SSE 帧带来的 `run_id`。
- 挂载/切换会话时：`GET /sessions/{id}/run` → 若 `running`，用 `GET /runs/{run_id}/stream?after=0` 订阅回放，UI 继续增量渲染。
- `stop()` 改为调用新的取消接口（`POST /runs/{run_id}/stop`，**新增**，语义为“用户主动停止” → run 状态 `cancelled` 但仍落库已生成部分）。这是与“刷新断连”的关键区分：刷新不退订语义为取消。

### 3.7 Java 代理

`ClientAgentController` / `AdminAgentController` 新增：

- `GET /runs/{runId}/stream`（SSE 透传，复用 `agentService.stream` + `HttpMethod.GET`）
- `GET /sessions/{sessionId}/run`
- `POST /runs/{runId}/stop`

`AgentApiPaths` 同步常量；Controller 测试补契约。

## 4. 四项副作用的具体落法

### 4.1 孤立 user 消息

`_drive()` 保证每次 run 结束（含失败/取消）都调用一次落库：

- 成功：正常 `on_answer_completed` 写入完整答案。
- 失败/取消且已聚合到部分答案：写入部分答案，content 前加 `*（生成已中断）*` 前缀（D5）。
- 失败/取消且无任何答案：写入一条 `*（生成已中断）*` assistant 消息（D5）。

实现位置：`ChatRunManager._drive()` 的 `finally`，以幂等方式补写（`persisted` 标记 + `persist_future` resolve）。

### 4.2 工具调用中间态

- **仅 stop 路径**：`stop()` 被调用时，若存在 `state=start` 但无匹配终态的 `function_call`，由 manager 合成一条 `state=end, result=aborted, message="生成已中断"` 事件，先广播再终止。订阅者（前端）据此把 `running` 收敛为「已中断」。
- **异常路径不合成**：流程抛异常导致 run 终止时，不发 `aborted` 帧——前端已由 `status=error` 帧得知出错，`aborted` 会让「系统错误」被误读为「用户主动停止」。
- **断连路径不合成**：断连时 run 还在跑，工具会自然闭合（Q12）。

### 4.3 pending_action

- 正常路径（含断连后台跑完）：`_drive` finally 里 `get_pending_action_event()` + 调 `on_pending_action`（Q3：collector 由 `start()` 在 create_task 前 set，`_drive` 继承）。
- 被 stop 的 run（D7）：**跳过** `on_pending_action`。已写入 Redis 的旧 pending_action 由 TTL（600s）自然过期。
- 失败路径：collector 在 finally 中 `reset`，不写半成品。

### 4.4 资源泄漏 / producer 取消

- 客户端断连 → 只 `unsubscribe`，不 `task.cancel()`。
- `shutdown()` → 取消全部 run task，`gather(return_exceptions=True)` + `wait_for(timeout=10s)`（D9）。
- 订阅者队列在退订时从 `subscribers` 集合移除，队列对象随引用消失。
- contextvar token 由 `start()` 在 create_task 前 set，`_drive` finally 里 reset（Q3）。

## 5. 关键不变量（测试要钉住）

1. 断连不取消 run：订阅者 `aclose()` 后，run task 仍 `not done()`，最终 `status=done`。
2. 断连后答案落库：`get_messages` 能读到完整 assistant 内容。
3. 重连回放不漏不重：`after=N` 精确从第 N 条开始，总事件序列 == 全量缓冲。缓冲截断时 `after < buffer_start` 降级提示（Q14）。
4. 恰好一个 `is_end` 帧（既有契约）。
5. 每会话最多一个 active run（D8：cancelled 不算 active）；同会话并发 `POST /stream` 409，见 §9。
6. 每 run 恰好一条 assistant 消息落库（幂等标记 + persist_future）。
7. stop 立即返回（D3）：`POST /runs/{id}/stop` 延迟 ~5ms，不等底层节点跑完。
8. stop 后部分答案落库带 `*（生成已中断）*` 前缀（D5），pending_action 不落（D7）。

## 6. 进程重启边界

新增 run 不持久化执行状态，重启后不可恢复。防线（D9）：

- **懒加载 stale 收敛**：`active_for_session` / `get` 读到 `running` 但内存无此 run → 收敛 `failed` + 补「生成已中断」消息。不做启动时扫描。
- **shutdown 10s 超时**：cancel + gather + `wait_for(timeout=10s)`，超时打日志放弃。
- 在 `agent-guidelines.md` 记录该边界，避免后续误以为「后台跑完」在重启后仍成立。

## 7. 拒绝的方案

- **把收尾挪进 `try/finally`**：只解决「丢失」，不解决「跑完」；用户明确要求后台跑完。
- **引入 Celery/RQ**：仓库无该基础设施，PRD 明确禁止新增常驻队列；且 run 需要复用进程内 graph 与 token。
- **SSE 里做重放不建 run**：无法跨请求续传增量，刷新即断。

## 8. 风险

| 风险 | 缓解 |
|---|---|
| 事件缓冲占内存（长回答 × 多并发） | 事件数/字节双上限，超限降级为「从历史读」 |
| 重复落库 | `persisted` 标记 + 幂等测试 |
| 前端重连风暴 | `after` 游标 + 退避重连，最多 N 次 |
| Spring 代理 GET SSE 兼容 | 复用既有 `agentService.stream`，补 Controller 测试 |
| `asyncio.Task` 强引用丢失导致中途回收 | manager 持强引用集合，测试断言 | 

## 9. 并发写入语义与 steering（2026-10-22 核实）

用户要求同会话并发时提供两个选择：**直接打断并插入**、**调整方向**。两者代价差一个数量级，必须分开。

### 9.1 打断并插入（本次范围内）

- `POST /runs/{run_id}/stop` → **逻辑停止**（D3）：立即标记 `cancelled` + 合成工具终态帧 + END 帧 + 返回 200。底层 task 自然跑完后落库部分答案（D5 前缀）。
- 前端确认 stop 200 后 `POST /stream` 启动新 run；消息顺序由 per-session persist future 保证（D4）。
- 这是 run 解耦的**自然产物**，后端几乎零额外成本；用户感知就是「打断并插入」。

### 9.2 中途注入指令改方向（**不在本次范围，需先重构执行模型**）

已核实现有架构**无法支持**真正的 mid-stream steering，不是加个参数的事：

| 事实 | 位置 | 影响 |
|---|---|---|
| 图无 checkpointer | `app/agent/graph.py:54` `graph.compile()` | LangGraph 的 `interrupt()`/`Command(resume=...)` 依赖 checkpoint 才能挂起后恢复，无 checkpointer 就无从「回到中途」 |
| `interrupt`/`Command`/`checkpointer` 全仓零引用 | `grep -rn` 复核 | 既无机制也无预留钩子 |
| 节点执行是**同步**的 | `app/agent/run.py:74` `run_domain_agent`，内部 `agent_stream` 经 `_run_async` | 返回时模型调用已全部结束 |
| `_run_async` 绕到线程池 | `app/agent/runtime.py:13-24` `ThreadPoolExecutor` + `asyncio.run` | 跨事件循环，注入指令无法安全投递到正在跑的协程 |

真正可用的插入点只有两处，**都不是「中途」**：`history_messages`（`run.py:100`，输入已交给模型）与「节点返回后重跑节点」（本质是再跑一轮）。

**升级为真 steering 的前置条件**（独立任务，风险与「修断连」不同量级）：

1. 给图加 checkpointer（thread_id = run_id），并确认 `AsyncRedisSaver` 或等价方案的依赖。
2. 节点改 async，拆掉 `_run_async` 线程池绕路，否则指令无法注入正在执行的协程。
3. 接入 `HumanInTheLoop` 类中间件或自行在 `create_agent` 的多轮循环里注入消息。
4. 扩 `AgentState`，改 `graph.py` 条件边与 5 个节点（search/discover/recommend/admin/gateway）。
5. 定义注入事件在 SSE 上的 wire 形态（需要同时改 `events.py`、`schemas/sse.py`、前端 `useAgentChat.ts` 与契约测试）。

> 结论：先把 run 解耦做对（断连不丢、能停、能落库），steering 再作为独立任务立项。不要在同一次改动里混着做。
