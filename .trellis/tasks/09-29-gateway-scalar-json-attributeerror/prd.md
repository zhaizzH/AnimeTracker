# Gateway 路由解析标量 JSON 抛 AttributeError

> 由 `09-21-agent-test-coverage-backfill` 补测暴露。该任务按「纯补测、不改生产代码」约束未修复。

## Goal

`_resolve_routing_result` 对 JSON 合法但非对象的 payload 抛出 `ValueError`（与其余 4 条判定一致），而非 `AttributeError`。

## Background（已核实）

`app/agent/client/gateway.py:129`：

```python
target = str((data or {}).get("route_target") or "").strip()
```

`data = json.loads(content.strip())`（`:126`）——JSON 合法时 `data` 可为 str/int/bool/list：

| 输入 content | 现状 | 期望 |
|---|---|---|
| `"x"` | `AttributeError: 'str' object has no attribute 'get'` | `ValueError: unsupported route_target: ` |
| `123` | `AttributeError: 'int' ...` | 同上 |
| `true` | `AttributeError: 'bool' ...` | 同上 |
| `["a"]` | `AttributeError: 'list' ...` | 同上 |
| `null` | `ValueError` ✅ | （已正确） |

**影响**：`AttributeError` 不是 `ValueError` 子类。`_resolve_routing_result` 的调用点 `gateway.py:157`（`return {"routing": _resolve_routing_result(result.payload), ...}`）无本地捕获，异常穿透到图执行层。其余 4 条判定（非 mapping / messages 空 / content 空 / JSON 非法）均抛 `ValueError`，本路径语义不一致。

**触发条件**：模型返回合法 JSON 标量/数组而非对象。属模型输出异常，非构造臆想。

## Requirements

1. `_resolve_routing_result` 对 `data` 非 mapping 时抛 `ValueError`，消息保持 `unsupported route_target: {target}` 或新增更明确的措辞（须同步更新测试 `match=`）。
2. 保持其余判定与返回语义不变。
3. `tests/agent/test_gateway_routing_result.py::test_scalar_or_array_json_should_raise_value_error` 的 `xfail(strict=True)` 标记移除后用例转绿（4 例参数化）。
4. 不改 `_ALLOWED_TARGETS` 与路由分派逻辑。

## Acceptance Criteria

- [ ] `_resolve_routing_result` 对 `"x"`/`123`/`true`/`["a"]` 抛 `ValueError`，不抛 `AttributeError`。
- [ ] `tests/agent/test_gateway_routing_result.py` 的 4 条 `xfail` 标记已移除且用例通过（strict 模式下会强制发现）。
- [ ] 其余 4 条判定与合法路径用例仍绿。
- [ ] `uv run pytest` 全绿，无 `xfail`/`XPASS` 与 gateway 相关。
- [ ] `git diff` 仅触及 `gateway.py:129` 一带与对应测试文件。

## Out of Scope

- 修改 `build_gateway_router` 的确定性分支（`write_confirmed`、`_resolve_forced_pending_route`、`_is_explicit_confirmation`）。
- 改变 `_ALLOWED_TARGETS` 内容或路由目标集合。
- 为路由失败新增重试/回退默认路由（当前设计是 fail-closed，见 spec `agent-guidelines.md` Gateway 路由结果解析节）。

## Notes

- 轻量任务：PRD-only 可直接 `task.py start`。
- spec 已登记：`.trellis/spec/backend/agent-guidelines.md` 的「Gateway 路由结果解析」节（含「已知缺陷」条）。
- 修复后须同步移除该 spec 条目的「已知缺陷」措辞。
