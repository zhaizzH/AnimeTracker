# 执行计划：409 冲突连环弹

> 关联 [prd.md](./prd.md)。TDD：每步先红后绿。

## 步骤 1：`asRunConflict` 带出 capabilities

- [x] `shared/src/api/conflict.ts`：返回值加 `capabilities: string[] | null`；字段缺失为 `null`（「不知道」），显式数组原样透出。
- [x] 用例：`[]` 透出空数组；缺字段为 `null`；已有两条形态用例补断言。

## 步骤 2：`resolveConflict` 加锁 + 失败不重发

- [x] `useAgentChat.ts`：
  - 同步锁 ref，进入即置位、`finally` 复位；
  - `stopRun` 抛错时**不** `send`，改为把错误写回 `conflict.error`（保留面板与原文）。
- [x] 用例：
  - 反转既有「停活跃 run 失败时仍尝试重发」→ 「失败不重发、面板保留、带内联错误」；
  - 双击只触发一次 `stopRun` + 一次重发。

## 步骤 3：两端面板按 capabilities 呈现 + 文案

- [x] client/admin：按钮文案「停止并发送」；`capabilities` 显式不含 `interrupt` 时禁用并给 `title` 说明。
- [x] 用例：非法能力 → 禁用；缺字段 → 可用；文案断言同步；内联错误文案渲染。

## 步骤 4：文档口径

- [x] `hook-guidelines.md` 的 Scenario 补：`stop` 同步置 `CANCELLED` 且 `active_for_session` 只认 `RUNNING`，因此成功停止后立即重发不会 409。
- [x] 归档任务 `implement.md` 附注改写三场景（A stop 失败 / B 双击 / C 多标签），删掉被证伪的解释。

## 步骤 5：验证

- [x] `frontend`：三包 `npx vitest run` + `npm run typecheck`；对照基线 32 文件 / 191 用例只增不减。
- [x] 提交前派 `trellis-check` 审工作树。

## 回滚点

每一步一个提交；步骤 3 只改渲染，可单独 revert 而不影响步骤 1–2 的行为修复。

## 实现附注

- `title` 挂在外层 `<span>`：disabled 的 `<button>` 在 Chrome/Safari 不派发 hover，直接写 title 用户看不到。
- 回填 effect 跳过 `conflict.error` 的更新：停 run 失败会换对象引用，按引用触发会把用户正在编辑的输入覆盖回原文。
- 「重试期间清掉旧 error」那一行只能在 `act` 内部观察到，没有稳定断言（已知不可测窗口，代码保留）。
- 用例数 191 → 202（shared 77 / client 46 / admin 79）。
