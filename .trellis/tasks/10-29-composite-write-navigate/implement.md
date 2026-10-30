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
    write_outcome: Literal["none", "succeeded", "failed"] = "none"
    pending_cleared: bool = False
```

ContextVar 承载，`set_turn_state()` / `get_turn_state()` / `reset_turn_state(token)`，
安装点在 `ChatRunManager._drive`（紧邻现有 `set_pending_action_collector`，同样的 Token 纪律）。

打标只改 `PreviewableAction.execute` 一处，三条写链路全覆盖：

```python
if isinstance(action, Clear):
    emit_pending_action_clear()
    mark_write_cleared(succeeded=bool(response.get("succeeded")))
```

**不能用 `Clear` 本身当「写成功」**：确定性失败（已收藏、条目失败）也发 `Clear`，
必须看 `succeeded` 列表是否非空。

## 切片 2：门控（工具已在 child 3 注册）

文件：`app/agent/client/navigation.py`

```python
def _navigation_gate(*, pending, turn) -> dict | None:
    ptype = getattr(pending, "type", None)
    if ptype in WRITE_PENDING_TYPES or ptype == SUBJECT_RESOLUTION:
        if turn.pending_cleared:
            return None            # 本回合已清空（写成功 / 取消 / 确定性失败）
        return {"error": True, "message": "写入尚未完成，请先确认或取消待确认动作"}
    return None
```

- `WRITE_PENDING_TYPES = {"ADD_TO_WISHLIST", "SET_COLLECTION_TYPE", "COLLECTION_PROGRESS_UPDATE"}`
- `SUBJECT_RESOLUTION` **列入**拒绝集：门控现在读 turn-bag 而非粘滞 state，
  走完「选候选 → 预览 → 确认」后 `pending_cleared=True` 自然放行，不会堵死多候选链路
- `turn` 在工具内部**调用时** `get_turn_state()`，不在工厂构造期定值（lifespan 组装时无 turn 上下文）
- 返回错误走 `Command(update={"messages": [ToolMessage(...)]})`，不写 `navigation_intent`

**这是本任务的关键安全点**：不能把「先写后导航」只交给 prompt 自觉。

## 切片 2：prompt 约束

文件：`resources/prompt/client/recommend_agent_prompt.md`

追加规则（中文，与现有风格一致）：
- 写入操作完成后，可以调用 `request_navigation` 附加一次页面跳转
- **预览阶段、等待用户确认时，不得调用** `request_navigation`
- 用户取消、否定或待确认动作已过期时，不得调用
- 多候选标题场景下，须等选中 → 预览 → 确认全部完成后才可调用

注意：prompt 是 Managed prompt（Redis 为准、本地文件兜底），改文件后需确认线上 Redis 里的
`client_recommend_agent_prompt` 同步更新。**这一条属于验收项**，只改文件会导致本地过、线上不生效。

search / discover 的 prompt 不加这段（它们没有写工具），其基础说明属 child 3。

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

- **门控正向**：state 里 pending 为 `ADD_TO_WISHLIST`、turn-bag 为 `pending_cleared=True` → 允许（锁 D1 核心修复）
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

## 不做

- 不重复注册工具（child 3 已完成）
- 不支持「导航后再写入」
- 不做跨轮导航队列
