# 用户端外壳与路由：app-shell-2 + 12 条路由重接

父任务：`.trellis/tasks/10-12-frontend-rebuild`（技术设计与总体约束见父任务 `design.md`）。

## Goal

在 client 安装 `@efferd/app-shell-2` 并改写为用户端外壳，重建路由守卫与全部 12 条路由。完成后未登录守卫与导航可用；业务页面内容由子任务 4 填充。

## 前置依赖

子任务 `10-12-rebuild-prep`（旧实现已删）与 `10-12-ui-infra`（Tailwind/shadcn/主题就绪）。**顺序理由**：外壳依赖 `components/ui` primitive 与 `cn()`。

## Requirements

- **R1 安装**：`cd frontend/client && npx shadcn@latest add @efferd/app-shell-2`；记录实际落地路径与 target 重写。
- **R2 外壳**：`AppShell`（`SidebarProvider` + 侧栏 + `AppHeader`）作 `layouts/ClientLayout.tsx`；继续作 router 父级 `element` 并渲染 `<Outlet />`。
- **R3 导航改写**：模板 demo（product/workspace/admin 分组 + changelog + dashboard 骨架）改为真实入口：首页 `/`、每周日程 `/schedule`、番剧索引 `/anime`，加登录后入口（我的追番 / AI 助手 / 个人中心）；面包屑映射中文。
- **R4 未接线件处理**：删除 `dashboard-skeleton.tsx`、`latest-change.tsx`（非看板应用不需）。
- **R5 路由重建**：12 条路由含 `RequireAuth`（`my-collections`/`agent`/`profile`）与 `PublicOnly`（5 个认证页）语义不变，保留 `lazy` + Suspense 骨架 fallback。
- **R6 Agent 挂载**：保留 `<AgentChatProvider key={user?.id ?? 'anonymous'}>` 与 `{user && <AIAssistantFloat />}` 的挂载位置与重置语义。
- **R7 主题切换 UI**：外壳内提供明暗切换开关（接 `useThemeStore`）。

## Acceptance Criteria

- [ ] AC1：`npm run dev:client` 外壳可渲染，侧栏三项导航可跳转。
- [ ] AC2：未登录访问 `/my-collections`、`/agent`、`/profile` 重定向 `/login` 且带 `state.from`；登录后回跳原路径。
- [ ] AC3：已登录访问 `/login` 等 `PublicOnly` 页重定向 `/`。
- [ ] AC4：`npm run typecheck` 通过；路由文件无 antd 导入。
- [ ] AC5：Agent 浮窗在登录态下挂载、在 `/agent` 下不重复出现（行为由子任务 4 验证完整）。

## Out of Scope

- 页面数据内容（子任务 `10-12-client-pages`）。
- admin（子任务 `10-12-admin-rebuild`）。

## 交付给父任务

可导航、守卫正确的 client 外壳与路由骨架。
