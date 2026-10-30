# 执行计划：复合指令「写入后导航」

**前置**：`navigation-graph` 已归档。

> **2026-10-29 修订**：原切片 1 的门控读 `state["pending_action"]`，但那是**回合开始时的快照**，
> 写成功后不会更新——会在「写成功正要导航」时把它拦死。改为 turn-bag 方案，
> 以 [design.md](./design.md) D1/D2 为准；`SUBJECT_RESOLUTION` 也随之**列入**拒绝集。

## 切片 1：TurnState 与打标点

新文件 `app/agent/client/actions/turn_state.py`：

```python
@dataclass
class TurnState:
    pending_resolved: bool = False
```

ContextVar 承载，`set_turn_state()` / `get_turn_state()` / `reset_turn_state(token)` /
`mark_pending_resolved()`，安装点在 `ChatRunManager._drive`（紧邻现有
`set_pending_action_collector`，同样的 Token 纪律）。

打标改 `PreviewableAction` 的 **两个** 方法（`cancel` 与 `execute`），三条写链路自动全覆盖：

```python
def cancel(self) -> dict:
    emit_pending_action_clear()
    mark_pending_resolved()      # 取消也是「本回合 pending 已结束」
    return {"cancelled": True}

def execute(self, ...):
    ...
    if isinstance(action, Clear):
        emit_pending_action_clear()
        mark_pending_resolved()
    elif isinstance(action, Replace):
        emit_pending_action_replace(action.new_pending)
    return response
```

**只有一个布尔量，没有 `write_outcome` 三态**（2026-10-30 修正，详见 design D2）：
三条链路的成功形态各不相同（只有 wishlist 有 `succeeded` 列表，
另两条是 `{"state": "SAVED"}` / `{"state": "COMPLETED"}`），
而「确定性失败」与「成功」对门控**同等放行**（区别只在 prompt 是否主动导航）。
`Keep`（基础设施错误）**不**打标——pending 还在，可重试，门控应继续拦。

## 切片 2：门控（工具已在 child 3 注册）

文件：`app/agent/client/navigation.py`

**child 3 交付的签名是 `build_request_navigation_tool()`，没有 `gated` 参数**
（刻意不留死开关）。本 child 先加回 `*, gated: bool = False`。

```python
WRITE_PENDING_TYPES = {"ADD_TO_WISHLIST", "SET_COLLECTION_TYPE", "COLLECTION_PROGRESS_UPDATE"}
_SUBJECT_RESOLUTION = "SUBJECT_RESOLUTION"

def _navigation_gate(*, pending, turn) -> dict | None:
    ptype = getattr(pending, "type", None)
    if ptype is None or turn.pending_resolved:
        return None   # 无待确认动作，或本回合已结束（成功/取消/确定性失败）
    if ptype in WRITE_PENDING_TYPES or ptype == _SUBJECT_RESOLUTION:
        return {"error": True, "message": "写入尚未完成，请先确认或取消待确认动作"}
    return None
```

- `state["pending_action"]` 是**回合开始时的 Redis 快照**，写成功后不更新，
  所以必须与 `turn.pending_resolved` **联合**判断，否则会在「写成功、正要导航」时把唯一该放行的导航拦死
- `SUBJECT_RESOLUTION` **列入**拒绝集：门控读 turn-bag 而非粘滞 state，
  走完「选候选 → 预览 → 确认」后自然放行，不会堵死多候选链路
- `gated=True` 时在**工具函数体里**读 `get_turn_state()` 并跑门控（不能工厂构造期定值）
- 拒绝时返回 `Command(update={"messages": [ToolMessage(...)]})`，不写 `navigation_intent`

**这是本任务的关键安全点**：不能把「先写后导航」只交给 prompt 自觉。

## 切片 3：注册点改造

**child 3 交付时删掉了 `gated` 参数**（留一个调用期不读的开关会让传 `True` 静默不生效），所以本 child 要先给
`build_request_navigation_tool` 加回 `gated: bool` 参数：

- `app/agent/client/recommend.py`：`build_request_navigation_tool(gated=True)`
- search / discover 保持 `build_request_navigation_tool()`（纯导航无门控，不传参）

加回参数时**门控必须在工具调用时读取** `get_turn_state()`，不能在工厂构造期定值——工厂在 lifespan 组装期
跑一次，那时没有 turn 上下文。

## 切片 4：端到端验证

- 「把 X 加入想看，然后打开我的收藏」全链路
- 「取消」分支：不写入也不导航
- 过期分支：提示重新发起，不导航
- 多候选分支：选候选 → 预览 → 确认 → 写 → 导航
- 纯导航不触发写工具

## 测试

- **门控正向**：state 里 pending 为 `ADD_TO_WISHLIST`、turn-bag 为 `pending_resolved=True` → 允许（锁 D1 核心修复）
- 预览阶段调 `request_navigation` 被拒（pending 为写入类且未清空）
- `SUBJECT_RESOLUTION` 未走完时被拒；走完后放行（多候选链路不堵死）
- 取消 / 过期 / 确定性失败三分支行为符合 design D3 表
- `PreviewableAction` 三条链路返回 dict 不变（加打标不改对外形态）
- 其他节点行为不回归

## 验证

```bash
cd backend/agent && uv run pytest
cd ../business && mvn -B clean test
```

## 公共测试缝（已确认，开工前定）

基线：`cd backend/agent && uv run pytest -q` → **899 passed**（2026-10-30 实测）。

| 缝 | 位置 | 能捕获 | 捕获不到 |
|---|---|---|---|
| 门控规则（纯函数） | **新** `tests/agent/test_navigation_gate.py` | 八种 `(pending, resolved)` 组合的放行/拒绝、`Keep` 不打标 | 真实写入链路 |
| TurnState 生命周期 | `tests/agent/test_chat_run_manager.py`（已存在，扩） | `_drive` 装了 turn state、写成功后 `pending_resolved=True`、`Keep` 保持 False | —— |
| 三条写链路不回归 | `tests/agent/test_wishlist.py` / `test_collection_type.py` / `test_collection_progress.py`（均已存在） | 打标没改变它们的返回 dict | —— |
| 工具门控接线 | `tests/agent/test_request_navigation_tool.py`（已存在，child 3 建的） | `gated=True` + 写入类 pending + 未 resolved → 拒绝且不写 intent；`gated=False` 无门控 | 真实模型是否遵守 prompt |
| prompt 文本 | `tests/agent/test_client_prompt_contract.py`（已存在） | recommend prompt 含「写完后才可导航」「预览阶段不得导航」 | 模型遵循程度 |

**必须遵守的断言强度**：
- 门控是纯函数，八种组合**逐条参数化**，不要合成一个「短路」测试。
- 「写入成功后允许导航」这条必须有：它是原设计的缺陷点（读 state 快照会把它拦死）。
- 打标改动后，三条写链路既有测试必须保持绿——它们的返回 dict 是模型可见的契约。

## 不做

- 不重复注册工具（child 3 已完成）
- 不支持「导航后再写入」
- 不做跨轮导航队列
