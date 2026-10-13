# 前端目录结构

## 工作区

```text
frontend/
├── client/                    # 用户端 React，Vite :5173（shadcn/ui + Tailwind v4，外壳 components/app-shell.tsx，顶栏 + 移动抽屉、无侧栏）
│   └── src/{pages,components,layouts,test}
├── admin/                     # 管理端 React，Vite :5174（shadcn/ui + Tailwind v4，外壳 layouts/AdminLayout.tsx）
│   └── src/{pages,components,components/ui,layouts,lib}
└── packages/shared/           # @animetracker/shared
    └── src/{api,auth,components,hooks,store,types}
```

根 `frontend/package.json` 使用 npm workspaces；client/admin 通过 `file:../packages/shared` 依赖 shared。

## 代码归属

- 路由页面放应用的 `src/pages`，页面只在对应 `router.tsx` 注册。
- 跨页面但只属于一个应用的 UI 放该应用 `src/components`。
- 跨 client/admin 的 API、鉴权、主题、SSE、类型和通用组件放 `packages/shared/src`。
- 布局壳放 `src/layouts`，认证/角色重定向放应用 `guards.tsx`。
- 测试靠近所有者：shared 与 admin 用同目录 `*.test.ts(x)`（admin 为 `src/guards.test.tsx`、`src/layouts/*.test.tsx`、`src/pages/*.test.tsx`、`src/components/auth/*.test.tsx`），client 集中用 `src/test` 的现状均可沿用。

## 导入规则

- 应用统一从 `@shared` 公共入口导入（Vite alias + tsconfig paths 指向 shared 源码）；`@animetracker/shared` 包名入口当前无人使用，不穿透 shared 私有文件。
- `@` 别名指向各应用自己的 `src`（admin 已在 `vite.config.mts` 与 tsconfig 中配置）。Vite 的别名匹配要求 importee 等于键或以 `<key>/` 开头，因此 `@` 不会误匹配 `@shared`。
- shared 的 API 在 `src/index.ts` 以 `authApi / subjectsApi / adminUsersApi` 等命名空间导出。
- client/admin 不互相相对导入。
- 新共享导出先检查命名冲突；同名动作保持命名空间，不改成扁平 re-export。
- 资源和全局样式保留在所有者应用，除非两个应用确实共用同一视觉契约。

## admin 页面与路由

- 页面：`Dashboard`、`Users`、`Subjects`、`Import`、`Logs`、`AgentConfig`、`AgentChat`、`NotFound`。登录页是 `components/auth/auth-page.tsx`（默认导出 `AdminLogin`），**不是** `pages/` 下的路由页面。
- 除登录页 `components/auth/auth-page.tsx` 静态导入外，其余页面在 `router.tsx` 中 `lazy` + Suspense。
- 登录页是独立路由页，不经任何 shell 包裹，直接渲染；其余页共享 `AdminLayout`；`NotFound`（`path: '*'`）在 `AdminLayout` 之外，避免未匹配路径套上外壳。
- **admin 路由不带 `/admin` 前缀**（`/login`、`/dashboard`……），页面以站点根为基路径。管理端生产部署在独立端口 `:8081` 的站点根（`docs/deploy/nginx/animetracker.conf`），本地开发为 `:5174`；给路由加 `/admin` 前缀会让本地与生产的可用路径不一致，违反 [ADR 0018](../adr/0018-admin-on-separate-port-not-subpath.md)「不得改用用户端子路径部署」的约束。当前路由表是这条 ADR 的**落地**：此前代码曾带 `/admin` 前缀，现已对齐 ADR。

## client 认证与 404

- 认证路由（`/login`、`/register`、`/verify-email`、`/forgot-password`、`/reset-password`）由 `PublicOnly` 包裹，并**位于 `ClientLayout` 之外**，整屏渲染、无侧栏/页头。
- `/login` 与 `/register` 渲染**同一个** `AuthPage`（`components/auth/auth-page.tsx`）：注册不是独立页面，而是同一面板内的模式切换；`/register` 仅 `Navigate` 重定向到 `/login`。
- client 的 404 是**顶层** `path: '*'`（`pages/NotFound.tsx`），同样在 `ClientLayout` 之外，未登录访问也不会被重定向到 `/login`。旧实现（`ClientLayout` 内的 `Navigate to="/"`）已删除。

## 两端页脚

- client 与 admin 各持一份本地页脚 `components/footer.tsx`（同骨架，Logo 目标各异），由 `ClientLayout` / `AdminLayout` 在内容区尾部渲染，使短内容页页脚贴底、长内容页位于文档末尾。骨架源自 efferd `footer-1`，但已改为手工落地（不跑 `shadcn add`），并**删除上游 nav 段**（与两端各自的顶栏/侧栏导航重复）与署名外链、`href="#"` 死链。页脚只保留「Logo + GitHub 图标位」一行与版权行。
- 页脚**默认随布局外壳显示**；404 与认证页位于布局之外，**天然不显示**；全高对话页（client `/agent`、admin `/agent-chat`）在布局内以 `FOOTERLESS_PATHS` 显式排除。
- GitHub 图标 `components/icons/github-icon.tsx` 与 admin 的 `components/logo.tsx` 均为**各端本地副本**（lucide-react 已不含品牌图标；admin 暂无自有图标，暂用 client 同款）。按 [ADR 0021](../adr/0021-shared-contract-visuals-vs-app-local-decorations.md)，装饰件各端自持、允许逐字节重复，不下沉 `packages/shared`。

## 未接线脚手架

- `components/portal.tsx`、`hooks/use-scroll.ts`、`components/mobile-nav.tsx` 原为 efferd registry 收录的营销页头脚手架，现已接线进入 client 外壳：`client/src/components/app-shell.tsx` 只渲染「吸顶顶栏 + 内容区」，无侧栏；`components/app-header.tsx` 用 `useScroll` 驱动滚动背景态，移动端复用 `Portal`/`PortalBackdrop` 全屏抽屉。`components/header.tsx`（脚手架 `Header` 与占位 `navLinks`）已删除，侧栏链（`app-sidebar`/`nav-group`/`app-breadcrumbs`/`custom-sidebar-trigger`/`ui/sidebar`/`ui/sheet`/`ui/kbd`/`hooks/use-mobile`）一并移除。
- 仓库允许存在其他未被引用的文件；目录规范只登记被引用的活代码（门禁见 [quality-guidelines.md](./quality-guidelines.md)）。

## 参考

- client 入口：`frontend/client/src/main.tsx`、`router.tsx`
- admin 入口：`frontend/admin/src/main.tsx`、`router.tsx`
- admin UI primitives：`frontend/admin/src/components/ui`
- client UI primitives：`frontend/client/src/components/ui`
- shared 出口：`frontend/packages/shared/src/index.ts`
