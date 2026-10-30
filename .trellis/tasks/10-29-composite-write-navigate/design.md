# 设计补充：复合指令「写入后导航」

> 承接 `prd.md` / `implement.md`。**D1 推翻了 implement.md 切片 1 的门控实现**——
> 原方案读的是过期 state，会拦掉它要保护的那次导航。

## D1 为什么不能读 `state["pending_action"]` 做门控

### 机制

`pending_action` 有三层（见 `app/chat/pending_action.py` 模块 docstring）：

| 层 | 角色 | 本回合内是否更新 |
|---|---|---|
| Redis | 持久事实源 | 只在 SSE 收尾回调写 |
| `AgentState.pending_action` | 运行时**只读视图** | 请求开始时从 Redis 注入一次，**之后不变** |
| ContextVar collector | 流内写缓冲 | 工具实时追加，收尾取最后一条 |

`PreviewableAction.execute` 写成功后只调 `emit_pending_action_clear()`（ContextVar），
**不会**改 state。所以在「写入已成功、模型紧接着调 `request_navigation`」那一刻：

```python
state["pending_action"].type   # 仍是 "ADD_TO_WISHLIST"
```

implement.md 的门控 `if pending.type in WRITE_PENDING_TYPES: reject` 会返回「写入尚未完成」，
**把唯一应该放行的那次导航拦死**。

多候选链路更糟：`SUBJECT_RESOLUTION` 同样粘着，若列入拒绝集全程堵死；
implement.md 说「不列入就不会堵」只对了一半——即便不列入，后续的 `ADD_TO_WISHLIST`
粘滞仍会在确认后拦导航。

### 推论

**门控信号必须来自本回合内实时可变的通道，不能来自 state。**

## D2 定案：turn-bag + 显式打标，门控读「本回合事实」

### 新增 TurnState

新建 `app/agent/client/actions/turn_state.py`：

```python
@dataclass
class TurnState:
    """单次图执行内的共享可变事实，供跨工具传递「本回合发生了什么」。

    与 PendingAction collector 同为 ContextVar 承载的流内状态，但用途不同：
    collector 是「待持久化的意图」，本对象是「已发生的事实」，不落 Redis。
    """
    pending_resolved: bool = False
```

安装点与 `pending_action_collector` 同一处：`ChatRunManager._drive` 里
`set_turn_state()` / `reset_turn_state(token)`（紧邻现有 `set_pending_action_collector`）。
理由相同：Token 绑定创建它的 Context，必须由 `_drive` 自己 set/reset。

### 打标点

只改 `PreviewableAction`（`app/agent/client/actions/previewable.py`）两处，
三条写链路（wishlist / collection_type / collection_progress）自动全覆盖：

```python
def cancel(self) -> dict:
    emit_pending_action_clear()
    mark_pending_resolved()      # 取消也是「本回合 pending 已结束」
    return {"cancelled": True}

def execute(self, ...):
    ...
    if isinstance(action, Clear):
        emit_pending_action_clear()
        mark_pending_resolved()  # 写入已定（成功或确定性失败），pending 结束
    elif isinstance(action, Replace):
        emit_pending_action_replace(action.new_pending)
    return response
```

**为什么只有 `pending_resolved` 一个布尔量，没有 `write_outcome` 三态**（2026-10-30 修正）：
初稿设计了 `write_outcome: Literal["none","succeeded","failed"]`，靠 response 里的
`succeeded` 列表判定成功。实现前核对三条链路，发现**只有 wishlist 有 `succeeded`**：

| 链路 | `classify_result` 成功形态 | 确定性失败形态 |
|---|---|---|
| wishlist | `{"succeeded": [...], "skipped": [...], "failed": [...]}` | `{"failed": [...]}`（`succeeded` 空） |
| collection_type | `{"state": "SAVED", ...}` | `{"state": "ALREADY_COLLECTED", ...}` / `{"error": True, "code": 409/404}` |
| collection_progress | `{"state": "COMPLETED", ...}` | `{"error": True, "code": 404}` |

要区分「真写入」与「确定性失败」就得为三条各写一套判据，脆弱且与链路细节耦合。
更重要的是：**这个区分对门控没用**。按 D3 的表，「确定性失败」与「成功」**都允许导航**
（区别只在 prompt 是否*主动*导航，那是 prompt 的事，TurnState 读不到）。
初稿门控伪码里两个分支也都 `return None`，三态本身就是死字段。

`Keep`（基础设施错误，写入结果不确定）**不**打标：pending 还在，下次重试仍被门控拦住，这是对的。

### 门控规则

`request_navigation` 在 recommend 注册时传 `gated=True`，工具**调用时**读 turn state：

```python
WRITE_PENDING_TYPES = {"ADD_TO_WISHLIST", "SET_COLLECTION_TYPE", "COLLECTION_PROGRESS_UPDATE"}
_SUBJECT_RESOLUTION = "SUBJECT_RESOLUTION"

def _navigation_gate(*, pending, turn: TurnState) -> dict | None:
    """写入类 pending 存在且本回合尚未结束时，拒绝导航。"""
    ptype = getattr(pending, "type", None)
    if ptype is None or turn.pending_resolved:
        return None      # 没有待确认动作，或本回合已结束（成功/取消/确定性失败）
    if ptype in WRITE_PENDING_TYPES or ptype == _SUBJECT_RESOLUTION:
        return {"error": True, "message": "写入尚未完成，请先确认或取消待确认动作"}
    return None
```

**关键点**：`state["pending_action"]` 是**回合开始时的 Redis 快照**，写成功后不会更新。
所以「pending 存在」这个信息本身不可靠——必须与 `turn.pending_resolved` 联合判断，
否则会在「写成功、正要导航」那一刻把唯一该放行的导航拦死。

### 为什么不直接读 `get_pending_action_event()`

零新增机制，但 `CLEAR` 同时覆盖「写成功」与「确定性失败」，语义混。
本 child 定案的 `pending_resolved` 同样做到「不需要导航工具去理解 PendingAction 的
持久化协议」，且比三态更省（三态对门控是死字段，见 D2）。耦合方向同样干净。

## D3 取消 / 过期 / 否定分支的行为

| 场景 | `state["pending_action"]` | `turn.pending_resolved` | 期望行为 |
|---|---|---|---|
| 用户确认，写成功 | 写入类（快照，未变） | `True` | **允许导航** |
| 用户取消（调 `cancel_*`） | 写入类（快照，未变） | `True` | 允许导航（等同纯导航），但 prompt 不应主动导航 |
| 用户否定但未调取消工具 | 写入类 | `False` | **拒绝导航** |
| pending 已过期 | 写入类 | `False`（`Keep` 不打标） | **拒绝导航** |
| 写入确定性失败（全部已收藏） | 写入类 | `True`（`Clear` 打标） | 允许导航，但 prompt 不应主动导航 |
| 基础设施错误（`Keep`） | 写入类 | `False` | **拒绝导航**（pending 还在，可重试） |
| 多候选未选（`SUBJECT_RESOLUTION`） | `SUBJECT_RESOLUTION` | `False` | **拒绝导航** |
| 纯导航（无 pending） | `None` | 无关 | 允许 |

「允许但 prompt 不应主动导航」的两行：硬门控只保证**不违反先写后导航**，
是否导航交给模型按 prompt 决定。这两行不需要额外硬约束——导航可逆、无持久副作用，
多跳一次不是安全事故。真正必须硬拦的是「写入未完成就导航」。

## D4 prompt 更新

`resources/prompt/client/recommend_agent_prompt.md` 追加（与现有中文风格一致）：

```
## 复合指令：写入后跳转

用户说「把 X 加入想看，然后打开我的收藏」这类指令时：
- 严格先完成写入，再调用 request_navigation；顺序不可颠倒。
- 预览阶段、等待用户确认时，不得调用 request_navigation。
- 用户取消、否定，或待确认动作已过期时，不得调用 request_navigation。
- 多候选标题场景下，须等「选中 → 预览 → 确认」全部完成后才可调用。
- 写入工具返回 error 时，不得调用 request_navigation，先向用户说明原因。
- 一次回合最多调用一次 request_navigation。
```

**Managed prompt 注意**：prompt 以 Redis 为准、本地文件兜底
（`prompt_repository.get(key, path)`）。改完文件后必须确认线上 Redis 里的
`client_recommend_agent_prompt` 同步更新，否则本地测试过、线上不生效。
这一条要写进验收清单，不能只改文件。

search / discover 两个 prompt **不加这段**——它们没有写工具，
只需要知道「可以调用 `request_navigation` 跳页」这一句基础说明即可
（属 child 3 的注册工作，但其 prompt 改动在 child 3 验收里）。

## D5 工具注册的变化

child 3 已在三个 Domain agent 注册 `request_navigation`，工厂签名预留了
`turn_state: TurnState | None = None`。本 child 只改 recommend 的注册点：

```python
# app/agent/client/recommend.py
request_navigation = build_request_navigation_tool(turn_state=get_turn_state())
```

`get_turn_state()` 必须在**工具调用时**读取（ContextVar），不能在工厂构造期定值——
工厂在 lifespan 组装期跑一次，那时没有 turn 上下文。因此门控要写在工具函数体里：

```python
@tool
def request_navigation(...):
    turn = get_turn_state()      # 调用时才读；工厂期读到的是「无回合」
    gate = _navigation_gate(pending=state.get("pending_action"), turn=turn)
    if gate is not None:
        return _error_command(gate["message"], tool_call_id)
```

工厂参数退化为「是否启用门控」的开关，而非具体实例。
child 3 实际交付时**没有预留任何参数位**（刻意的：留一个调用期不读的开关会让 `gated=True` 静默不生效）。
本 child 需给 `build_request_navigation_tool` 加回 `gated: bool` 参数，并在工具内部调用时 `get_turn_state()`。

## D6 测试清单

- **门控正向**：state 里 pending 为 `ADD_TO_WISHLIST`，turn-bag 为 `pending_resolved=True`
  → 允许写 `navigation_intent`（锁 D1 的核心修复）
- **门控负向**：pending 为写入类、turn-bag 默认 → 拒绝且 state 无 intent
- **多候选**：`SUBJECT_RESOLUTION` 在、无打标 → 拒绝；
  模拟走完选候选 → 预览 → 确认（打标）→ 允许
- **取消分支**：`pending_resolved=True` → 不拒绝（行为由 prompt 决定）
- **过期分支**：pending 过期且无打标 → 拒绝
- **确定性失败**：`Clear` 同样打标 → 允许导航（与成功同待遇，区别只在 prompt）
- **不回归**：纯导航三节点可用；`admin_agent` 无该工具；
  三条写链路既有测试全绿（`PreviewableAction` 加了打标，不能改变其返回 dict）

## 端到端验收（人工 + 自动化各一遍）

1. 「把《孤独摇滚》加入想看，然后打开我的收藏」→ 预览 → 确认 → 写成功 →
   跳 `/my-collections`，浮层保持打开，出现 `⚡ 已跳转到「我的收藏」`
2. 同上但回「取消」→ 不写入，不导航
3. 同上但 pending 过期 → 提示重新发起，不导航
4. 多候选标题 → 选候选 → 预览 → 确认 → 写成功 → 才导航
5. 「打开我的收藏」（纯导航）→ 不触发任何写工具
6. 断线重连 → 不重复导航（由 child 2 的 `replayed` 标记保证）

## 不做

- 不重复注册工具
- 不支持「导航后再写入」
- 不做跨轮导航队列（turn-bag 只活在单次图执行内，跨轮即失效，这是刻意的）
- 不把导航做成 PendingAction
