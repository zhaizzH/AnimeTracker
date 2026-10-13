# 用户端外壳去侧栏改顶部导航

## Goal

移除用户端 `ClientLayout` 的 `Sidebar`/`SidebarProvider` 外壳，改为 `@efferd/header-1` 风格的纯顶部导航：公开项（首页/每周日程/番剧索引）平铺顶栏，个人项（我的追番/AI 助手/个人中心）收进右侧头像菜单，移动端用 efferd `Portal` 全屏抽屉。删除仅服务于侧栏的 primitive 与 efferd 脚手架 `Header`，并同步前端 spec。

## Background

用户请求「把用户端 `html/body/div/div/div` 侧边栏改为 `npx shadcn@latest add @efferd/header-1`」。

排查结论：`@efferd/header-1` **不含侧栏**——它是营销页头（`Logo` + Features/Pricing/About + Sign In/Get Started + 汉堡菜单），只产出 `header.tsx` 与 `mobile-nav.tsx`。当前侧栏实际上是 `@efferd/app-shell-1` 的侧栏（`app-{shell,sidebar,header,shared,breadcrumbs}` + `nav-user` 正是该 block 的完整文件集，提交 `41a2c44a` 已入库）。因此字面需求不可执行，用户确认目标为「整个外壳去掉侧栏，改为 header-1 的纯顶部导航」。

## Requirements

### R1 外壳形态

- `AppShell` 不再渲染 `SidebarProvider` / `AppSidebar` / `SidebarInset`。
- 新布局：吸顶顶栏 + 内容区；外壳**不再提供**统一内边距与 `max-w-80rem` 包裹，容器由各页面自持（现状页面已自带 `mx-auto w-full max-w-[*] p-6`）。
- 保留 `AppPathContext` / `ShellUserContext`（顶栏、移动抽屉、头像菜单仍需读路径与登录态）。

### R2 顶栏（header-1 形态）

- 左：`Logo`（→ `/`）+ 公开项（`首页` / `每周日程` / `番剧索引`），当前路径高亮。
- 右：搜索表单、`ThemeSwitcher`、头像菜单（登录）或登录按钮（匿名）、移动端汉堡（`md:hidden`）。
- 吸顶态：`useScroll` 驱动滚动后加背景/边框/模糊，形态对齐 header-1 的 `scrolled` 分支。
- 内层 `nav` 与页面同宽居中（`mx-auto max-w-[1400px] px-4 md:px-6`）。

### R3 移动端抽屉

- `MobileNav` 复用 efferd `Portal` + `PortalBackdrop`：展开时全屏覆盖、锁定背景滚动；渲染公开项 +（登录时）个人项 + 登录/退出。
- 点击任一链接后**关闭抽屉**（导航不改变组件挂载状态，需显式关闭）。
- 不依赖 efferd 脚手架导出的占位 `navLinks`；改用真实导航数据。

### R4 个人项入头像菜单

- `NavUser` 下拉用 `memberNavItems` 渲染导航项（补齐当前缺失的 `AI 助手`），保留既有「退出登录」。

### R5 死代码清理

- 删除：`components/header.tsx`（efferd 脚手架 `Header`）、`components/app-sidebar.tsx`、`components/nav-group.tsx`、`components/app-breadcrumbs.tsx`、`components/custom-sidebar-trigger.tsx`。
- 删除仅服务于侧栏链的 primitive：`components/ui/sidebar.tsx`、`components/ui/sheet.tsx`、`components/ui/kbd.tsx`、`hooks/use-mobile.ts`。
- 保留并接线：`components/portal.tsx`、`hooks/use-scroll.ts`。
- **`frontend/admin` 的同名副本一律不动。**

### R6 垂直偏移修正

- 移除外壳内边距后，页面根**自持内边距**。`pages/Agent.tsx` 根需补内边距，并把硬编码高度从「假设 8rem」改为「顶栏 3.5rem + 自身内边距」。
- `pages/SubjectDetail.tsx` 的 `md:sticky md:top-20` 按新顶栏高度复核（可保持）。

### R7 测试

- `src/test/shell.guards.test.tsx` 的「侧栏链接计数」断言改为顶栏/导航断言；个人项在头像下拉中默认不挂载，需交互后再断言。
- 不新增测试文件（client 仍 6 个）。

### R8 文档同步

- `.trellis/spec/frontend/directory-structure.md`：更新「未接线脚手架」段（`header.tsx` 删除；`mobile-nav`/`portal`/`use-scroll` 已接线），补 client 外壳现为「顶栏 + 移动抽屉、无侧栏」。
- 保持 `.trellis/spec/frontend/*.md` 原有行尾（混合 CRLF/LF），不得整文件刷成 LF。

## Acceptance Criteria

- [ ] `AppShell` 不含 `Sidebar*`/`app-sidebar` 引用；`html/body/div/div/div` 的侧栏结构消失。
- [ ] 桌面渲染单条吸顶顶栏，公开项随路径高亮；滚动触发顶栏背景/模糊态。
- [ ] 移动端汉堡展开 `Portal` 抽屉，点击链接跳转并关闭，背景滚动被锁定。
- [ ] 登录时头像菜单含 `我的追番`/`AI 助手`/`个人中心`/`退出登录`；匿名时仅顶栏登录按钮、无个人项。
- [ ] `components/header.tsx`、`app-sidebar.tsx`、`nav-group.tsx`、`app-breadcrumbs.tsx`、`custom-sidebar-trigger.tsx`、`ui/sidebar.tsx`、`ui/sheet.tsx`、`ui/kbd.tsx`、`hooks/use-mobile.ts` 已删除且无残留引用。
- [ ] `frontend/admin` 未改动（`git status` 无 admin 变更）。
- [ ] `cd frontend && npm run typecheck && npm test && npm run build` 通过。
- [ ] 免登录浏览器验证四条：桌面无侧栏 + 高亮、移动抽屉开关、`/login` 与 `*` 404 仍整屏无顶栏、页面宽度由 1280 变 1400。
- [ ] `directory-structure.md` 同步且行尾未被改写。

## Notes

- 登录态验证：仓库无可用凭据，个人项/退出以源码 + 更新后测试为准（沿用 drift-audit 的「免登录优先、登录态以源码为准」原则）。
- 本次不重跑 `shadcn add`，只改写仓库内既有文件；`@efferd` CLI 的既有缺陷（`from "cn"`、非 forwardRef Button、React 19 语法）不适用。
