# Agent 测试盲区补齐

## Goal

为已确认的测试盲区补自动化测试，使写入进度链路、SSE wire 契约、健康端点、pending 持久化失败、gateway LLM 路由与 Evidence 重复 ID 不再能静默回归。

## Background（已核实的盲区）

- `collection_progress.py` **零测试**：`PREVIEW_CHANGED`→`emit_pending_action_replace`(`:66-69`)、404/409 清理(`:58-62`)、COMPLETED 分类均未测。
- SSE 序列化 **零测试**：`app/api/sse.py` + `app/api/schemas/sse.py`（事件联合 answer/thinking/function_call/status/end、`is_end`、`exclude_none`）无用例。
- health 端点 **零测试**：`app/api/chat.py:99-107`（恒 200 + `llm_configured`）。
- streaming pending 持久化失败 **未测**：`tests/agent/test_streaming.py` 只覆盖 `on_answer_completed` 失败；`on_pending_action` 失败分支(`streaming.py:165-180`，"待确认动作保存失败，请重试")无用例——正是 spec 矩阵(`agent-guidelines.md:184-189`)点名的最低回归。
- gateway LLM 路由 **未测**：`_resolve_routing_result`(`gateway.py:114-132`，JSON 解析/空内容/非法 route_target→ValueError) 与 `build_gateway_router` 完整路径无用例（现仅测 `_resolve_forced_pending_route`/`_is_explicit_confirmation`）。
- Evidence 重复 ID **未测**：与 T2 相关，若 T2 未覆盖则在此补。

## Requirements

1. collection_progress：预览生成 pending、执行 COMPLETED 分类、`PREVIEW_CHANGED`→REPLACE、404/409→clear、基础设施错误保留动作。
2. SSE：各事件类型序列化字段（type/content/is_end/meta）、END 事件 `is_end=true`、`exclude_none` 行为、`text/event-stream` 分帧。
3. health：LLM 可解析/不可解析两种返回；恒 200；字段稳定。
4. streaming：`on_pending_action` 保存失败时发出 status 错误事件并仍安全发送 end；不宣称动作已持久化。
5. gateway：`_resolve_routing_result` 对合法/非法 payload 的行为；`gateway_router` 在明确写入意图/待确认动作/普通 LLM 路由三分支的确定性走向（LLM 用替身）。
6. Evidence 重复 ID：若 T2 未覆盖，补 fail-closed 用例。

## Acceptance Criteria

- [ ] 上述 6 类各有对应测试并纳入 `uv run pytest`，全绿。
- [ ] pending 持久化失败路径断言：发出 status 错误 + 安全 end + 不宣称已持久化（对齐 spec 最低回归）。
- [ ] gateway LLM 路由测试用替身模型，不依赖真实 LLM；覆盖非法 route_target 抛错。
- [ ] 不改变被测生产代码行为（纯补测）；若补测暴露真实缺陷，记录并转对应任务，不在本任务内顺手改逻辑。

## Out of Scope

- 不追求 100% 覆盖；只补上述已确认盲区。
- 不在本任务修改生产逻辑（缺陷转 T2/T3 或新任务）。

## Notes

- 轻量-中等任务：可 PRD-only 直接 `task.py start`；若补测过程发现需要改生产代码，另记并转相应任务。
- 与 T2/T3 有交叠（Evidence 重复 ID、pending 持久化失败）——先做 T2/T3 时若已覆盖则此处跳过，避免重复。
