# Implement: Admin App Shell Migration

## Preconditions

- [x] Foundation child task is complete and its Tailwind/shadcn registry setup is present.
- [x] The child PRD has been reviewed for scope, routes, logout semantics, and theme behavior.
- [x] `implement.jsonl` and `check.jsonl` contain real frontend spec entries.
- [x] Obtain explicit approval of the final planning summary before starting the task.
- [x] Run `trellis-before-dev` immediately before editing product code.

## Ordered checklist

### C1. Import the registry shell

- [x] Run the existing shadcn registry command for `@efferd/app-shell-5` from `frontend/admin`; the registry dependency/update step completed, while existing foundation component collisions were preserved.
- [x] Confirm shell imports resolve through the existing `@/` alias and do not overwrite unrelated foundation files.
- [x] Adapt the app-shell-specific navigation, user menu, theme switcher, and keypress utility locally to the repository's existing primitives and accessibility contract.

### C2. Compose the admin layout

- [x] Replace the Ant Design implementation in `frontend/admin/src/layouts/AdminLayout.tsx` with the app-shell composition and `Outlet`.
- [x] Remove demo navigation/content from the registry block.
- [x] Keep the existing `AdminLayout` export and router nesting unchanged.

### C3. Wire the seven routes

- [x] Define the seven route/label entries exactly as listed in `prd.md`.
- [x] Navigate without full page reloads.
- [x] Derive active state from the current pathname so query strings and refreshes preserve highlighting.
- [x] Verify every item is rendered with its existing child route and add route-navigation regression coverage.

### C4. Wire the user menu and logout

- [x] Render `useAuthStore().user?.username` in the user menu.
- [x] Reuse `completeLogout(authApi.logout)`.
- [x] Preserve `isLoggingOut`, the disabled pending control, `退出中…`, success navigation, and failure toast text.
- [x] Add focused tests for success, failure, and repeated clicks.

### C5. Wire the shared theme

- [x] Add the admin theme bridge using `useThemeStore` and `resolveMode`.
- [x] Apply/remove `.dark` and set `color-scheme` in an effect; handle system preference changes with cleanup.
- [x] Adapt the app-shell theme switcher to update the shared store and avoid an independent persisted `next-themes` preference.
- [x] Verify explicit light/dark selection and system mode/listener cleanup in regression tests; persisted state uses the existing shared store.

### C6. Remove the admin entry-point Ant Design provider

- [x] Remove `ConfigProvider`, `antdTheme`, and `antd/dist/reset.css` from `frontend/admin/src/main.tsx`.
- [x] Keep bootstrap auth, `AuthGate`, router, query provider, and `Toaster` behavior intact.
- [x] Leave page-level Ant Design dependencies in place for the sibling migration tasks.

### C7. Quality gate

- [x] Run `cd frontend && npm run typecheck`.
- [x] Run `cd frontend && npm test -w admin` — 2 files, 9 tests passed.
- [x] Run `cd frontend && npm run build` — client and admin builds passed.
- [x] Verify all seven navigation items, refresh/query highlighting, username, logout success/failure/pending states, and theme behavior through focused regression tests.
- [x] Run `git diff --check` and confirm no product files outside the app-shell scope changed.

## Risk points and rollback

| Risk | Check | Rollback point |
|---|---|---|
| Registry output overwrites foundation files | Review generated diff immediately after C1 | Restore only the generated shell files, preserving foundation changes |
| Theme state splits between shared store and registry code | Inspect storage and DOM class after each theme action | Revert the theme adapter, keep shell navigation/user menu |
| Removing reset CSS exposes page-specific transitional styling issues | Run admin build and browser smoke checks | Keep the entry-point cleanup in the shell commit and record page issues for migration child |
| Logout wiring triggers duplicate requests | Focused user-event test with delayed logout promise | Revert only user-menu wiring and retain static shell |

## Completion evidence

The task is ready to archive only when every PRD acceptance criterion is evidenced, the quality gate is green, and the implementation diff contains no page migration or dependency-cleanup work owned by sibling tasks.
