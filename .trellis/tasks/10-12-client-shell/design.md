# 设计：client 外壳与路由

总体设计见父任务 `design.md` §2.3；此处写本子任务的落地细节。

## 成分归属

`@efferd/app-shell-2` 是 `registry:block`，10 个文件、无路由、无数据层，导航是 demo 数据。落地后按用途重新归属：

| 模板文件 | 处理 |
|---|---|
| `app-shell.tsx` | 作为 `ClientLayout` 的骨架（`SidebarProvider` + `SidebarInset`） |
| `app-sidebar.tsx` | 改写导航为真实三项 + 登录后入口 |
| `app-header.tsx` | 保留头部（触发按钮 + 面包屑 + 右侧动作） |
| `app-breadcrumbs.tsx` | 路径 → 中文标签映射 |
| `nav-group.tsx` / `nav-user.tsx` | 保留；`nav-user` 接 `completeLogout(authApi.logout)` |
| `dashboard-skeleton.tsx` | 删除（非看板） |
| `latest-change.tsx` | 删除（非看板） |
| `custom-sidebar-trigger/radix.tsx` | 保留（⌘b 快捷键提示） |
| `app-shared.tsx` | 类型 `SidebarNavItem` / `SidebarNavGroup` 复用于导航配置 |

## 契约

- **路由契约不变**：`RequireAuth` 未认证 → `/login` + `state.from`；`PublicOnly` 已认证 → `/`。重建 `guards.tsx` 保持这两个语义（读 `useAuthStore(s => s.status)`）。
- **Suspense fallback**：沿用「骨架屏 + 接近最终宽度」原则（父 spec `component-guidelines.md:16` 要求 fallback 接近最终内容宽度），用 shadcn `Skeleton` 替代旧的 antd `Spin`。
- **导航配置**：`SidebarNavItem` 支持 `isActive`，由 `useLocation().pathname` 计算，替代旧的 antd Menu `selectedKeys`。

## 取舍

| 取舍 | 选择 | 理由 |
|---|---|---|
| 外壳是否留在 `layouts/` | 留在 `layouts/ClientLayout.tsx` | 与 spec 的「布局壳放 src/layouts」一致，router 引用不变 |
| 模板 Kbd 快捷键是否保留 | 保留 | 附带能力，无成本 |
| 面包屑 | 保留并按路径映射 | 侧栏外壳下比顶部导航更需要位置提示 |

## 回滚

- 外壳为独立文件；回滚只需还原 `layouts/`、`router.tsx`、`guards.tsx`。
- 依赖子任务 2 的配置层；若子任务 2 回滚，本子任务需一并回滚。
