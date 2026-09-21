# 实施计划：写入硬确认门禁与动作版本绑定

## 1. 实现顺序（TDD）

1. **确认标志贯通 state**
   - `AgentState` 加 `write_confirmed: bool`；`service.build_initial_state` 默认 False。
   - `gateway_router` 各返回分支并入 `write_confirmed=_is_explicit_confirmation(current_question)`。
   - 先补 gateway 测试：明确确认→True；普通/否定/查询→False；三分支（强制 pending、显式写入意图、LLM 路由）都带该字段。

2. **共享守卫**
   - 新增 `write_guard.py::require_confirmed_write(user, pending, expected_type, write_confirmed)`：用户→类型→用户绑定→TTL→确认标志，逐项返回可读错误。
   - 单测覆盖每条拒绝分支与放行分支。

3. **三个 execute 接守卫**
   - `execute_add_to_wishlist`、`execute_weekly_collection_progress`、`execute_set_collection_type` 改为先过守卫再写；execute 工具签名新增 `write_confirmed: Annotated[bool, InjectedState("write_confirmed")] = False`。
   - 更新既有 execute 测试显式传 `write_confirmed=True`；新增"非确认回合调用 execute → 拒写、Business 未收到请求"的负路径测试（含"重发加入请求"场景）。

4. **动作版本 action_id**
   - `WishlistPendingAction`/`SetCollectionTypePendingAction` 加 `action_id: str`（默认 ""，序列化 alias `actionId`）；在预览生成处填入服务端随机短串。
   - 序列化往返与旧 JSON（无 actionId）兼容测试；REPLACE 覆盖产生新 action_id 的测试。

5. **提示词与文档对齐**
   - run.py 待确认上下文补充"需用户明确确认"（已具备，复核措辞）；如行为契约变化，更新 `agent-guidelines.md` 安全写操作小节（硬门禁 + action_id 语义）。

6. **质量门禁**
   - 跑受影响测试 → `uv run pytest tests/agent` → 全量 `uv run pytest`。
   - 跨层核对：确认标志只由 gateway 设置、模型不可篡改；三条写链路同一守卫；未改 Business/前端。

## 2. 重点文件与回滚点

### 重点文件
- `app/agent/state.py`、`app/agent/client/gateway.py`
- `app/agent/client/actions/write_guard.py`（新增）
- `app/agent/client/actions/wishlist.py`、`collection_progress.py`、`collection_type.py`
- `app/chat/pending_action.py`
- `tests/agent/`（gateway 标志、守卫、三链路正/负路径、序列化兼容）

### 回滚点
- 步骤 1-2（state 标志 + 守卫）为纯增量，可独立回退。
- 步骤 3 接守卫前后各跑一次 09-16/09-20 写链路回归；若回归失败，先撤回 execute 的守卫接线，**不得放宽门禁或绕过确认来修复**。
- 步骤 4（action_id）与门禁解耦，可单独回退。

## 3. 验证命令

```powershell
Set-Location backend/agent
uv run pytest tests/agent -q
uv run pytest -q
```

## 4. 必测场景

- gateway：明确确认→`write_confirmed=True`；查询/否定/普通消息→False；三个返回分支都携带该字段；模型无法通过工具参数改写它。
- 守卫：缺用户/缺动作/类型不符/用户不匹配/过期/未确认 各自拒绝；全通过才放行。
- 三链路：非确认回合调用 execute_* → 拒写且 Business 零调用；确认回合 → 正常写（wishlist 幂等、progress preview_id、collection_type /save）。
- "重发加入请求"回归：存在待确认动作时重发加入语句（非确认词）→ 不写入。
- action_id：序列化往返、旧 JSON 无 actionId 兼容、REPLACE 生成新 action_id。
- 既有回归：想看、设类型 ADD/CHANGE/NOOP、进度更新、SSE/pending 持久化（若 T4 未先做则此处不重复）。

## 5. 启动前门禁

- `prd.md`、`design.md`、`implement.md` 完成并通过规划摘要审核。
- design §3 对"nonce→服务端 action_id"的收敛已获用户确认。
- 用户在规划摘要后明确批准实现。
- `task.py validate .trellis/tasks/09-21-write-confirmation-hard-gate` 通过。
- 过门禁后 `task.py start`，读 `trellis-before-dev` 再编码。
