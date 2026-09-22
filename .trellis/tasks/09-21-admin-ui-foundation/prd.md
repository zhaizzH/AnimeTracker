# admin 地基：Tailwind + shadcn 接入与 shared 去 antd

> 父任务：`09-21-admin-tailwind-shadcn-dashboard`。本子任务覆盖其 `implement.md` 的**阶段 A + B**，是整条迁移链路的起点。

## Goal

让 `frontend/admin` 具备可用的 Tailwind + shadcn/ui 能力，并解除 `packages/shared` 对 antd 的**运行时**依赖，为后续替换应用外壳与全部页面扫清障碍。

用户价值：admin 获得 shadcn 组件能力，同时 shared 变成 UI 无关的包，使 admin 后续可以彻底移除 antd 而不被 shared 拖住。

## Dependencies

**无前置依赖 —— 本子任务是起点。** 后续子任务 `09-21-admin-app-shell`、`09-21-admin-dashboard-block`、`09-21-admin-pages-migration` 均依赖本子任务完成。

## Requirements

- R1：接入 Tailwind v4（`tailwindcss` + `@tailwindcss/vite`，CSS-first，无 `tailwind.config.js`）。
- R2：`admin/vite.config.mts` 新增 `tailwindcss()` 插件与 `@` → `./src` 别名；**保留**现有 `@shared` → `../packages/shared/src`。
- R3：`admin/tsconfig.json` 的 `paths` 新增 `@/*`，保留 `@shared`。
- R4：创建 `admin/components.json`，并在 `registries` 注册 `"@efferd": "https://efferd.com/r/{style}/{name}.json"`。
- R5：创建 shadcn 基础 CSS 变量文件（含 light 与 `.dark` 两套变量，为 D5 暗色做准备），`@import "tailwindcss"` + `@custom-variant dark`，并在 `main.tsx` 引入。
- R6：安装 shadcn 基础组件：`badge` `button` `card` `chart` `table` `tooltip` `input` `label` `select` `dialog` `alert-dialog` `switch` `radio-group` `textarea` `separator` `dropdown-menu` `avatar` `breadcrumb` `sidebar` `input-group` `kbd` `scroll-area`。
- R7：安装 `recharts`、`class-variance-authority`、`clsx`、`tailwind-merge`、`lucide-react`、`sonner`、`next-themes`。
- R8：接入 sonner `<Toaster />`，并建立与 AntD `message` 等价的调用封装（**文案保持一致**），供后续页面迁移与 `guards.tsx` 使用。
- R9：新增 `packages/shared/src/hooks/useAuthStatus.ts`，导出 `useAuthStatus()` → `{ status, retry }`，复用现有 `useAuthStore` 分支与 `retryBootstrapAuth`。
- R10：改造 `packages/shared/src/components/AuthGate.tsx`，去掉 antd 组件依赖，**必须原样保留**类名 `auth-gate` / `auth-gate--checking` / `auth-gate--error` / `auth-gate__panel` / `auth-gate__brand` / `auth-gate__result`，以及 `role="status"` / `aria-live="polite"` / `aria-busy="true"` / `role="alert"` / `aria-live="assertive"` 语义。
- R11：`packages/shared/src/components/SubjectCard.tsx` 去掉 `theme.useToken()`，改为组件内常量/内联样式，行为与视觉不变。
- R12：修正 `packages/shared/package.json`：移除源码未使用的 `react-markdown`，声明 `SubjectCard` 实际使用的 `react-router-dom`。
- R13：确认 admin 经 `@shared` barrel 引入时不会带入 antd 运行时代码（`theme.ts` 的 `import type` 可保留）。

## Acceptance Criteria

- [x] AC1：`cd frontend && npm run typecheck` 通过 —— shared / client / admin 三个 workspace 全部 `tsc` 无报错。
- [x] AC2：`npm test -w @animetracker/shared` 6/6 通过；`npm test -w client` 7/7 通过。
- [x] AC3：`npm run build` 三个 workspace 全部成功（client 8.43s / admin 9.83s，2367 modules）。
- [x] AC4：admin 7 个页面与 `AdminLayout` **视觉等价**，已实测确认。
      ⚠️ **更正**：本 AC 原文假设「preflight 未破坏 AntD 样式」，**实测证伪**。antd `reset.css` 仅 3.6KB 且不含 h1–h6 / ul / ol 规则，无法阻挡 preflight。受控对照（同页无 class 探针）：client（无 Tailwind）h1=32px / h3=18.72px / ul=disc·40px；admin（含 Tailwind）h1=h3=16px / ul=none·0。
      等价性由**就地补偿**达成，非「未破坏」：`charts.tsx` `<h3>` → `text-[1.17em]`；`Dashboard.tsx` `<ol>` → `list-decimal pl-10`。
      补偿完备性已扫 7 页：所有 `<h*>` 均为图表标题且带补偿类，唯一 `<ol>` 为 Top10 且已补偿，其余 `<ul>` 全为 antd 自管组件。比值核对：client 18.72 = 1.17×16 与 admin 16.38 = 1.17×14，比值一致。
- [x] AC5：client 登录态三态实测无回归，`od-*` 类名与 ARIA 语义原样保留。
      `checking` → `.auth-gate--checking.od-auth-gate` + `role=status` + `aria-live=polite` + `aria-busy=true` + `.auth-gate__spinner`，无 retry。
      `retryable-error` → `.auth-gate--error.od-auth-gate` + `role=alert` + `aria-live=assertive` + `.auth-gate__retry`。
      正常态 → gate 节点移除，children 直接渲染（已登录 test1，首页完整）。
      另补测出并修复一处暗色回归：`SubjectCard` 初版硬编码亮色 token，暗色下标题仍为近黑 `rgb(35,38,31)`（body 已转暗 `rgb(26,29,23)`），不可读。改引 `--od-*` 变量后复测通过，见 implement.md B3。
- [x] AC6：`grep -rn "from 'antd'" packages/shared/src` 仅命中 `theme.ts:1` 的 `import type { ThemeConfig } from 'antd'`（编译期消失）。其余 antd 字样均为中文注释，`index.ts` 的 `export { antdTheme }` 可树摇。
- [x] AC7：`@/` 与 `@shared` 双侧均正确解析，无歧义。24 个 shadcn ui 组件经 `@/lib/utils`、`@/components/ui/*` 解析成功，与 `@shared` 同处一次 typecheck + build 中通过 —— 最长前缀匹配行为已实测。
- [x] AC8：sonner `<Toaster>` 实测已挂载（`aria-label="Notifications alt+T"`），`toastSuccess` / `toastError` 封装文案由调用方原样传入，保证与 antd `message` 逐字一致。

## Out of Scope

- 替换 `AdminLayout`（属 `09-21-admin-app-shell`）。
- 迁移任何页面到 shadcn（属后续子任务）。
- 移除 `admin/package.json` 的 antd / echarts 依赖（属 `09-21-admin-pages-migration`，需等全部页面迁完）。
- 引入 `@efferd/app-shell-5` 或 `@efferd/dashboard-5`（属后续子任务）。
- 修改 `shared` 的 API / types / store 业务逻辑。

## Key Decisions（继承父任务）

- D3：拆分 AuthGate —— 逻辑共享，外壳各 app 自渲；shared 移除 antd 运行时依赖。
- D5：支持暗色 —— 本子任务需准备好 `.dark` 变量集，但切换器接入在 `admin-app-shell`。

## 技术要点

- `SubjectCard` 的 `react-router-dom` 依赖缺失是规范已记录的存量债务，本子任务顺带修正声明，不改行为。
- AuthGate 改造后 client 仍从 shared 导入；不得改变其对外 props 签名（`{ children, className }`）。
- Tailwind 与 `antd/dist/reset.css` 的加载顺序若导致 preflight 破坏既有样式，需调整引入顺序或将该阶段样式限定在 `@layer` 内。**实测决定，不预设结论。**

## 风险

| 风险 | 缓解 | 回滚 |
|---|---|---|
| preflight 破坏现有 7 页样式 | 本阶段单独提交；实测后调整引入顺序 | 单独 revert 本子任务 |
| AuthGate 改造致 client 登录态回归 | 保留全部 `od-*` 类名与 ARIA 语义 | 单独 revert |
| `@/` 与 `@shared` 别名歧义 | 双侧配置后实测解析 | — |
