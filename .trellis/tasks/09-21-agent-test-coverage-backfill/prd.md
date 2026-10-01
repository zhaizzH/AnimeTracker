# Agent 测试盲区补齐

## Goal

为剩余 3 处测试盲区补自动化测试：`collection_progress` 工具、SSE wire 序列化、`_resolve_routing_result` 路由解析。使这三处不再能静默回归。

## 重设计说明（2026-09-29 复核）

原 PRD 列 6 类盲区。复核代码后发现 3 类**已由其它任务落地**，本任务范围收窄：

| 原盲区 | 现状 | 证据 |
|---|---|---|
| health 端点 | ✅ 已覆盖 | `tests/api/test_health.py`（agent-health-depth 交付） |
| Evidence 重复 ID | ✅ 已覆盖 | `tests/rag/test_evidence_contract.py:302`（rag-correctness 交付） |
| streaming pending 持久化失败 | ✅ 已覆盖 | `tests/agent/test_streaming.py:38`（断言 status error + 安全 end + 不宣称已持久化） |
| collection_progress | ❌ 仍缺 | `tests/` 零引用 |
| SSE 序列化 | ❌ 仍缺 | `tests/` 零引用 `app.api.sse` / `app.api.schemas.sse` |
| `_resolve_routing_result` | ❌ 仍缺 | `tests/` 零引用；既有 gateway 测试均以 `llm_factory=None` 绕过 |

## Background（已核实的剩余盲区）

- `app/agent/client/actions/collection_progress.py`（90 行）**零测试**，三处未覆盖分支：
  - `preview_weekly_collection_progress`：`user is None` 早退（`:24-26`）；`previewId` 存在时 `emit_pending_action_set`（`:36-37`）。
  - `execute_weekly_collection_progress`：写入门禁拒绝路径（`require_confirmed_write`）；404 与「409 + 重新生成」→ `emit_pending_action_clear`（`:58-62`）；`COMPLETED` → clear；`PREVIEW_CHANGED` → `emit_pending_action_replace`（`:66-69`）；`PREVIEW_CHANGED` 但无 `previewId` → 不动（隐含分支）。
  - `cancel_weekly_collection_progress`：`emit_pending_action_clear`。
- `app/api/sse.py`（37 行）+ `app/api/schemas/sse.py`（37 行）**零测试**：
  - `serialize_agent_event` 各 `AgentEventType` → `MessageType` 映射；END 事件走 `is_end=True` 且 content 为空的特化分支。
  - `serialize_sse` 的 `exclude_none=True`（`None` 字段不得出现在 wire 上）与 `data: ...\n\n` 分帧。
  - `create_sse_response` 的 `media_type` 与 `Cache-Control`/`Connection`/`X-Accel-Buffering` 头。
- `app/agent/client/gateway.py::_resolve_routing_result`（`:114-132`）**零测试**。既有 gateway 测试（`test_write_guard.py`、`test_capability_route.py`）覆盖的是 `build_gateway_router` 的**确定性分支**（`write_confirmed`、`_resolve_forced_pending_route`、`_is_explicit_confirmation`），本函数及其 LLM 调用路径从未被执行。
  - 7 条判定（`design.md` 记录实现形状）：非 mapping / messages 空 / 末条 content 空 / JSON 非法 / `route_target` 缺失 / `route_target` 非法（不在 `("search_agent","discover_agent","recommend_agent")`）/ 合法 → `{"route_target": target}`。
  - `extract_text` 支持 content 块列表（模型返回多块时的路径）。

## Requirements

1. `collection_progress`：补上列「Background」逐条分支的测试。`BusinessGateway` 用替身（记录 `request` 调用）；pending 事件发射断言经既有 stub 机制（参考 `tests/agent/test_streaming.py`、`tests/agent/test_write_guard.py` 的 stub 方式）。
2. SSE 序列化：`serialize_agent_event` 覆盖 answer/thinking/function_call/status 四类 + END；`serialize_sse` 覆盖 `exclude_none` 与分帧；`create_sse_response` 覆盖 media_type 与三个头，并断言 body 可被 `async for` 逐帧消费。
3. `_resolve_routing_result`：参数化覆盖上列 7 条判定；合法用例断言返回 `{"route_target": ...}`，非法用例断言 `ValueError` 且消息可辨识（`pytest.raises(..., match=...)`）。
4. 纯补测，**不改生产代码**。若补测暴露真实缺陷，记录并转新任务。

## Acceptance Criteria

- [x] `tests/agent/test_collection_progress.py` 覆盖 Background 列出全部分支，绿。（24 passed, 2 xfailed）
- [x] `tests/api/test_sse_serialization.py` 覆盖四类事件 + END + `exclude_none` + 分帧 + 响应头，绿。（16 passed）
- [x] `tests/agent/test_gateway_routing_result.py` 覆盖 7 条判定，绿。（29 passed, 4 xfailed）
- [x] `uv run pytest` 全绿（基线 **516 passed**），实际数字记录在完成说明。（**585 passed, 6 xfailed**）
- [x] 断言覆盖到分支而非仅行：每类至少有「正常」与「异常/边界」各一例。
- [x] `git diff` 仅新增测试文件，`app/` 零改动。

## 补测暴露的真实缺陷（转新任务，本任务内不改生产代码）

按 R4/Out of Scope，以下两处**未**在实现中修复，仅以 `xfail(strict=True)` 钉住：

1. **`_resolve_routing_result` 对标量/数组 JSON 抛 `AttributeError`**（`app/agent/client/gateway.py:129`）
   - 触发：模型返回 `"x"`、`123`、`true`、`["a"]` 等非对象 JSON。
   - 现状：`(data or {}).get(...)` 直接调用；`data` 为 str/int/bool/list 时抛 `AttributeError`。
   - 影响：`AttributeError` 非 `ValueError` 子类；调用方 `:157` 无本地捕获，异常穿透到图执行层，与其它 4 条判定（均 `ValueError`）语义不一致。
   - 测试：`tests/agent/test_gateway_routing_result.py::test_scalar_or_array_json_should_raise_value_error`（4 例 xfail）。

2. **`collection_progress` 缺 `isinstance` 守卫，None 响应崩溃**（`app/agent/client/actions/collection_progress.py:44,65`）
   - 触发：Business 成功但 `data` 为 null → `business_http.py:68` 显式 `return None`。
   - 现状：裸调 `data.get(...)` → `AttributeError`。
   - 影响：**同目录其它 5 个模块均用 `isinstance(data, dict) and data.get(...)` 守卫**（`collection_state.py:24`、`collection_type.py:141`、`subject_resolution.py:157,266,442,548,559`、`wishlist.py:107`、`collections.py:76`），仅 `collection_progress.py` 遗漏。
   - 测试：`test_preview_none_response_should_not_emit_and_not_crash`、`test_execute_none_response_should_not_crash`（2 例 xfail）。

## Out of Scope

- 不追求覆盖率数字；只补上述三处已确认盲区。
- 不重复补测 health / Evidence 重复 ID / streaming 持久化失败（已覆盖）。
- 不覆盖 `build_gateway_router` 确定性分支（已覆盖）。
- 不修改 `app/` 生产逻辑。

## Notes

- 轻量-中等任务：PRD-only 可直接 `task.py start`。
- 原 PRD 的 Background/Requirements 6 类已按上表收窄；`implement.jsonl`/`check.jsonl` 需相应重载 spec 上下文。
