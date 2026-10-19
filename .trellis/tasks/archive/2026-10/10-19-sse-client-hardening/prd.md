# SSE 客户端加固：帧解析、错误分类与结束锁

## Goal

消除 SSE 客户端路径上的静默错误面，把「后端契约明确、前端实现脆弱」的差距补齐。本任务只改 `packages/shared/src/sse.ts` 与 `packages/shared/src/hooks/useAgentChat.ts`（及各自测试），不动后端。

## Background

`hook-guidelines.md` 已把 SSE 客户端登记为已知债务，问题分两层：

**`sse.ts`（31 行，传输层）**
- 只按单个换行 `\n` 切分，未按 SSE 规范以空行（`\n\n`）分帧——遇到值里含换行的多行帧会被切碎。
- 不校验响应 `Content-Type` 是不是 `text/event-stream`——后端报错页/JSON 会被当流读。
- 流结束时 `buf` 里的尾帧残片没有 flush——最后一帧若不带结尾换行会被丢弃。

**`useAgentChat.ts`（消费层）**
- 未区分事件类型：任何含 `content.text` 的事件都会拼进正文，`status` / `function_call` 的 error 状态没有单独通道。
- `is_end` 只跳过当前帧，不锁住后续帧——结束帧之后的脏数据仍会污染正文。
- SSE 的 401/403 走通用中断分支，未区分「主动 Abort」与「故障断开」（spec 原文：『SSE 的 401/403 当前会进入通用中断分支，没有 Axios 自动刷新，也未区分主动 Abort 与故障』）。

权威契约来源：`docs/spec/openapi.yaml` 的 SSE 段（`text/event-stream`、单帧 `SSEFrame`、`type ∈ {answer, thinking, function_call, status}`、结束帧以 `is_end=true` 表达，**无独立 `type=end`**）。

## Requirements

- **R1 传输层（sse.ts）**：
  - 以空行分帧（`\r?\n\r?\n`），帧内多行 `data:` 按规范拼接；
  - 校验响应 Content-Type 含 `text/event-stream`，否则抛出可读错误；
  - 流结束时 flush `buf` 中残留的未终结帧；
  - 主动 `Abort` 与网络/协议故障分开抛出，调用方能区分。
- **R2 消费层（useAgentChat.ts）**：
  - 按 `type` 分发：`answer` → 正文、`thinking` → 思考区、`function_call` → 工具步骤、`status` → 状态通道；含 `content.text` 的非 `answer`/`thinking` 事件不再落入正文；
  - `is_end=true` 之后锁住流，后续帧一律忽略；
  - `function_call` / `status` 的 error 状态有单独处理（工具步骤标 error，不停在 running）；
  - 401/403 显式进鉴权失败分支，不与主动 Abort 混淆。
- **R3 测试**：为两类改动各补 Vitest 用例——sse.ts 的分帧/Content-Type/尾帧/Abort；useAgentChat 的类型分发/结束锁/error 状态/鉴权失败。至少覆盖 spec 要求：「SSE 改动必须补 parser、状态机、断开与鉴权失败测试」。
- **R4 文档收尾**：`hook-guidelines.md` 的「已知债务」条目在行为修复后删除或改写为现状描述。

## Out of Scope

- 后端 SSE 帧格式、Spring 转发空行行为（`openapi.yaml` 已知债务 #3，另案）。
- SSE 401 自动刷新重试（spec 标注「后续应实现」，本任务只做「显式分类」，不做刷新闭环）。
- client/admin 各自展示层的视觉改动。

## Acceptance Criteria

- [x] AC1：`sse.ts` 以空行分帧、校验 Content-Type、flush 尾帧、区分 Abort 与故障。
- [x] AC2：`useAgentChat.ts` 按 type 分发四类事件，`is_end` 后锁帧，`function_call`/`status` error 单独处理。
- [x] AC3：新增 Vitest 用例覆盖上述行为，`cd frontend && npm test` 全绿（用例数较基线 125 增加）。
- [x] AC4：`hook-guidelines.md` 的「已知债务」段更新，不再描述已修复的行为。
- [x] AC5：不改后端任何文件（`git diff --stat` 无 `backend/**`）。

## 待办（另案，不进本任务）

- **P2 · 产品级**
  - 管理端正式化：把演示登录替换为真实鉴权 + 角色权限，补全骨架页面（`user.role` 与 JWT 机制已具备）。
  - Agent 个性化推荐深化：画像维度细化、推荐附理由、冷启动兜底。
  - 多用户形态：注册开放、数据隔离、权限细分、内容审核。
- **P3 · 工程级**
  - 容器化 / CI 部署流水线（README 已列为 🚧）。
  - OpenAPI 漂移自动校验（现手工维护，`openapi.yaml` 4 条已知债务）。
  - SSE 401 自动刷新闭环（spec 已标注「后续应实现」）。
