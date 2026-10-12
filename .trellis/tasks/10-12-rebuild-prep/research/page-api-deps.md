# 各页 API 依赖核对表

来源：`grep` 扫描 `frontend/client/src` 与 `frontend/admin/src`（重建前）；shared 导出面见 `packages/shared/src/index.ts`。
用途：子任务 3/4/5 重接时的核对表——重建后每一项都必须有落点。

## shared 导出面（`packages/shared/src/index.ts`）

| 类别 | 导出 |
|---|---|
| 常量 | `SHARED_SENTINEL` |
| 类型 | `export * from './types'`、`export * from './format'` |
| store | `useAuthStore`、`useThemeStore`、`resolveMode` |
| 类型 | `AuthStatus`、`AuthState`、`ThemeMode` |
| 组件 | `SubjectCard`、`AuthGate` |
| HTTP/SSE | `export * from './api/http'`、`export * from './sse'` |
| 主题（**待删除**） | `antdTheme`、`antdThemeDark` |
| hooks | `useBootstrapAuth`、`useAuthStatus`、`useAgentChat` |
| 类型 | `ChatMsg`、`ToolStep` |
| 鉴权协调 | `bootstrapAuth`、`retryBootstrapAuth`、`refreshWithLock`、`publishSessionAvailable`、`publishSignedOut`、`completeLogout` |
| 命名空间 API | `authApi`、`subjectsApi`、`collectionsApi`、`tagsApi`、`filesApi`、`agentApi`、`adminAgentApi`、`adminImportApi`、`adminLogsApi`、`adminUsersApi`、`adminSubjectsApi`、`adminDashboardApi` |

## 用户端 client

| 文件 | 依赖的 shared | 备注 |
|---|---|---|
| `main.tsx` | `antdTheme`/`antdThemeDark`（**删除**）、`AuthGate`、`useBootstrapAuth`、`useThemeStore`、`resolveMode` | 重建后改为 ThemeBridge |
| `guards.tsx` | `useAuthStore` | `RequireAuth` / `PublicOnly` |
| `layouts/ClientLayout.tsx` | `useAuthStore`、`authApi`、`completeLogout`、`useThemeStore`、`resolveMode` | 外壳重建 |
| `components/AgentChat.tsx` | `agentApi`、`useAgentChat`、`ChatMsg` | `clientAgentApi` 是本地适配器（包 `agentApi` 的 listSessions/createSession/history/deleteSession/streamBody/health），**非 shared 缺口** |
| `components/CollectionActions.tsx` | `collectionsApi`、`useAuthStore` | 收藏/进度 CRUD |
| `components/ProgressPreviewModal.tsx` | `collectionsApi` | |
| `components/SubjectGrid.tsx` | （`SubjectCard` 来自 shared） | |
| `pages/Home.tsx` | `subjectsApi` | hero 轮播 |
| `pages/AnimeIndex.tsx` | `subjectsApi`、`tagsApi` | 多条件筛选 |
| `pages/Schedule.tsx` | `subjectsApi` | 放送日历 |
| `pages/SubjectDetail.tsx` | `subjectsApi` | 详情 + 剧集表 |
| `pages/MyCollections.tsx` | `collectionsApi` | Tabs + CRUD |
| `pages/Profile.tsx` | `authApi`、`filesApi`、`useAuthStore` | 三弹窗；改密后 `publishSignedOut` |
| `pages/Login.tsx` | `authApi`、`useAuthStore` | `setAuthenticated` + `publishSessionAvailable` |
| `pages/Register.tsx` | `authApi` | |
| `pages/VerifyEmail.tsx` | `authApi`、`useAuthStore` | |
| `pages/ForgotPassword.tsx` | `authApi` | |
| `pages/ResetPassword.tsx` | `authApi` | |
| `test/home.hero.test.tsx` | mock `subjectsApi`、`useBootstrapAuth`、`useThemeStore`、`resolveMode` | 锚点待重写 |
| `test/agent.float.test.tsx` | mock `authApi`、`completeLogout`、`useAgentChat`、`useAuthStore`、`useThemeStore`、`resolveMode` | 渲染真实 `<ClientLayout/>`，锚点待重写 |

## 管理端 admin

| 文件 | 依赖的 shared | 备注 |
|---|---|---|
| `main.tsx` | （待重建时确认 `useBootstrapAuth`） | |
| `guards.tsx` | （`useAuthStore`） | `RequireAdmin` |
| `layouts/AdminLayout.tsx` | `authApi`、`completeLogout` | |
| `components/theme-bridge.tsx` | `useThemeStore`、`resolveMode` | 移植到 client |
| `components/theme-switcher.tsx` | `useThemeStore` | |
| `components/nav-user.tsx` | `useAuthStore` | |
| `components/dashboard/*.tsx` | `adminDashboardApi` | visitors/traffic-sources/top-referrers/top-pages/top-countries/browser-share/audience-mix |
| `pages/Dashboard.tsx` | `adminDashboardApi` | |
| `pages/Subjects.tsx` | `adminSubjectsApi`、`subjectsApi`、`tagsApi` | |
| `pages/Users.tsx` | `adminUsersApi` | |
| `pages/Import.tsx` | `adminImportApi` | |
| `pages/Logs.tsx` | `adminLogsApi` | |
| `pages/AgentConfig.tsx` | `adminAgentApi` | |
| `pages/AgentChat.tsx` | `adminAgentApi`、`useAgentChat` | SSE |
| `pages/AdminLogin.tsx` | `authApi`、`useAuthStore` | |

## 核对结论

- `@shared` 引用点 62 处，全部落在上表；无一指向 shared 内部私有文件（均走公共入口）。
- 唯一需要在 shared 侧改动的导出是 `antdTheme`/`antdThemeDark`（消费方仅 `client/src/main.tsx`）。
- `clientAgentApi` 为 client 本地适配器，重建时需在 client 侧重写，不属于 shared 缺口。
