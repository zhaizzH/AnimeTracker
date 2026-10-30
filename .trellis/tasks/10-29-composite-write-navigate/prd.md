# 复合指令：写入后导航

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

- [ ] 「把《孤独摇滚》加入想看，然后打开我的收藏」：出预览 → 用户确认 → 写成功 → 跳 `/my-collections`，浮层保持打开
- [ ] 同上但用户回复「取消」：不写入，也**不导航**
- [ ] 同上但 pending 已过期：提示重新发起，不导航
- [ ] 多候选标题场景：用户先选候选 → 再出预览 → 确认 → 写成功 → 才导航
- [ ] 「打开我的收藏」（纯导航）不触发任何写工具
- [ ] 三个 Domain agent 均可做纯导航；`admin_agent` 仍无该工具
- [ ] 写入类 `pending_action` 存在且本回合未清空时，`request_navigation` 被拒绝且不写 state（即使模型误调）
- [ ] 写入成功后同一回合内 `request_navigation` **能成功**（门控不误拦，这是原方案的缺陷点）
- [ ] prompt 改动已同步到 Redis 中的 `client_recommend_agent_prompt`（Managed prompt，只改文件不够）
- [ ] 全量测试不回归

## Out of Scope

- 不重复注册工具（`navigation-graph` 已完成三节点注册）
- 不支持「导航后再写入」的反向顺序
- 不做跨多轮的导航队列
