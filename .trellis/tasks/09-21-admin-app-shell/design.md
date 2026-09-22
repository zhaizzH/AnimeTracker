# Design: Admin App Shell Migration

## Scope

This child task implements stage C of `09-21-admin-tailwind-shadcn-dashboard`. It replaces the Ant Design layout used by `frontend/admin` with the `@efferd/app-shell-5` registry block while preserving the existing route, authentication, and logout contracts.

The implementation must remain isolated to the admin shell. Dashboard and page migrations remain owned by the sibling tasks.

## Architecture

### Registry integration

1. Add `@efferd/app-shell-5` through the existing `frontend/admin/components.json` registry.
2. Keep the generated primitives under `frontend/admin/src/components/ui` and place app-shell-specific components under `frontend/admin/src/components`.
3. Keep `frontend/admin/src/layouts/AdminLayout.tsx` as the composition boundary. It owns the `Outlet`, `SidebarProvider`/inset structure, and the app-shell-specific providers required by the registry block.
4. Remove the registry demo navigation and demo content. The shell may keep structural breadcrumb/search placeholders only when they do not display fabricated business data.

### Navigation contract

The navigation model is a typed constant owned by the admin shell:

| Path | Label |
|---|---|
| `/admin/dashboard` | 看板 |
| `/admin/subjects` | 番剧管理 |
| `/admin/users` | 用户管理 |
| `/admin/import` | 导入管理 |
| `/admin/logs` | 日志审计 |
| `/admin/agent-config` | Agent 配置 |
| `/admin/agent-chat` | Agent 对话 |

Each item navigates with `useNavigate` or a router-aware link. Active state is derived from `useLocation().pathname`, using exact path matching for the seven current child routes so query strings do not clear the highlight. The existing router nesting, `RequireAdmin` guard, lazy pages, and `Suspense` fallback remain unchanged.

### User menu and logout

The user-menu component reads `user.username` from `useAuthStore`. Logout remains an event-driven local state machine:

1. Ignore a click while `isLoggingOut` is true.
2. Set `isLoggingOut` before calling `completeLogout(authApi.logout)`.
3. On success, navigate to `/admin/login`.
4. On failure, call `toastError('退出失败，请重试')`.
5. Clear `isLoggingOut` in `finally`.

The button/menu item is disabled while the request is pending and shows `退出中…`, preserving the current duplicate-submit behavior. The implementation must not move logout into a render path or expose a second auth state source.

### Theme integration

`useThemeStore` remains the single persisted preference source. The shell adapts the registry theme-switcher UI to that store instead of allowing `next-themes` to persist a competing preference.

- `resolveMode(mode, followSystem)` determines the effective `light`/`dark` mode.
- A small admin theme bridge applies the effective mode to `document.documentElement.classList` and `color-scheme` inside an effect.
- When `followSystem` is enabled, the bridge listens for `prefers-color-scheme` changes and removes the listener on unmount.
- Explicit light/dark choices call `setMode`; the system choice calls `toggleFollowSystem` as needed.
- The `.dark` variables prepared by foundation remain the CSS contract.

`next-themes` may remain installed because it is part of the registry dependency graph, but it must not become a second persisted source of truth. If the downloaded registry component requires `ThemeProvider`, adapt the component to the shared-store bridge rather than enabling independent storage.

### Entry-point cleanup

`frontend/admin/src/main.tsx` keeps `QueryClientProvider`, bootstrap auth, the admin `AuthGate`, router, and `Toaster`. It removes:

- `ConfigProvider`
- `antdTheme`
- `antd/dist/reset.css`

No page-level Ant Design imports are removed in this child task; that belongs to the page-migration child. The temporary coexistence of Ant Design page code and Tailwind shell code is accepted and must be recorded if visual checks expose a page-specific issue.

## Compatibility and accessibility

- Preserve all seven existing route paths and labels.
- Preserve the current `AdminLayout` export consumed by `router.tsx`, unless a rename is required by the registry block; if renamed, update only the router import in this task.
- Keep the shell keyboard navigable, give icon-only controls accessible labels/tooltips, and keep logout disabled while pending.
- Do not introduce fake search results, latest-change data, or other demo values.
- Do not modify client layout, backend contracts, or page business behavior.

## Verification and rollback

The shell should be implemented in a small, independently revertible commit. Verification must cover route navigation/highlighting, username rendering, logout success/failure and duplicate-click protection, theme persistence/effective dark class, typecheck, admin tests, and the frontend build. If theme integration conflicts with the registry block, first revert the adapter portion while retaining the shell composition; do not change the shared theme store in this child task.
