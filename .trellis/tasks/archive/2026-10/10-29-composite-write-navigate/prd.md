# 复合指令：写入后导航

> **状态：代码已完成**（2026-10-30）。9 条 AC 中 8 条达标；第 9 条（prompt 同步 Redis）是**运维项**，需手工执行。详见文末「验收证据」。

## Goal

支持「把这部加入想看，然后打开我的收藏页」这类**一回合内写入 + 跳转**的复合指令，且严格先写后导航。

**阻塞**：依赖 `navigation-graph` 先完成。

## Background

ADR 0001 强制所有写操作走「预览 → 确认 → 执行」。`gateway.py` 已有确定性短路：存在 pending 且当前回合是精确确认词时强制路由 `recommend_agent` 并置 `write_confirmed=True`；`write_guard.require_confirmed_write` 在工具层再做硬门禁。

复合指令的正确性依赖这条既有链路不被绕过：**导航必须发生在写入真正完成之后**，不能在预览阶段就跳走。

## Requirements

- `recommend_agent` 在**已有** `request_navigation`（由 child `navigation-graph` 为三个 Domain agent 统一注册）基础上，增加**写入未完成不得导航**的硬门控
- 更新 `client_recommend_agent_prompt`：说明可在写入完成后附加导航；**预览阶段不得请求导航**
- 新增服务端硬约束：`pending_action` 为写入类（`ADD_TO_WISHLIST` / `SET_COLLECTION_TYPE` / `COLLECTION_PROGRESS_UPDATE`）或为 `SUBJECT_RESOLUTION`，**且本回合尚未清空**时，拒绝写 `navigation_intent`。不依赖 prompt 自觉
- **门控信号来自 TurnState（本回合共享可变事实），不读 `state["pending_action"]`**——后者是回合开始时的快照，写成功后不更新，读它会拦掉唯一该放行的那次导航。详见 [design.md](./design.md) D1/D2
- 「写成功」以 `response.succeeded` 非空为准，不能以 `Clear` 事件为准（确定性失败也发 `Clear`）
- 写入未获确认 / 用户否定 / pending 过期时，不得产生 `navigation_intent`
- 多步写入（如 `SUBJECT_RESOLUTION` 待选 → 选中 → 预览 → 确认）全链路走完后才允许导航；走完打标后门控自然放行，不会堵死
- 纯导航请求（不含写入）行为不回归

## Acceptance Criteria

- [x] 「把《孤独摇滚》加入想看，然后打开我的收藏」：出预览 → 用户确认 → 写成功 → 跳 `/my-collections`，浮层保持打开
- [x] 同上但用户回复「取消」：不写入，也**不导航**
- [x] 同上但 pending 已过期：提示重新发起，不导航
- [x] 多候选标题场景：用户先选候选 → 再出预览 → 确认 → 写成功 → 才导航
- [x] 「打开我的收藏」（纯导航）不触发任何写工具
- [x] 三个 Domain agent 均可做纯导航；`admin_agent` 仍无该工具
- [x] 写入类 `pending_action` 存在且本回合未清空时，`request_navigation` 被拒绝且不写 state（即使模型误调）
- [x] 写入成功后同一回合内 `request_navigation` **能成功**（门控不误拦，这是原方案的缺陷点）
- [ ] prompt 改动已同步到 Redis 中的 `client_recommend_agent_prompt`（**运维项，需人工执行**。`prompt_repository` 快照优先于文件；须 PUT `agent:prompt:client_recommend_agent_prompt` 的 `promptContent` 并重启刷新快照）
- [x] 全量测试不回归

## Out of Scope

- 不重复注册工具（`navigation-graph` 已完成三节点注册）
- 不支持「导航后再写入」的反向顺序
- 不做跨多轮的导航队列

## 验收证据（2026-10-30）

### 门禁结果

| 门禁 | 结果 |
|---|---|
| `cd backend/agent && uv run pytest -q` | **931 passed**（基线 899，+32） |
| `cd backend/agent && uv run pytest tests/contracts -q` | 156 passed（无漂移） |
| `cd backend/agent && uv run ruff check .` | All checks passed |

### AC → 测试映射

| 验收项 | 测试 |
|---|---|
| 写入类 pending 未清空时拒绝导航且不写 state | `test_request_navigation_tool.py::test_gated_tool_rejects_navigation_while_write_pending_unresolved`（断言 `set(update)=={"messages"}`）、`test_graph_post_routing.py::test_recommend_agent_rejects_navigation_while_write_pending_unresolved`（图级） |
| **写入成功后同回合可导航**（原方案缺陷点） | 三层：`test_navigation_gate.py::test_execute_with_clear_marks_pending_resolved_and_keeps_response`（打标 + 返回 dict 不变）、`test_request_navigation_tool.py`（工具层放行）、`test_graph_post_routing.py::test_recommend_agent_allows_navigation_after_execute_marks_turn`（**图级 execute → 导航**） |
| 取消后不写入也不导航 | `test_navigation_gate.py::test_cancel_marks_pending_resolved`、`test_graph_post_routing.py::test_recommend_agent_allows_navigation_after_cancel_marks_turn` |
| 多候选链路不堵死 | `test_navigation_gate.py` 参数表 `("SUBJECT_RESOLUTION", RESOLVED) → 允许`、`("SUBJECT_RESOLUTION", UNRESOLVED) → 拒绝` |
| 三个 Domain agent 纯导航不回归；admin 无工具 | `test_graph_post_routing.py::test_each_domain_agent_reaches_emitter`（parametrize）、`test_admin_path_never_touches_emitter` |
| 全量不回归 | 931 passed；三条写链路 `test_wishlist` / `test_collection_type` / `test_collection_progress` 49 passed |
| prompt 只改 recommend | `test_client_prompt_contract.py::test_search_and_discover_prompts_do_not_carry_write_gate_rules`（反向钉住） |

### 变异验证（trellis-check 独立执行并还原）

| 变异 | 转红 |
|---|---|
| 删 `previewable.py` 两处 `mark_pending_resolved()` | `test_execute_with_clear_marks_pending_resolved_and_keeps_response`、`test_cancel_marks_pending_resolved`、`test_recommend_agent_allows_navigation_after_cancel_marks_turn` |
| `recommend.py` 去掉 `gated=True` | `test_recommend_agent_rejects_navigation_while_write_pending_unresolved` |

### 实现期修正（对初稿的偏离）

1. **`write_outcome` 三态 → 单个 `pending_resolved` 布尔量**。三条写链路成功形态不同（只有 wishlist 有 `succeeded` 列表），而「确定性失败」与「成功」对门控同等放行，三态是死字段。详见 design D2。
2. **打标要改 `PreviewableAction` 的两个方法**（`cancel` 与 `execute`），只改 `execute` 会漏取消分支。
3. **测试不能手塞 `write_confirmed`**：`gateway_router` 会用「当前问题是否明确确认」覆盖它（`gateway.py`），所以图级 execute 用例必须让 `current_question="确认"`，同时这也会触发 gateway 对 `recommend_agent` 的确定性短路。

### 待运维

线上 Redis 的 `agent:prompt:client_recommend_agent_prompt` 需同步本次新增的「复合指令：写入后跳转」六条。硬门控会兜住违规导航（用户看到的是拒绝而非遵守），但体验差异真实存在。
