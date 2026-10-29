# 修复 409 冲突连环弹

## 背景

`10-27-agent-run-reconnect-frontend` 交付了 409 冲突三选一，但留下三个真实缺口。原附注把根因写成「stopRun 是逻辑停止，后端 run 未立即结束，所以重发仍会 409」——**这条已被源码证伪**：`backend/agent/app/chat/runs.py:190` 的 `stop()` 同步把状态置为 `CANCELLED`，而 `active_for_session()`（`:184`）只认 `RUNNING`。单进程内，成功的 `stopRun` 之后立刻重发**不会** 409。

真正会造成「面板反复弹」的两条：

1. **stop 失败后仍重发**：`useAgentChat.ts` 的 `resolveConflict` 在 `stopRun` 抛错时 `console.warn` 后照样 `send`，此时活跃 run 仍在 → 必然再 409 → 面板重开，形成循环。
2. **双击打断**：`setConflict(null)` 是异步 state，两次同步点击都读到旧 `conflict` → 两次 `stopRun` + 两次 `send`，第二次必 409。

多标签场景（A 标签有 run，B 标签打断）**不在本任务范围**：那是设计意图，由用户裁决。

## 需求

- **R1** `stopRun` 失败时不重发：保留冲突面板，给出内联错误，用户可原地重试；不得自动再发。
- **R2** `resolveConflict` 同一次尝试只执行一遍（同步锁），双击不会产生第二次请求。
- **R3** 面板按后端 `capabilities` 决定「打断」是否可用：显式不含 `interrupt` 时按钮禁用并说明原因；字段**缺失**时视为可用（缺失是「不知道」，不是「不允许」）。
- **R4** 文案改为「停止并发送」：后端没有排队能力，「插入」承诺了不存在的行为。类型名 `interrupt` 保留（与后端 `capabilities` 对齐）。
- **R5** 文档修正：`hook-guidelines.md` 补「stop 成功即不再是 active run」这条接口事实；归档任务附注删掉被证伪的解释，改为上述三场景。

## 验收标准

- [x] AC1: `stopRun` 抛错时 `streamSse` 调用次数不变（不重发），且 `conflict` 仍在、带内联错误文案
- [x] AC2: 双击 `resolveConflict('interrupt')` 只产生一次 `stopRun` 与一次重发
- [x] AC3: `capabilities: []` 时「停止并发送」禁用；字段缺失时可用；两种情况都有用例
- [x] AC4: 两端按钮文案为「停止并发送」，相关断言同步
- [x] AC5: `hook-guidelines.md` 含「stop 成功 → 不再是 active run」；归档附注不再有「run 未立即结束所以重发会 409」的说法
- [x] AC6: `npm test` 三包与 `npm run typecheck` 全绿，用例数不低于 191

## 范围外

- 多标签跨窗口的状态同步
- 后端排队 / 真正的物理停止
