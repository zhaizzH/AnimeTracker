# 技术设计：用户端顶栏外壳

## 边界与契约

### 外壳契约（变更后）

```
AppShell({ children, path, user })
  └─ <div class="flex min-h-svh w-full flex-col">
       <AppHeader />          // sticky top-0 z-50, h-14（内层 nav）
       {children}             // 页面自持容器与该有的滚动区域
```

- 外壳**不再**提供 `p-*` 与 `max-w-*`：页面根自持容器（现状已满足）。
- 外壳仅承担：布局栈、`AppPathContext`、`ShellUserContext` 两个 Context 的注入。
- 保留 `path` / `user` props（`ClientLayout` 已传入，测试以 `MemoryRouter` 直挂 `ClientLayout`）。

### 导航数据契约（`app-shared.tsx`）

```ts
export type NavItem = { title: string; path?: string; icon?: ReactNode; isActive?: boolean };

export const publicNavItems: NavItem[];  // 首页 / 每周日程 / 番剧索引
export const memberNavItems: NavItem[];  // 我的追番 / AI 助手 / 个人中心

export const isNavItemActive: (pathname: string, path?: string) => boolean;  // 不变
export const AppPathContext / useAppPath;        // 不变
export const ShellUserContext / useShellUser;    // 不变
```

- 删除：`SidebarNavItem`、`SidebarNavGroup`、`guestNavGroups`、`memberNavGroup`、`footerNavLinks`、`PATH_TITLES`、`titleForPath`、`subItems` 相关结构（无消费方）。
- 扁平化理由：侧栏的二级 `subItems` 从未被实际数据使用（`guestNavGroups`/`memberNavGroup` 均为单层），顶栏本就扁平的。

### 顶栏交互契约

| 状态 | 表现 |
|---|---|
| 顶部（未滚动） | 透明边框、无背景模糊（`border-transparent`） |
| 滚动 > 10px | 加 `border-border bg-background/95 backdrop-blur-sm supports-backdrop-filter:bg-background/50` |
| 当前路径命中公开项 | 该项 `Button` 用 `variant="secondary"`（或 `isActive` 样式），其余 `ghost` |
| `md` 以上 | 公开项 + 搜索 + 主题 + 头像可见；汉堡隐藏 |
| `md` 以下 | 只留 `Logo` + 汉堡；其余收进 `MobileNav` 抽屉 |

### 移动抽屉

- `MobileNav`：`md:hidden` 汉堡（`aria-controls="mobile-menu"`、`aria-expanded`）。
- 展开：`<Portal className="top-14" id="mobile-menu">` + `<PortalBackdrop />`，内部公开项 +（登录）个人项 + 登录/退出。
- 每个 `Link` 的 `onClick={() => setOpen(false)}`。
- `Portal` 负责 `body { overflow: hidden }` 与滚动条占位补偿（既有实现，不改）。

### 头像菜单

- `NavUser` 保留头像/下拉骨架与 `completeLogout` 流程。
- 导航项改为 `memberNavItems.map(...)`，`onSelect={() => navigate(item.path)}`；补 `AI 助手`（`/agent`）。
- 保留「退出登录」（`variant="destructive"`）。

## 数据流

```
router(injected: location.pathname)
  → ClientLayout(user from useAuthStore)
    → AppShell(path, user)
      → AppPathContext / ShellUserContext
        ├─ AppHeader: useAppPath() → isNavItemActive 高亮；useShellUser() → 登录按钮 or NavUser
        │    └─ MobileNav: useShellUser() → 是否渲染个人项
        └─ Outlet 页面
```

## 关键文件与改动

| 文件 | 动作 |
|---|---|
| `components/app-shared.tsx` | 数据结构扁平化，删面包屑标题表 |
| `components/app-shell.tsx` | 去 `SidebarProvider`/`SidebarInset`/`AppSidebar`，改布局栈 |
| `components/app-header.tsx` | 按 header-1 重写（`Logo` + 公开项 + 搜索 + 主题 + 头像 + 汉堡 + `useScroll`） |
| `components/mobile-nav.tsx` | 重写为真实导航抽屉（复用 `Portal`，链接点击关闭） |
| `components/nav-user.tsx` | 导航项改用 `memberNavItems`，补 `AI 助手` |
| `components/header.tsx` | 删除（脚手架 `Header` + 占位 `navLinks`） |
| `components/app-sidebar.tsx` / `nav-group.tsx` | 删除 |
| `components/app-breadcrumbs.tsx` / `custom-sidebar-trigger.tsx` | 删除 |
| `components/ui/sidebar.tsx` / `ui/sheet.tsx` / `ui/kbd.tsx` / `hooks/use-mobile.ts` | 删除（仅侧栏链引用） |
| `components/portal.tsx` / `hooks/use-scroll.ts` | 保留，成为活代码 |
| `pages/Agent.tsx` | 根补内边距，修正硬编码高度 |
| `pages/SubjectDetail.tsx` | 复核 `md:top-20` |
| `src/test/shell.guards.test.tsx` | 断言改为顶栏/导航；个人项需交互后断言 |
| `directory-structure.md` | 更新未接线脚手架段 + client 外壳描述 |

## 权衡

- **宽度**：去外壳 `max-w-80rem` 后，`max-w-[1400px]` 页面从「有效 1280px」变为「有效 1400px」。这是期望的（当前是被外壳压窄的意外），代价是视觉变宽。若需保守，可给顶栏内层与页面统一取 1400px（本设计顶栏内层即为 `max-w-[1400px]`，与页面一致）。
- **双内边距**：现状外壳 `p-4 md:p-6` × 页面 `p-6`。改为外壳不提供内边距后消除。
- **`Agent` 页依赖外壳**：唯一不自带容器的页面，需显式补 `p-4 md:p-6`。
- **删除 primitive**：`ui/sidebar.tsx` 是 700+ 行废弃件；删除与 `quality-guidelines.md`「未接线文件不得进构建产物」一致。admin 副本独立，不受影响。

## 兼容性与回滚

- 无 API/类型契约变更，纯用户端展示层。回滚 = `git revert` 单个提交。
- 无数据迁移、无部署配置变更。

## 非目标

- 不改 `admin`。
- 不改 `packages/shared`。
- 不新增页面或路由。
- 不为本次改动新增 ADR（顶栏 vs 侧栏属可逆的展示层选择，不满足 ADR 门槛）。
