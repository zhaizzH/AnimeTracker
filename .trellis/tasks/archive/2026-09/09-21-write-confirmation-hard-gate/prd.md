# 写入硬确认门禁与 nonce 绑定

## Goal

把三条写链路的"预览→明确确认→写入"从提示词/路由级约束升级为**代码级硬门禁**：非明确确认回合即使模型调用 execute 也一律拒写；并给待确认动作补 nonce/preview_id 绑定，防陈旧或错配动作被执行。

## Background

- 现状（已核）：`execute_add_to_wishlist`(`wishlist.py:84-99`)、`execute_weekly_collection_progress`(`collection_progress.py:49-56`)、`execute_set_collection_type`(`collection_type.py:121-133`) 只校验"存在对应类型的注入 pending 动作"就写；"明确确认"仅存在于提示词(`run.py:59` 等)与 gateway 路由启发式(`gateway.py:47-57,95`)。非确认回合也能经 LLM 路由到 recommend_agent 并由模型调用 execute。
- 实测复现：存在 SET_COLLECTION_TYPE 预览待确认动作时，重发"把X添加到追番"被模型当作确认并直接写入（硬边界"无 pending 不写"守住了，但"必须明确确认"没守住）。
- nonce 缺失：spec 持久化矩阵(`agent-guidelines.md:183`)要求绑定 `preview_id`/nonce，但只有 `CollectionProgressPendingAction` 有 `preview_id`(`pending_action.py:22`)；`WishlistPendingAction`(`:34-38`) 与 `SetCollectionTypePendingAction`(`:68-82`) 无 nonce。

## Requirements

1. **确认回合硬门禁**：gateway 在判定当前用户回合为明确确认时，向 AgentState 写入一个服务端标志（如 `write_confirmed: bool`，仅由 gateway 依据 `_is_explicit_confirmation` 等确定性规则设置，模型不可写）。所有 execute_* 工具在标志为假时**拒绝写入**并返回可读错误，无论模型是否调用。
2. **nonce/preview_id 绑定**：给 `WishlistPendingAction` 与 `SetCollectionTypePendingAction` 增加 nonce（服务端生成、随 pending 持久化、注入 execute）；execute 校验注入 nonce 与待确认动作一致，防陈旧/错配。保持旧 JSON 向后兼容（新字段带默认/可选，旧动作按既定损坏-清理策略处理）。
3. **共享守卫**：抽 `require_confirmed_write(...)`（或等价装饰器/助手），统一承载"确认回合标志 + pending 类型 + 用户绑定 + TTL + nonce"校验，三条写链路复用，避免各自实现漂移。
4. SUBJECT_RESOLUTION 选择语义不变：选择只产出预览（新的待确认动作），选择本身不是写入确认；写入仍需其后的明确确认回合。
5. 取消/过期/用户不匹配仍只清理本地状态，不写业务数据。

## Acceptance Criteria

- [ ] 存在待确认动作但当前回合非明确确认时，execute_* 一律拒写（返回错误），Business 未收到写请求；补该路径回归（含"重发加入请求"不触发写入）。
- [ ] 明确确认回合 + 匹配 nonce 时才写入；nonce 不匹配/缺失/陈旧动作被拒。
- [ ] wishlist/collection_type 的 pending 动作带 nonce 并序列化往返正常，旧类型 JSON 兼容；三条写链路都经同一共享守卫。
- [ ] 预览→确认→幂等写入边界不变；已收藏不覆盖；基础设施写入不确定时保留动作供重试。
- [ ] `uv run pytest` 全绿；09-16/09-20 既有回归（想看、设类型、进度更新）不回归。

## Out of Scope

- 不改 Business 写入接口或幂等语义。
- 不引入前端确认 UI 变更（门禁在 Agent 侧）。
- 不改 SUBJECT_RESOLUTION 的候选/选择协议（仅确保选择不等于写入确认）。

## Notes

- 复杂且跨切面（gateway→state→pending_action→三个 execute 工具）：`task.py start` 前必须补 `design.md`（确认标志如何由 gateway 确定性设置且模型不可篡改、nonce 生成与注入方式、共享守卫签名、旧动作兼容与清理）与 `implement.md`。
- 与 T4 协同：pending 持久化失败路径、gateway 路由测试可在 T4 补；本任务聚焦门禁与 nonce 的正/负路径测试。
- 安全基线参考 spec《待确认动作持久化失败矩阵》与《单标题设置收藏类型》两节。
