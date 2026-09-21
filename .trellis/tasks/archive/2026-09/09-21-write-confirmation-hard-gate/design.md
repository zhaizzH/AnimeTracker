# 技术设计：写入硬确认门禁与动作版本绑定

## 1. 边界与目标

只在 Agent 侧把三条写链路（wishlist / collection_progress / collection_type）的"明确确认"从提示词级升级为**代码级硬门禁**，并给待确认动作补一个服务端版本号用于陈旧/替换失效与 trace 关联。不改 Business 接口、不改前端、不改 SUBJECT_RESOLUTION 的候选/选择协议。

核心不变量：**没有"当前回合为明确确认"这一服务端标志，任何 execute_* 都不得写入**，无论模型是否调用。

## 2. 机制：确认回合硬门禁

### 2.1 确认标志由 gateway 确定性设置

- `AgentState` 新增 `write_confirmed: bool`（默认 False，`total=False` TypedDict）。
- `gateway_router` 在返回前统一计算 `confirmed = _is_explicit_confirmation(state.current_question)`，并把 `write_confirmed: confirmed` 并入所有返回分支（强制 pending 路由、显式写入意图路由、LLM 路由）。该值只由服务端依据确定性规则得出，**模型无法写入或篡改**（它不是工具参数、不由域节点设置）。
- 每回合状态由 `service.build_initial_state` 重建、gateway 每回合重算，因此 `write_confirmed` 天然只反映"当前这条用户消息"，不会跨回合残留。
- ADMIN 不经 gateway，但 admin 节点无收藏写工具，不受影响。

### 2.2 共享守卫

- 新增 `app/agent/client/actions/write_guard.py::require_confirmed_write(*, user, pending, expected_type, write_confirmed) -> dict | None`：统一校验 用户存在 → 待确认动作存在且类型匹配 → 用户绑定（`pending.user_id == user.user_id`）→ 未过期（`expires_at`）→ `write_confirmed is True`。任一不满足返回可读错误 dict（不写入）。
- 三个 execute 工具改为先调用该守卫，通过后才写；wishlist/collection_type 顺带获得此前缺失的用户绑定与过期校验（progress 侧已有 preview_id，纳入同一守卫）。

### 2.3 选择 ≠ 写入确认

- `select_resolved_subject` 不受 `write_confirmed` 门禁（它只产出预览/新的待确认动作，不写业务数据）。SUBJECT_RESOLUTION 回合即便用户说"确认"，因不存在写入类 pending 动作，execute_* 的类型校验也会拒绝。

## 3. 动作版本绑定（对"nonce"的工程性收敛）

原 Q8 提到 "nonce/preview_id 绑定"。设计阶段结论：本架构下 execute_* **只读服务端注入的 pending 动作、模型不提供任何写入参数**，因此"模型回传 nonce 再比对"既无对象（nonce 与动作同源、自比对恒真）又会重新引入模型可篡改数据，违背既有安全原则。

据此收敛为：

- 给 `WishlistPendingAction` 与 `SetCollectionTypePendingAction` 增加服务端生成的 `action_id`（每次 SET/REPLACE 重新生成的短随机串），用途限于：
  1. **持久化层的版本失效/替换检测**：REPLACE 覆盖同一 Redis 键时以新 `action_id` 失效旧版本；保存失败沿用 `streaming.py` 既有 status 错误事件，客户端不得据此宣称已持久化（对齐 spec《待确认动作持久化失败矩阵》"使其版本失效"）。
  2. **trace 关联/日志**：把预览与执行用同一 `action_id` 串起来（不落敏感信息）。
- `action_id` **不作为模型回传令牌**、不参与"模型是否可写"的判定；写入门禁由 §2 的 `write_confirmed` + 类型/用户/TTL 绑定承担。
- collection_progress 继续用 Business 的 `preview_id`（已是服务端权威版本标识），并同样纳入 `require_confirmed_write` 的确认门禁。

> 这是对 Q8"(iii) 两者都做"的细化：确认回合门禁为主、版本绑定为辅且服务端持有。若你更希望"模型必须回传 nonce 才能执行"，需要改变"模型不提供写入参数"的现有安全前提，请在批准前指出。

## 4. 失败与错误矩阵

| 条件 | 必须行为 |
|---|---|
| 当前回合非明确确认（`write_confirmed=False`），模型调用 execute_* | 拒绝写入，返回可读错误（"需要用户明确确认后才执行"），Business 不收到请求 |
| 明确确认 + 类型/用户/TTL/action 均匹配 | 正常写入（保持各自幂等/覆盖语义） |
| pending 动作缺失或类型不符 | 拒绝（沿用现有语义） |
| 用户不匹配 / 过期 | 拒绝并清理本地待确认状态 |
| 保存/替换待确认动作失败 | 沿用 streaming 既有 status 错误事件，不宣称已持久化；`action_id` 版本失效避免误执行旧动作 |
| SUBJECT_RESOLUTION 回合说"确认" | 路由到 recommend_agent，但无写入 pending 动作 → execute_* 类型校验拒绝；选择仍只产出预览 |

## 5. 受影响文件

- `app/agent/state.py`（+`write_confirmed`）
- `app/agent/client/gateway.py`（各返回分支并入 `write_confirmed`）
- `app/agent/client/actions/write_guard.py`（新增共享守卫）
- `app/agent/client/actions/wishlist.py`、`collection_progress.py`、`collection_type.py`（execute_* 接守卫）
- `app/chat/pending_action.py`（Wishlist/SetCollectionType +`action_id`；旧 JSON 兼容）
- 生成/清理 `action_id` 处：`wishlist.py::_pending_action_from_items`、`collection_type.py::build_collection_type_preview`
- `tests/agent/*`（execute 相关用例补 `write_confirmed=True`；新增门禁正/负路径、版本失效、gateway 标志设置用例）

## 6. 兼容性

- `action_id`、`write_confirmed` 均带默认/可选，旧 pending JSON 缺字段按默认解析；未知/损坏动作沿用既有安全清理。
- 现有 execute_* 直接调用（测试）需显式传 `write_confirmed=True`；这是本任务的预期行为变更，回归据此更新，不放宽门禁来"修复"失败。

## 7. 可观测性

- `agent.request.completed` 已有；新增/复用 `action_id` 作为预览↔执行的关联键，不记录用户标题、类型明细、token 或完整回答。
