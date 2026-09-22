# admin 应用外壳：app-shell-5 替换 AdminLayout

> 父任务：`09-21-admin-tailwind-shadcn-dashboard`。本子任务覆盖其 `implement.md` 的**阶段 C**。

## Goal

用 `@efferd/app-shell-5` 重写 admin 的应用外壳，替换 `admin/src/layouts/AdminLayout.tsx`，并启用主题切换支持暗色。

用户价值：admin 获得统一、现代的应用框架（侧边栏 + 顶栏 + 用户菜单 + 主题切换），且为后续页面迁移提供 shadcn 语境下的布局容器。

## Dependencies

**前置依赖：`09-21-admin-ui-foundation` 必须已完成。** 本子任务需要其交付的 Tailwind + shadcn 地基、`@/` 别名、`components.json` 中的 `@efferd` 命名空间、sonner toast 封装与 `useAuthStatus()`。

**被依赖**：`09-21-admin-dashboard-block` 与 `09-21-admin-pages-migration` 均需本子任务完成后再开始（它们假定页面已运行在 shadcn 外壳内）。

## Requirements

- R1：执行 `shadcn add @efferd/app-shell-5`，含其 `registryDependencies` 中的 `@efferd/logo`、`@efferd/use-keypress` 及 `avatar` `breadcrumb` `button` `dropdown-menu` `input-group` `kbd` `separator` `sidebar` `tooltip`；引入 `next-themes`。
- R2：重写 `app-sidebar` 导航为现有 **7 个菜单项**，**删除 block 自带的 demo 导航**：
      `/admin/dashboard` 看板 · `/admin/subjects` 番剧管理 · `/admin/users` 用户管理 · `/admin/import` 导入管理 · `/admin/logs` 日志审计 · `/admin/agent-config` Agent 配置 · `/admin/agent-chat` Agent 对话。
- R3：导航当前路由高亮正确（等价于现有 AntD `Menu` 的选中行为）。
- R4：`nav-user` 接入 `useAuthStore` 的 `user.username`，显示登录用户名。
- R5：退出登录复用现有 `completeLogout(authApi.logout)`：
      - 成功 → 跳转 `/admin/login`；
      - 失败 → 提示 `退出失败，请重试`；
      - **保留 `isLoggingOut` 防重复提交语义**（提交中禁用按钮，文案 `退出中…`）。
- R6：接入 `theme-switcher`，与 shared `useThemeStore` / `resolveMode` 对齐，避免两套主题状态互相打架；`.dark` 变量由 foundation 阶段已备好。
- R7：`admin/src/layouts/AdminLayout.tsx` 替换为 AppShell 实现；`admin/src/main.tsx` 去掉 `ConfigProvider` + `antdTheme` + `antd/dist/reset.css` 引入。
- R8：`admin/src/router.tsx` 的 `AdminLayout` 引用随实现更新；`lazy` + `Suspense` 与 `RequireAdmin` 包裹关系保持不变。

## Acceptance Criteria

- [ ] AC1：7 个菜单项逐一点击均可导航到对应路由，无死链。
- [ ] AC2：当前路由高亮正确（逐项核对，含刷新后直接落在某子路由的场景）。
- [ ] AC3：顶栏/用户菜单正确显示当前登录用户名。
- [ ] AC4：退出登录**成功路径**跳转 `/admin/login`；**失败路径**出现 `退出失败，请重试` 提示。
- [ ] AC5：退出提交中按钮禁用且文案为 `退出中…`，重复点击不产生第二次请求。
- [ ] AC6：主题切换器可用，切换后 `.dark` 生效，刷新后主题保持；admin 与 client 的主题状态不发生互相干扰。
- [ ] AC7：`cd frontend && npm run typecheck` 通过；`npm test -w admin`（现有 `guards.test.tsx`）通过；`npm run build` 成功。
- [ ] AC8：`admin/src/main.tsx` 与 `AdminLayout.tsx` 中不再出现 `ConfigProvider` / `antdTheme` / `antd/dist/reset.css`。

## Out of Scope

- 迁移任何页面内容（Dashboard 属 `admin-dashboard-block`；其余属 `admin-pages-migration`）。本子任务只负责外壳。
- 移除 `admin/package.json` 的 antd / echarts 依赖。
- `AdminLogin` 页面（它不在外壳内，属 `admin-pages-migration`）。
- 实现 block 自带的 ⌘K 全局搜索的业务逻辑（保留 UI 骨架即可，搜索目标未定义）。

## Key Decisions（继承父任务）

- D1：用 `@efferd/app-shell-5` 替换 `AdminLayout`，**保留现有 7 个菜单项**，不残留 block 的 demo 导航。
- D5：支持暗色，启用主题切换。

## 技术要点

- AppShell 自带 `app-breadcrumb`、`app-search`、`latest-change` 等 demo 区块：**面包屑可保留**（有导航价值），`app-search` 与 `latest-change` 若无法对应真实业务，应移除而非填充假数据。
- `use-keypress` 是 `app-search` 的 ⌘K 依赖；若移除 search，需评估该 registry 依赖是否仍需要。
- 主题对齐需先读 shared `theme.ts` 的 `resolveMode` 与 `store/theme.ts`，再决定 `next-themes` 的接入方式（受控 vs 非受控）。

## 风险

| 风险 | 缓解 | 回滚 |
|---|---|---|
| AppShell 引入 `next-themes` 与 shared 主题 store 冲突 | 先对齐 mode 解析规则再接入切换器；本阶段单独提交 | 回退主题部分，保留外壳 |
| demo 区块残留假数据 | 逐区块核对，无法对应真实业务的一律移除 | — |
| 移除 `reset.css` 后页面样式漂移 | 本阶段后续子任务会替换页面；漂移需记录为已知过渡态 | — |
