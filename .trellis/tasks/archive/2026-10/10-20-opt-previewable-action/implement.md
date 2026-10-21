# 实施计划：PreviewableAction 抽象

按顺序执行；每步给出验证命令；任一步失败回到上一步。

## 0. 准备

- [ ] 确认基线绿：`cd backend/agent && uv run pytest` → 期望 `668 passed, 0 xfailed`
- [ ] 确认 `pending_preview_id` 注入位置（已查：`app/agent/state.py:21` 是 `AgentState` 字段，`app/chat/service.py:64` 从 `pending_action.preview_id` 派生注入）。`execute_weekly_collection_progress` 的 `preview_id` 参数**保留签名不动**（父任务约束：不动 LangGraph 状态图拓扑）

## 1. 新增 `previewable.py`

- [ ] 新建 `backend/agent/app/agent/client/actions/previewable.py`，内容按 `design.md` §4：
  - `Clear` / `Keep` / `Replace` 三个 frozen dataclass
  - `ClearAction = Clear | Keep | Replace` 类型别名
  - `PreviewableAction(ABC, Generic[P])` 抽象基类
    - 类属性 `pending_type: ClassVar[str]`
    - 共享方法 `cancel()`
    - 模板方法 `execute(*, pending, user, write_confirmed)`
    - 抽象钩子 `do_execute(*, pending, user)` / `classify_result(*, result, pending)`
  - 模块 docstring 引用 `write_guard.py` 与 `pending_action.py` 的三层同步架构
- [ ] 验证：`cd backend/agent && uv run python -c "from app.agent.client.actions.previewable import PreviewableAction, Clear, Keep, Replace"`
- [ ] 验证：`uv run pytest` 仍 668 绿（还没人用它，不该有任何测试变化）

## 2. 迁移 `collection_type.py`（最简单，单条目 + 单 Business 调用）

- [ ] 在 `collection_type.py` 内新增 `SetCollectionTypePreviewable(PreviewableAction[SetCollectionTypePendingAction])`：
  - `pending_type = "SET_COLLECTION_TYPE"`
  - `__init__(self, business)` 存 `self._business`
  - `do_execute` = 当前 `execute_set_collection_type` 里的 `business.save_collection(...)` 一行
  - `classify_result` = 当前 `execute_set_collection_type` 里的「`code is None` → Keep / `code == 409` → Clear + ALREADY_COLLECTED / 其他 `code` → Clear + error / 成功 → Clear + SAVED」分支
- [ ] 改 `execute_set_collection_type` 函数体：删掉 `require_confirmed_write` 调用与所有 emit 调用，变成 `return action.execute(pending=pending, user=user, write_confirmed=write_confirmed)`
- [ ] 改 `cancel_set_collection_type` 函数体：`return action.cancel()`
- [ ] `set_subject_collection`（preview 工具）**完全不动**
- [ ] 在 `build_collection_type_tools(business, retrieval)` 顶部实例化 `action = SetCollectionTypePreviewable(business)`
- [ ] 验证：`uv run pytest tests/agent/test_collection_type.py` → 352 行测试全绿
- [ ] 验证：`uv run pytest` → 668 绿

## 3. 迁移 `wishlist.py`（多条目 + 聚合结果）

- [ ] 在 `wishlist.py` 内新增 `WishlistPreviewable(PreviewableAction[WishlistPendingAction])`：
  - `pending_type = "ADD_TO_WISHLIST"`
  - `__init__(self, business)`
  - `do_execute`：当前 `execute_add_to_wishlist` 里 for 循环 + `infra_error` 标志计算，返回 `(succeeded, skipped, failed, infra_error)` 四元组
  - `classify_result`：`infra_error=True` → `Keep()`，否则 `Clear()`；响应 dict 都是 `{"succeeded": ..., "skipped": ..., "failed": ...}`
- [ ] 改 `execute_add_to_wishlist` 为薄壳
- [ ] 改 `cancel_add_to_wishlist` 为 `return action.cancel()`
- [ ] `preview_add_to_wishlist` 和 `build_wishlist_preview` **完全不动**（后者被 `subject_resolution` 复用）
- [ ] 在 `build_wishlist_tools(business)` 顶部实例化 `action = WishlistPreviewable(business)`
- [ ] 验证：`uv run pytest tests/agent/test_wishlist.py` → 31 行测试全绿
- [ ] 验证：`uv run pytest` → 668 绿

## 4. 迁移 `collection_progress.py`（唯一有 REPLACE 的业务）

- [ ] 在 `collection_progress.py` 内新增 `CollectionProgressPreviewable(PreviewableAction[CollectionProgressPendingAction])`：
  - `pending_type = "COLLECTION_PROGRESS_UPDATE"`
  - `__init__(self, business)`
  - `do_execute`：用 `pending.preview_id` 作为路径参数调 `/progress-preview/{preview_id}/execute`（**不**用注入的 `preview_id` 参数，让 `pending` 作为唯一事实源）
  - `classify_result`：
    - 非 dict → `Keep()` + 原样返回
    - `error` + (`code == 404` 或 `code == 409` 且 message 含「重新生成」) → `Clear()` + 原 dict
    - `error` 其他 → `Keep()` + 原 dict
    - `state == "COMPLETED"` → `Clear()` + 原 dict
    - `state == "PREVIEW_CHANGED"` 且 `preview.previewId` 存在 → `Replace(_preview_data_to_pending_action(preview, user))` + 原 dict
    - 其他 → `Keep()` + 原 dict
  - 注意 `classify_result` 需要 `user` 来构造 `Replace` 的新 pending，但基类签名是 `classify_result(*, result, pending)`。**处理**：`do_execute` 把 `user` 一并放进返回值的内部结构（例如返回 `(business_result, user)`），或者把 `_preview_data_to_pending_action` 的构造延迟到 `classify_result` 内、由子类自己在 `__init__` 时拿不到 user 就在 `classify_result` 签名里加个 `user` 参数（**这是允许的设计：基类签名是 `classify_result(*, result, pending, user)`**，把 user 传给所有子类，wishlist/collection_type 忽略它）
  - **决定**：基类 `classify_result(*, result, pending, user)`，三个子类统一签名；wishlist/collection_type 忽略 `user`
- [ ] 改 `execute_weekly_collection_progress`：
  - 保留 `preview_id: Annotated[str, InjectedState("pending_preview_id")]` 签名（LangGraph 拓扑约束）
  - 函数体忽略 `preview_id`，改 `return action.execute(pending=pending, user=user, write_confirmed=write_confirmed)`
  - 在函数 docstring 末尾加一行说明：「`preview_id` 参数仅为保持 LangGraph state 注入契约；实际写入使用 `pending.preview_id`」
- [ ] 改 `cancel_weekly_collection_progress` 为 `return action.cancel()`
- [ ] `preview_weekly_collection_progress` **完全不动**
- [ ] 在 `build_collection_progress_tools(business)` 顶部实例化 `action = CollectionProgressPreviewable(business)`
- [ ] 验证：`uv run pytest tests/agent/test_collection_progress.py` → 281 行测试全绿
- [ ] 验证：`uv run pytest` → 668 绿

## 5. 全量验收

- [ ] `cd backend/agent && uv run pytest` → `668 passed, 0 xfailed`
- [ ] `grep -rn "emit_pending_action_clear" app/agent/client/actions/` → 命中数 **≤ 1**（仅 previewable.py 的 `cancel()`）
- [ ] `grep -rn "require_confirmed_write" app/agent/client/actions/` → 命中数 **≤ 2**（previewable.py 调用 + write_guard.py 定义）
- [ ] `grep -rn "emit_pending_action_replace" app/agent/client/actions/` → 命中数 **≤ 1**（仅 previewable.py 的 `execute()` 处理 `Replace`）
- [ ] `grep -rn "secrets.token_hex" app/agent/client/actions/` → 命中数不变（action_id 生成是 preview 侧职责，不在本次范围）

## 6. 提交策略

按业务顺序提交，每步一个 commit + merge：

1. `refactor(agent): add PreviewableAction 骨架 + Clear/Keep/Replace 三态`
2. `refactor(agent): collection_type 迁移到 PreviewableAction`
3. `refactor(agent): wishlist 迁移到 PreviewableAction`
4. `refactor(agent): collection_progress 迁移到 PreviewableAction + Replace 三态落地`

每个 commit 前跑 `uv run pytest` 确认绿。

## 7. 回滚点

- 步骤 1 是纯新增，无回滚成本
- 步骤 2/3/4 各自独立，单步出问题 `git checkout -- <file>` 即回滚
- 三态设计本身如果评审翻车，回滚到「只合并 cancel」版本只需删 `execute()` 模板方法和 `classify_result` 钩子，留 `cancel()` + `pending_type`

## 8. 不做的事

- 不改任何测试
- 不改 `pending_action.py` / `pending_events.py` / `write_guard.py` / `streaming.py` / `recommend.py`
- 不把 `build_wishlist_preview` 包进抽象
- 不动 LangGraph 状态图、SSE 协议、Redis 键格式
- 不引入 `ruff`（不在 pyproject.toml，PRD 不列验收）
