# 前端目录结构

## 工作区

```text
frontend/
├── client/                    # 用户端 React，Vite :5173（Ant Design + `od-*` 样式）
│   └── src/{pages,components,layouts,test}
├── admin/                     # 管理端 React，Vite :5174（shadcn/ui + Tailwind）
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
- 测试靠近所有者：shared 用同目录 `*.test.ts(x)`，client 集中用 `src/test` 的现状均可沿用。

## 导入规则

- 应用统一从 `@shared` 公共入口导入（Vite alias + tsconfig paths 指向 shared 源码）；`@animetracker/shared` 包名入口当前无人使用，不穿透 shared 私有文件。
- `@` 别名指向各应用自己的 `src`（admin 已在 `vite.config.mts` 与 tsconfig 中配置）。Vite 的别名匹配要求 importee 等于键或以 `<key>/` 开头，因此 `@` 不会误匹配 `@shared`。
- shared 的 API 在 `src/index.ts` 以 `authApi / subjectsApi / adminUsersApi` 等命名空间导出。
- client/admin 不互相相对导入。
- 新共享导出先检查命名冲突；同名动作保持命名空间，不改成扁平 re-export。
- 资源和全局样式保留在所有者应用，除非两个应用确实共用同一视觉契约。

## admin 页面与路由

- 页面：`Dashboard`、`Users`、`Subjects`、`Import`、`Logs`、`AgentConfig`、`AgentChat`、`AdminLogin`。
- 除 `AdminLogin` 静态导入外，其余页面在 `router.tsx` 中 `lazy` + Suspense。
- `AdminLogin` 用独立的 `AdminLoginShell` 布局；其余页共享 `AdminLayout`。

## 参考

- client 入口：`frontend/client/src/main.tsx`、`router.tsx`
- admin 入口：`frontend/admin/src/main.tsx`、`router.tsx`
- admin UI primitives：`frontend/admin/src/components/ui`
- shared 出口：`frontend/packages/shared/src/index.ts`
