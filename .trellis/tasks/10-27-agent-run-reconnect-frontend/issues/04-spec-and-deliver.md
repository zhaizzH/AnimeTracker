# 04: 收尾：把 run 语义写进规范并交付

**What to build:** 前端 run 重连这套语义不只活在本任务的代码里：下一个改 SSE 的人能从规范里读到「断连不等于停止」「游标是事件序号」「回放必须新建气泡」「409 要弹选择」，并且整包能构建发布。

**Blocked by:** 01、02、03

**Status:** ready-for-agent

- [ ] `npm test`（shared / client / admin 三包）与 `npm run typecheck` 全绿，且相对本任务基线（26 文件 / 145 用例）只增不减
- [ ] `npm run build`（client + admin）通过
- [ ] 前端 hook 规范补齐 run 重连语义：断连≠停止、`after` 是事件序号、回放新建气泡、409 选择、`failed` 不订阅
- [ ] 规范里不复制具体数字与 CI 状态（本仓约定：环境事实以配置文件为准）
- [ ] 本任务 prd 的 AC1–AC8 逐条勾选，未达成项写明原因
