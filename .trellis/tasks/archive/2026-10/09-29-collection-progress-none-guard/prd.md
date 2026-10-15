# collection_progress 缺 isinstance 守卫致 None 响应崩溃

> 由 `09-21-agent-test-coverage-backfill` 补测暴露。该任务按「纯补测、不改生产代码」约束未修复。

## Goal

`collection_progress` 的两个工具对 `BusinessGateway.request` 可能返回的 `None` 做守卫，与同目录其余 5 个模块一致；不抛 `AttributeError`。

## Background（已核实）

`HttpBusinessGateway.request` 返回类型为 `dict | list | None`。`business_http.py:61-69`：

```python
if isinstance(body, dict):
    if "data" in body:
        return body["data"]
    if "code" in body and "message" in body:
        return None      # 成功但 data 为 null → 显式返回 None
return body
```

`app/agent/client/actions/collection_progress.py:44,65` 裸调：

```python
if not data.get("error") and data.get("previewId"):      # :44  preview
...
if data.get("error"):                                     # :65  execute
```

`data is None` → `AttributeError: 'NoneType' object has no attribute 'get'`。

**同目录其它模块均有守卫**（模式不统一是本缺陷的成因）：

| 文件 | 守卫写法 | 行 |
|---|---|---|
| `collection_state.py` | `isinstance(data, dict) and data.get("error")` | :24 |
| `collection_type.py` | `isinstance(result, dict) and result.get("error")` | :141 |
| `subject_resolution.py` | `isinstance(response/preview, dict) and ....get("error")` | :157, :266, :442, :548, :559 |
| `wishlist.py` | `isinstance(result, dict) and result.get("error")` | :107 |
| `collections.py` | `isinstance(data, dict) and data.get("error")` | :76 |
| **`collection_progress.py`** | **无** | :44, :65 |

**影响**：Java 端点成功但 `data` 为 null 时，预览与执行工具均崩溃。异常穿透工具调用层，用户看到未捕获错误而非可读失败。

## Requirements

1. `collection_progress.py` 的 `:44`、`:65` 两处补 `isinstance(data, dict)` 守卫，采用与同目录一致的写法。
2. `data is None` 时的行为须明确：预览 → 不发射待确认动作、返回原值；执行 → 不清理动作、返回原值。**不得虚构成功或失败语义**，须在 `design.md` 记录选择理由。
3. `tests/agent/test_collection_progress.py` 的 2 条 `xfail(strict=True)` 标记移除后转绿。
4. 不改变正常路径（dict 响应）的任何行为。

## Acceptance Criteria

- [ ] `data is None` 时预览与执行工具均不抛异常。
- [ ] `test_preview_none_response_should_not_emit_and_not_crash`、`test_execute_none_response_should_not_crash` 的 `xfail` 标记已移除且通过。
- [ ] 既有 24 条 collection_progress 用例仍绿（正常路径零回归）。
- [ ] `uv run pytest` 全绿。
- [ ] `git diff` 仅触及 `collection_progress.py` 与对应测试文件。

## Out of Scope

- 修改 `HttpBusinessGateway.request` 的返回语义（`None` 是其既有契约，其它模块已适配）。
- 修改其它 5 个模块的守卫写法（已正确）。
- 为 `None` 响应新增错误码或用户可见提示（除非 `<design.md>` 论证必要）。

## Notes

- 轻量任务：PRD-only 可直接 `task.py start`；若 §2 的「`None` 行为选择」需要论证，补 `design.md`。
- spec 已登记：`.trellis/spec/backend/agent-guidelines.md` 的「Business 响应守卫」节（含「已知缺陷」条）。
- 修复后须同步移除该 spec 条目的「已知缺陷」措辞。
