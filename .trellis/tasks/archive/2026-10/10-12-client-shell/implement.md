# 实施：client 外壳与路由

## 1. 安装
- [x] `cd frontend/client && npx shadcn@latest add @efferd/app-shell-2`
- [x] 记录 CLI 实际落地路径 / target，按实际情况调整后续 import

## 2. 安装 shared primitive
- [x] 确认 `components/ui/*`（sidebar / dropdown-menu / breadcrumb / avatar / kbd / tooltip / button / separator）已落地，缺失则 `npx shadcn@latest add <name>`

## 3. 外壳
- [x] 建 `layouts/ClientLayout.tsx`：`SidebarProvider` + `AppSidebar` + `SidebarInset(AppHeader + Outlet)`
- [x] 改写 `components/app-sidebar.tsx` 导航为真实三项 + 登录后入口
- [x] 改写 `components/app-breadcrumbs.tsx` 为路径→中文映射
- [x] 删除 `components/dashboard-skeleton.tsx`、`components/latest-change.tsx`
- [x] `components/nav-user.tsx` 接 `useAuthStore` + `completeLogout(authApi.logout)` + `navigate('/login')`
- [x] 外壳内加主题切换（`useThemeStore`）

## 4. 路由与守卫
- [x] 重建 `guards.tsx`（`RequireAuth` / `PublicOnly`）
- [x] 重建 `router.tsx`：12 条路由 + `lazy` + `withLoading`（shadcn `Skeleton` fallback）
- [x] 路由页先以占位组件挂载（子任务 4 替换为真实页）
- [x] 挂载 `AgentChatProvider key={user?.id}` 与 `AIAssistantFloat`

## 5. 验证
- [x] 冒烟：侧栏导航跳转、未登录守卫重定向带 `state.from`、登录后回跳、`PublicOnly` 重定向
- [x] `npm run typecheck`

## 验证命令
```bash
cd frontend
npm run typecheck
npm run dev:client
```

## 回滚点
- 外壳文件与路由可整体还原；依赖子任务 2 的配置层。
