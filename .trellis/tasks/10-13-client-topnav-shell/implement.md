# 执行计划：用户端顶栏外壳

## 前置

- 任务已在 `planning`；本文件与 `prd.md`、`design.md` 齐备后 `task.py start`。
- 工作目录：`C:\workspace\project\AnimeTracker`；改动范围限于 `frontend/client/**` 与 `.trellis/spec/frontend/directory-structure.md`。

## 顺序清单

### 1. 导航数据（`frontend/client/src/components/app-shared.tsx`）

- [ ] `SidebarNavItem` → `NavItem`（去 `subItems`）；删除 `SidebarNavGroup`。
- [ ] `guestNavGroups` → `publicNavItems: NavItem[]`（扁平 3 项，保留原图标）。
- [ ] `memberNavGroup` → `memberNavItems: NavItem[]`（扁平 3 项）。
- [ ] 删除 `footerNavLinks`、`PATH_TITLES`、`titleForPath`。
- [ ] 保留 `isNavItemActive`、`AppPathContext`/`useAppPath`、`ShellUserContext`/`useShellUser`。

### 2. 外壳（`components/app-shell.tsx`）

- [ ] 去 `SidebarProvider`/`SidebarInset`/`AppSidebar` 与 `[--app-wrapper-max-width:80rem]`。
- [ ] 改为 `<div className="flex min-h-svh w-full flex-col"><AppHeader />{children}</div>`。

### 3. 顶栏（`components/app-header.tsx`）

- [ ] 接入 `useScroll(10)`；`scrolled` 时加边框/背景模糊。
- [ ] 左簇：`Logo` → `/`、`Separator`、`publicNavItems`（`Button asChild variant=ghost|secondary` + `isNavItemActive`）。
- [ ] 右簇：搜索表单（保留）、`ThemeSwitcher`、`Separator`、`NavUser`/登录按钮、`MobileNav`。
- [ ] 移除 `CustomSidebarTrigger`、`AppBreadcrumbs` 及其 import。
- [ ] 内层 `<nav className="mx-auto flex h-14 w-full max-w-[1400px] items-center justify-between gap-2 px-4 md:px-6">`。
- [ ] 链接用 react-router `<Link>`（不是 `<a href="#">`）。

### 4. 移动抽屉（`components/mobile-nav.tsx`）

- [ ] 汉堡 `Button size="icon" variant="outline"`，`aria-controls`/`aria-expanded`/`aria-label`。
- [ ] `Portal className="top-14" id="mobile-menu"` + `PortalBackdrop`。
- [ ] 公开项 +（`useShellUser()` 非空时）个人项，每个 `Link` `onClick={() => setOpen(false)}`。
- [ ] 底部登录/退出动作（匿名显示登录，登录显示退出）。
- [ ] 删除 `components/header.tsx`（脚手架 `Header`/`navLinks`），确认无残留 import。

### 5. 头像菜单（`components/nav-user.tsx`）

- [ ] `memberNavItems.map` 渲染导航项 + `onSelect` navigate。
- [ ] 保留「退出登录」与 `completeLogout` 流程。

### 6. 删除

- [ ] `components/app-sidebar.tsx`、`components/nav-group.tsx`、`components/app-breadcrumbs.tsx`、`components/custom-sidebar-trigger.tsx`。
- [ ] `components/ui/sidebar.tsx`、`components/ui/sheet.tsx`、`components/ui/kbd.tsx`、`hooks/use-mobile.ts`。

### 7. 页面偏移

- [ ] `pages/Agent.tsx`：根加 `mx-auto w-full max-w-[1400px] p-4 md:p-6`；高度改 `h-[calc(100vh-6.5rem)]`（顶栏 3.5rem + 上下内边距）。
- [ ] `pages/SubjectDetail.tsx`：复核 `md:top-20`（顶栏 3.5rem + 间距），必要时调整。

### 8. 测试（`src/test/shell.guards.test.tsx`）

- [ ] 改断言：公开项存在（`首页`/`每周日程`/`番剧索引`）；匿名不含 `我的追番`/`个人中心`。
- [ ] 登录态个人项断言改为「点击头像后」再查（`user-event`），或断言顶栏不直接渲染。
- [ ] `agent.float.test.tsx` 确认仍可挂载 `ClientLayout`。

### 9. 文档

- [ ] `directory-structure.md` 更新「未接线脚手架」段与 client 外壳描述。**保持原行尾。**
- [ ] 复核 `index.md` / `component-guidelines.md` 中外壳措辞是否仍准确。

## 验证命令

```bash
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm run build
```

浏览器（免登录，`:5173`）：

1. `/`、`/schedule`、`/anime` 桌面无侧栏、顶栏公开项高亮随路径变化、滚动触发模糊。
2. 移动视口汉堡开合、点击链接关闭、背景不滚动。
3. `/login` 与未知路径 404 仍整屏无顶栏。
4. 页面有效宽度 1280 → 1400。

## 审查门

- 第 1–6 步完成后跑一次 `typecheck`，消除所有悬空 import（删除集是主要失败源）。
- 第 8 步后跑完整 `npm test`。
- 第 9 步后核对 `git diff --stat` 未触碰 `frontend/admin/**`。

## 回滚点

- 单提交；`git revert <sha>` 即可整体回退。