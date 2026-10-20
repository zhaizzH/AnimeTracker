# 优化项 3: PreviewableAction 抽象 + 三业务对齐矩阵

## Goal

把 `wishlist` / `collection_type` / `collection_progress` 三条写链路的「预览 → 确认 → 取消」骨架下沉到一个 `PreviewableAction` 抽象，消除三件套复制粘贴。完成信号：

- 三个 `cancel_*` 函数（当前逐字相同，共 3 处）合并到 1 处实现
- 新增写业务（评分/列表/删除）从「改 3 个文件复制三件套」降到「声明 1 个 `PreviewableAction` 子类 + 在 `recommend.py` 注册工具」
- 668 个测试全绿，且**不修改任何测试**（除非测试本身在测三件套复制粘贴）

## Context

父任务约束（不可违反）：

- 不动 LangGraph 状态图拓扑
- 不动 SSE 帧协议
- 不动 Redis 键格式与 TTL
- 不动 business 侧 Java 代码
- 不改现有测试（除非测试本身在测三件套复制粘贴）
- 重构必须测试全绿

三业务对齐矩阵（handoff.md 已盘点，本任务直接采用）：

| 维度 | `wishlist` | `collection_type` | `collection_progress` |
|---|---|---|---|
| 预览条目数 | 列表，上限 10（`_MAX_WISHLIST_PREVIEW_ITEMS`） | 单条 | 由 Business 返回决定 |
| PendingAction 类型 | `ADD_TO_WISHLIST` | `SET_COLLECTION_TYPE` | `COLLECTION_PROGRESS_UPDATE` |
| TTL 来源 | 本地 +10min | 本地 +600s | **Business 返回 `expiresAt`** |
| 跳过/NOOP 逻辑 | `check_collection_state` → 已收藏进 `skippedItems` | 已在目标类型 → `NOOP` 不发动作 | 无 |
| 预览返回值 | `{pendingItems, skippedItems}` | `{action: ADD/NOOP/CHANGE, ...}` | Business 原始 `data` |
| 执行状态机 | `ADDED` / `ALREADY_COLLECTED` / 其他 | `SAVED` / `ALREADY_COLLECTED`(409) / 404 | `COMPLETED` / `PREVIEW_CHANGED` |
| REPLACE 支持 | ❌ | ❌ | ✅ `PREVIEW_CHANGED` 时 REPLACE |
| 基础设施错误不清理 | `infra_error` 标志 | `code is None` | 非 dict / 未定 |
| action_id | `secrets.token_hex(8)` | `secrets.token_hex(8)` | 用 Business `preview_id` |

## Requirements

### 设计决策（已与用户对齐）

1. **抽象粒度 = 最小骨架**：只下沉 `cancel` + `execute` 的 gate/调用/清理骨架。`preview` 完全留给各业务，因为三个业务的 preview 签名/返回值/NOOP 语义差异过大，强行统一会让抽象比现状更难读。
2. **REPLACE 泛化为结果钩子**：execute 的「业务结果 → PendingAction 清理动作」用三态表达：`Clear` / `Keep` / `Replace(new_pending)`。wishlist 和 collection_type 只产出 `Clear`/`Keep`，只有 progress 会产出 `Replace`。
3. **新文件位置**：`backend/agent/app/agent/client/actions/previewable.py`，与 `write_guard.py` 同级。
4. **工具函数仍是 9 个**：LangChain `@tool` 装饰器 + `InjectedState` 签名决定每个工具必须是独立函数。收敛指「业务逻辑下沉到 3 个 `PreviewableAction` 子类 + 1 个共享 cancel」，工具函数本身变成 5-10 行薄壳。`recommend.py` 消费的工具列表不变。

### 功能要求

- FR-1: `PreviewableAction` 抽象基类提供 `cancel()` 共享实现（`emit_pending_action_clear()` + `{"cancelled": True}`）
- FR-2: `PreviewableAction` 提供 `execute()` 模板方法，骨架为：`require_confirmed_write` gate → 调用 `do_execute` 钩子 → 用 `classify_result` 钩子把业务结果映射到 Clear/Keep/Replace → 执行对应 emit → 返回业务响应 dict
- FR-3: 三个业务各声明一个子类，封装自己的 `do_execute` 和 `classify_result`
- FR-4: 三个 `cancel_*` 工具函数体合并为调用对应子类的共享 `cancel()`
- FR-5: `require_confirmed_write` 调用从三个 execute 工具函数体内移到 `PreviewableAction.execute()` 骨架里
- FR-6: 工具函数签名、`@tool` 装饰器、`tool_call_status` display_name、docstring 全部保持不变（提示词和测试依赖）

### 非功能要求

- NFR-1: 不修改 `pending_action.py`（PendingAction 类型已经完整，不需要改）
- NFR-2: 不修改 `pending_events.py` / `streaming.py`（emit 三接口已是良好抽象）
- NFR-3: 不修改 `write_guard.py`（`require_confirmed_write` 是被复用的守卫，不是要抽走的骨架）
- NFR-4: 不修改 `subject_resolution.py` / `candidate_matcher.py` / `title_normalizer.py` / `subject_authority.py`（上一任务产物，与本次无关）
- NFR-5: 不修改 `recommend.py`（工具列表形态不变）
- NFR-6: 不修改任何 `tests/agent/test_wishlist.py` / `test_collection_type.py` / `test_collection_progress.py`

## Acceptance Criteria

- [ ] AC-1: 新增 `backend/agent/app/agent/client/actions/previewable.py`，导出 `PreviewableAction` 抽象基类与 `Clear`/`Keep`/`Replace` 三态类型
- [ ] AC-2: `wishlist.py` / `collection_type.py` / `collection_progress.py` 各自定义一个 `PreviewableAction` 子类，封装各自的 `do_execute` 和 `classify_result`
- [ ] AC-3: 三个 `cancel_*` 函数体逐字相同 → 改为调用共享的 `cancel()` 实现，源代码中 `emit_pending_action_clear(); return {"cancelled": True}` 这两行**只出现在 `previewable.py` 一处**
- [ ] AC-4: 三个 `execute_*` 工具函数体内**不再直接调用** `require_confirmed_write`，由 `PreviewableAction.execute()` 骨架统一调用
- [ ] AC-5: `collection_progress` 的 `PREVIEW_CHANGED` + `emit_pending_action_replace` 通过 `Replace` 三态走通，不再在工具函数体内显式调用 `emit_pending_action_replace`
- [ ] AC-6: `uv run pytest` 在 `backend/agent/` 下跑出 **668 passed, 0 xfailed**（与 2026-10-19 基线一致）
- [ ] AC-7: `grep -rn "emit_pending_action_clear" backend/agent/app/agent/client/actions/{wishlist,collection_type,collection_progress,previewable}.py` 在 execute/cancel 骨架范围内命中数 ≤ 1（仅在 previewable.py）。注意 `collection_type.py` 的 `set_subject_collection`（preview 工具）和 `subject_resolution.py` 里的 `emit_pending_action_clear` 属于 preview 侧「清陈旧状态」职责，不在本范围
- [ ] AC-8: `grep -rn "require_confirmed_write" backend/agent/app/agent/client/actions/` 命中数 ≤ 2（previewable.py + write_guard.py 定义处）

## Out of Scope

- 强行统一 TTL 策略（progress 的 TTL 来自 Business，wishlist 是 10min，collection_type 是 600s，保持现状）
- 强行统一 preview 返回值结构（被提示词和测试依赖）
- 把 `build_wishlist_preview` 包进抽象（它被 `subject_resolution` 复用，是多入口共享的纯函数）
- 改工具名（`build_*_tools` 返回的列表被 `recommend.py` 消费）
- 动 LangGraph 状态图、SSE 协议、Redis 键格式、Java 代码

## Notes

- ruff 不在 `pyproject.toml` 依赖里，PRD 不列 ruff 验收项
- 测试基线：2026-10-19 起为 **668 passed / 0 xfailed**（老文档里的 585/6 已过时）
