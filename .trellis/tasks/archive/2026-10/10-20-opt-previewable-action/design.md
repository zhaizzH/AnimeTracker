# 设计：PreviewableAction 抽象

## 1. 问题陈述

三条写链路（wishlist / collection_type / collection_progress）当前各自实现「预览 → 确认 → 取消」三件套，产生三处逐字相同的 `cancel_*` 函数和三份「`require_confirmed_write` → 调 Business → 按状态 emit_clear/replace」骨架。差异点只在「调哪个 Business 接口、怎么把结果映射到清理动作」。

## 2. 设计目标

- 骨架只写一次，在 `PreviewableAction` 基类
- 差异点通过抽象方法 / 钩子表达，子类只填差异
- 不动工具函数签名、不动提示词、不动测试

## 3. 抽象边界

### 放进抽象（基类负责）

| 职责 | 说明 |
|---|---|
| `cancel()` 实现 | `emit_pending_action_clear()` + 返回 `{"cancelled": True}` |
| `execute()` 骨架 | gate → do_execute → classify_result → 按三态 emit → 返回 dict |
| `require_confirmed_write` 调用 | 从工具函数体上移到骨架 |
| 三态结果类型 | `Clear` / `Keep` / `Replace(new_pending)` 的语义定义 |

### 留在子类（业务负责）

| 职责 | 说明 |
|---|---|
| `pending_type` | 类属性，声明对应的 PendingAction.type 字面量 |
| `do_execute(pending, user)` | 调 Business 接口，返回原始 dict |
| `classify_result(result, pending)` | 把 Business 响应映射到三态 + 业务响应 dict |
| 整个 preview 流程 | 签名/返回值/NOOP 逻辑差异太大，强行抽象得不偿失 |

### 完全不动

- `pending_action.py`（PendingAction 类型已完整）
- `pending_events.py`（emit 三接口已是良好抽象）
- `write_guard.py`（`require_confirmed_write` 是被复用的守卫）
- `streaming.py`（SSE 协议禁区）
- 工具函数 `@tool` 签名、`tool_call_status`、docstring

## 4. 核心类型

```python
# backend/agent/app/agent/client/actions/previewable.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Generic, TypeVar

from app.agent.client.actions.write_guard import require_confirmed_write
from app.chat.pending_events import (
    emit_pending_action_clear,
    emit_pending_action_replace,
)
from app.chat.user import UserInfo


# ---- 三态：execute 结果对应的 PendingAction 清理动作 ----

@dataclass(frozen=True)
class Clear:
    """写入已确定（成功或确定性失败），清理待确认动作。"""


@dataclass(frozen=True)
class Keep:
    """基础设施错误等写入结果不确定，保留待确认动作供重试。"""


@dataclass(frozen=True)
class Replace:
    """预览已变化（如 Business 端数据更新），用新动作替换旧的。"""
    new_pending: Any  # 实际是 PendingAction 判别联合的某个成员


ClearAction = Clear | Keep | Replace


# ---- 抽象基类 ----

P = TypeVar("P")  # 子类声明的 PendingAction 具体类型


class PreviewableAction(ABC, Generic[P]):
    """「预览 → 确认 → 取消」三件套骨架。

    子类只需声明 pending_type 并实现 do_execute / classify_result；
    cancel 与 execute 的 gate/emit 时序由基类统一保证。
    """

    pending_type: ClassVar[str]

    # ---- 共享实现 ----

    def cancel(self) -> dict:
        """取消当前待确认动作，只清理本地状态，不修改后端数据。"""
        emit_pending_action_clear()
        return {"cancelled": True}

    # ---- 模板方法 ----

    def execute(
        self,
        *,
        pending: P | None,
        user: UserInfo | None,
        write_confirmed: bool,
    ) -> dict:
        gate = require_confirmed_write(
            user=user,
            pending=pending,
            expected_type=self.pending_type,
            write_confirmed=write_confirmed,
        )
        if gate is not None:
            return gate
        # 通过 gate 后 pending/user 必然非 None 且类型匹配
        result = self.do_execute(pending=pending, user=user)
        action, response = self.classify_result(result=result, pending=pending)
        if isinstance(action, Clear):
            emit_pending_action_clear()
        elif isinstance(action, Replace):
            emit_pending_action_replace(action.new_pending)
        # Keep: 不 emit 任何东西
        return response

    # ---- 子类钩子 ----

    @abstractmethod
    def do_execute(self, *, pending: P, user: UserInfo) -> Any:
        """调 Business 写入接口，返回原始结果。"""

    @abstractmethod
    def classify_result(self, *, result: Any, pending: P) -> tuple[ClearAction, dict]:
        """把 Business 结果映射到「PendingAction 清理动作 + 返回给模型的 dict」。"""
```

## 5. 三个子类

### 5.1 WishlistPreviewable

```python
class WishlistPreviewable(PreviewableAction[WishlistPendingAction]):
    pending_type = "ADD_TO_WISHLIST"

    def __init__(self, business: BusinessGateway):
        self._business = business

    def do_execute(self, *, pending, user):
        # 循环调 /wishlist，收集 succeeded/skipped/failed + infra_error 标志
        ...

    def classify_result(self, *, result, pending):
        # result 是 (succeeded, skipped, failed, infra_error) 四元组
        # infra_error=True → (Keep(), response)
        # 否则 → (Clear(), response)
        ...
```

注意：wishlist 的「do_execute」返回的不是 Business 原始 dict，而是聚合后的四元组。这是合理的——`do_execute` 的契约是「业务自己决定的中间表示」，`classify_result` 配对自己解释。

### 5.2 SetCollectionTypePreviewable

```python
class SetCollectionTypePreviewable(PreviewableAction[SetCollectionTypePendingAction]):
    pending_type = "SET_COLLECTION_TYPE"

    def do_execute(self, *, pending, user):
        return self._business.save_collection(
            pending.subject_id, collection_type=pending.target_type, token=user.token
        )

    def classify_result(self, *, result, pending):
        # error + code is None → Keep + {"error": True, "retryable": True, ...}
        # error + code == 409 → Clear + {"state": "ALREADY_COLLECTED", ...}
        # error + 其他 code → Clear + {"error": True, ...}
        # 成功 → Clear + {"state": "SAVED", ...}
```

### 5.3 CollectionProgressPreviewable

```python
class CollectionProgressPreviewable(PreviewableAction[CollectionProgressPendingAction]):
    pending_type = "COLLECTION_PROGRESS_UPDATE"

    def do_execute(self, *, pending, user):
        # preview_id 从 pending 来，不再从 InjectedState("pending_preview_id") 单独注入
        return self._business.request(
            "POST",
            f"/api/client/collections/progress-preview/{pending.preview_id}/execute",
            token=user.token,
        )

    def classify_result(self, *, result, pending):
        # 非 dict → Keep + result
        # error + (404 or 409+"重新生成") → Clear + result
        # error + 其他 → Keep + result
        # state == COMPLETED → Clear + result
        # state == PREVIEW_CHANGED → Replace(new_pending_from(result["preview"])) + result
        # 其他 → Keep + result
```

注意：collection_progress 的 `execute_weekly_collection_progress` 工具函数当前还接收一个 `preview_id: Annotated[str, InjectedState("pending_preview_id")]` 参数。需要查 `pending_preview_id` 是不是真的从 LangGraph state 注入；如果是从 `pending_action.preview_id` 派生的，那么工具签名不变、但内部不再用 `preview_id` 参数（或保留参数但不再使用，需要谨慎——见 §7 风险）。

## 6. 工具函数形状

工具函数变成薄壳，签名/装饰器/docstring 完全不动：

```python
def build_wishlist_tools(business: BusinessGateway):
    action = WishlistPreviewable(business)

    @tool
    @tool_call_status(display_name="预览加入想看")
    def preview_add_to_wishlist(...) -> dict:
        # preview 不进抽象，保持现状
        ...

    @tool
    @tool_call_status(display_name="确认加入想看")
    def execute_add_to_wishlist(
            pending: Annotated[WishlistPendingAction | None, InjectedState("pending_action")],
            user: Annotated[UserInfo | None, InjectedState("user")] = None,
            write_confirmed: Annotated[bool, InjectedState("write_confirmed")] = False) -> dict:
        """docstring 保持原样"""
        return action.execute(pending=pending, user=user, write_confirmed=write_confirmed)

    @tool
    @tool_call_status(display_name="取消加入想看")
    def cancel_add_to_wishlist() -> dict:
        """docstring 保持原样"""
        return action.cancel()

    return [preview_add_to_wishlist, execute_add_to_wishlist, cancel_add_to_wishlist]
```

## 7. 风险与权衡

### R-1: `pending_preview_id` 注入参数

`execute_weekly_collection_progress` 当前签名为：

```python
def execute_weekly_collection_progress(
        preview_id: Annotated[str, InjectedState("pending_preview_id")],
        ...
```

需要查清 `pending_preview_id` 是从哪儿注入的：

- 如果是从 `AgentState.pending_action.preview_id` 派生的 LangGraph 注入键，那工具签名保留这个参数但内部不用它（为了不改 LangGraph 拓扑，按父任务约束），把 `pending.preview_id` 作为唯一事实源
- 如果是独立 state 键，按父任务「不动 LangGraph 状态图拓扑」约束，**保留签名+保留使用**，do_execute 接收 `preview_id` 作为参数（破坏「do_execute 只看 pending」的纯度，但符合约束）

**倾向**：保留签名，函数体忽略 `preview_id`，用 `pending.preview_id` 作为事实源。在 PRD/design 里写明这一点。

### R-2: 测试不动 vs 行为微变

`execute_weekly_collection_progress` 当前的逻辑里，`preview_id` 参数虽然被注入了但函数体**没用到它**（只调了 `business.request(f".../{preview_id}/execute")`——这里用的是参数 `preview_id` 而不是 `pending.preview_id`）。如果改成用 `pending.preview_id`，在测试 mock `InjectedState` 的场景下行为是否一致需要看测试如何构造 `pending_action` 和 `pending_preview_id`。

**应对**：实施时先跑 `pytest tests/agent/test_collection_progress.py` 拿基线，改完再跑，如果挂了就看是测试假设不一致还是真改坏了。

### R-3: 抽象返回值类型 `Any`

`do_execute` 返回 `Any`（wishlist 返回四元组、其他两个返回 Business dict）损失类型安全。可以考虑给每个子类定 `ExecuteResult` 类型别名，但基类不需要知道。

**决定**：基类用 `Any`，子类在自己的 `do_execute`/`classify_result` 签名里写具体类型。类型安全在子类层保证，基类保持通用。

### R-4: `build_wishlist_preview` 是被 `subject_resolution` 复用的纯函数

不包进抽象，保持现状。这意味着 wishlist 的「preview 逻辑」仍然是模块级函数 + 工具薄壳，不变成 `WishlistPreviewable.preview()` 方法。这是有意的——preview 差异太大，下沉会让抽象漏出三个业务的签名差异。

## 8. 影响面

### 修改

- `backend/agent/app/agent/client/actions/wishlist.py`
- `backend/agent/app/agent/client/actions/collection_type.py`
- `backend/agent/app/agent/client/actions/collection_progress.py`

### 新增

- `backend/agent/app/agent/client/actions/previewable.py`

### 不动

- 所有测试文件
- `pending_action.py` / `pending_events.py` / `write_guard.py` / `streaming.py` / `recommend.py`
- `subject_resolution.py` 及其兄弟模块

## 9. 验收命令

```bash
cd backend/agent
uv run pytest                                                        # 668 passed, 0 xfailed
grep -rn "emit_pending_action_clear" app/agent/client/actions/       # ≤1 命中（previewable.py）
grep -rn "require_confirmed_write" app/agent/client/actions/         # ≤2 命中（previewable.py + write_guard.py）
```
