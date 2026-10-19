# P0 债务清理：前端死文件 + CI 门禁 + 泄露密钥轮换登记

## Goal

在不动摇现有代码结构的前提下清掉三项低风险 P0 债务，让仓库回到「CI 可信、无死文件、密钥风险已处置」的干净基线。本任务不做任何重构、不引入新功能。

## Background

复查发现：

1. **前端死文件**（共 262 行，全部零引用，来源是 10-12 前端重建后未清尾）：
   - `frontend/admin/src/App.tsx`（3 行，内容为 `<div>app ok</div>` 占位，入口实为 `src/main.tsx`）
   - `frontend/admin/src/components/delta.tsx`（88 行）
   - `frontend/admin/src/components/ui/kbd.tsx`（28 行）
   - `frontend/admin/src/hooks/use-keypress.ts`（98 行）
   - `frontend/client/src/components/decor-icon.tsx`（45 行）
   零引用已用「除自身外 grep 引用数为 0」复核确认。
2. **CI 门禁缺口**：`.github/workflows/ci.yml` 的 `frontend` job 只跑 `npm run typecheck`，没有 `npm test`（125 用例）和 `npm run build`——测试失败/构建失败可以绿过 CI。后端 Java/Python 两个 job 已有 `mvn -B test` / `uv run pytest`，本次**不动**。
3. **泄露密钥**：开发库密码 `ZPQ0801yy` 曾在 `docs/test/test-seed.sql` 中入库（提交 `390318dc`、`44715b70`，`bf7c4242` 已删），当前 HEAD 已无该串，但 git 历史仍可检出。另有 `application-local.yml` 里硬编码的同一密码与 `jwt.secret=dev-…`，该文件**未被 git 跟踪**，属本地配置。

## Requirements

- **R1 删死文件**：删除上述 5 个文件；删除后 `npm run typecheck` + `npm test` + `npm run build` 全绿，证明删除无回归。
- **R2 补 CI**：在 `frontend` job 中追加两步 `npm test` 与 `npm run build`（置于 `typecheck` 之后）；不改其它 job、不改 Node 版本。
- **R3 登记密钥**：不改写 git 历史、不改 `docs/test/`（文件已被删除），只做两件事——
  a. 通知维护者轮换 `ZPQ0801yy` 对应的数据库/Redis 密码（历史泄露不可逆，轮换是唯一缓解）；
  b. 在本任务 `research/` 落盘一份 `secret-leak-note.md`，记录泄露范围（含哪些提交、哪些历史文件、缓解动作），作为审计痕迹。
- **R4 不越界**：不重构、不改 UI 组件、不动 `client`/`admin` 的重复 shadcn 原语（ADR-0021 的既定决策），不改任何业务行为。

## Out of Scope

- SSE 客户端加固（另起 P1 任务）。
- OpenAPI 漂移自动校验、容器化、管理端正式化。
- 任何代码重构 / 组件拆分。
- git 历史改写（`git filter-repo` 之类）。

## Acceptance Criteria

- [ ] AC1：5 个目标文件从工作区删除且 `git status` 中无其它多余删除。
- [ ] AC2：本地 `cd frontend && npm run typecheck && npm test && npm run build` 全绿（作为删除无回归的证明）。
- [ ] AC3：`ci.yml` 前端 job 含 `npm test` 与 `npm run build` 两步，顺序在 `typecheck` 之后；改动仅限前端 job。
- [ ] AC4：`research/secret-leak-note.md` 落盘，含泄露提交哈希、文件路径、轮换通知措辞。
- [ ] AC5：无其它任何文件被改动（用 `git diff --stat` 核对，改动应只在：删除的 5 文件 + `ci.yml` + 任务目录）。
