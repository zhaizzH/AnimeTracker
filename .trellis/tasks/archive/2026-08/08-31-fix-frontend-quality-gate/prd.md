# 修复前端质量门禁

## Goal

让 `frontend` 根目录的依赖、类型检查、测试和构建门禁在干净安装后具有明确且可重复的结果，避免 Bootstrap 任务在质量检查阶段被既有环境问题阻塞。

## Background

- `frontend/client/src/components/AgentMarkdown.tsx:3` 导入 `remark-gfm`。
- `frontend/client/package.json:21` 和 `frontend/package-lock.json` 已声明并锁定 `remark-gfm@4.0.1`，但当前 `frontend/node_modules` 缺少该包；这是本地安装状态漂移，不需要修改依赖清单。
- `frontend/admin/package.json` 的测试脚本是 `vitest run`，但 admin 当前没有测试文件，所以根目录 `npm test` 返回退出码 1。
- shared 的 6 个测试、client 首页测试、Java Maven 门禁和 Python 的 3 个 pytest 均能运行；client 另两个套件仅因缺少 `remark-gfm` 无法加载。

## Requirements

- 从现有 lockfile 恢复前端依赖，不改变 `package.json` 或 `package-lock.json` 中的依赖版本。
- Admin 必须至少运行一项有业务价值的测试，不允许用 `--passWithNoTests` 绕过零测试状态。
- 保持现有 npm workspace 命令入口；开发者仍从 `frontend` 根目录运行质量门禁。
- 不修改业务 API、页面功能、鉴权行为或 UI 样式。
- 若新增测试，沿用 `frontend/admin/vitest.config.mts`、Testing Library 和现有中文测试命名风格。
- 为 `RequireAdmin` 增加最小守卫测试，覆盖未登录、非管理员和管理员三个鉴权分支。

## Acceptance Criteria

- [x] `frontend/node_modules/remark-gfm` 可由现有 lockfile 正常恢复，依赖清单无版本变更。
- [x] `cd frontend && npm run typecheck` 退出码为 0。
- [x] `cd frontend && npm test` 退出码为 0，且不会掩盖 shared/client 的失败。
- [x] `cd frontend && npm run build` 退出码为 0。
- [x] Admin 测试验证未登录用户跳转登录页、非管理员被拒绝、管理员可以看到受保护内容。
- [x] Git diff 只包含本任务批准范围内的测试或测试配置变更。

## Out of Scope

- 提升整个 admin 的测试覆盖率。
- 修改 `AgentMarkdown`、路由守卫或页面业务行为。
- 升级 npm 包版本或重构 workspace 脚本。
- 修复与本次质量门禁无关的后端或前端功能问题。

## Key Decisions

- 不使用 `--passWithNoTests`；Admin 门禁必须至少执行一项有业务价值的测试。
- 首个测试聚焦 `RequireAdmin`，因为它是管理端访问控制边界，价值高于仅渲染 `App` 的无行为 smoke test。
- 此任务按轻量任务处理，仅使用 `prd.md`；不创建不必要的 `design.md` 和 `implement.md`。
