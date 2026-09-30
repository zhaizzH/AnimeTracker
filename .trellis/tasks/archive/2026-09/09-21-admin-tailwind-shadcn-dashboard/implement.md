# Implement：admin 迁移到 Tailwind + shadcn/ui

> 需求见 `prd.md`，技术设计见 `design.md`。本文是可执行的顺序清单。

## 执行归属（本任务为父任务，不下沉实现）

阶段 A–H 由 4 个子任务分别承担，**各子任务的 `prd.md` 为准**；本文保留为父任务的全局执行视图与集成审查依据。

| 子任务 | 阶段 | 起点条件 |
|---|---|---|
| `09-21-admin-ui-foundation` | A + B | 无 —— 起点 |
| `09-21-admin-app-shell` | C | 需 foundation 完成 |
| `09-21-admin-dashboard-block` | D | 需 foundation + app-shell 完成 |
| `09-21-admin-pages-migration` | E + F + G | 需 foundation + app-shell 完成；负责收尾 |

**集成审查（父任务自身的工作）**：全部子任务完成后，由父任务统一执行：
- 阶段 H 的**全量**门禁（`typecheck` / `test` / `build`）。
- AC1–AC8 的完整核对，确认跨子任务的验收项（尤其 AC7）在合并后仍成立。
- 阶段 F 与 G 的最终确认：若 `admin-pages-migration` 与 `admin-dashboard-block` 对 `admin/package.json` 的依赖区产生冲突，在此解决。

## 执行顺序总览

按「地基 → shared 解耦 → 外壳 → 看板 → 其余页面 → 清理 → 规范 → 门禁」推进，目的是**把 antd 与 Tailwind 的共存窗口压到最短**，且每一步都独立可验证、可回滚。

| 阶段 | 交付物 | 独立验证 |
|---|---|---|
| A | Tailwind + shadcn 地基 | admin 能构建，现有页面**零视觉变化** |
| B | shared 去 antd（AuthGate 拆分） | client 测试通过，client 视觉无回归 |
| C | app-shell-5 外壳替换 AdminLayout | 7 个菜单可导航、高亮正确、退出登录可用 |
| D | Dashboard-5 + 真实数据 | AC3/AC4/AC5 逐项核对 |
| E | 其余 7 页迁移 | 逐页行为对照 |
| F | 依赖清理 | antd/echarts 不再进产物 |
| G | spec 修订 | 与实现一致 |
| H | 全量门禁 | typecheck / test / build |

---

## A. 地基

- [x] A1：安装 `tailwindcss`、`@tailwindcss/vite`。
- [x] A2：`admin/vite.config.mts` 加入 `tailwindcss()` 插件与 `@` → `./src` 别名；**保留** 现有 `@shared` → `../packages/shared/src`。
- [x] A3：`admin/tsconfig.json` 的 `paths` 补 `@/*`，保留 `@shared`。
- [x] A4：创建 `admin/components.json`，注册命名空间：
      `"registries": { "@efferd": "https://efferd.com/r/{style}/{name}.json" }`
- [x] A5：创建 shadcn 基础 CSS 变量文件并在 `main.tsx` 引入；`@import "tailwindcss"` + `@custom-variant dark`；同时准备 `.dark` 变量集（D5）。
- [x] A6：安装 shadcn 基础组件：`badge` `button` `card` `chart` `table` `tooltip` `input` `label` `select` `dialog` `alert-dialog` `switch` `radio-group` `textarea` `separator` `dropdown-menu` `avatar` `breadcrumb` `sidebar` `input-group` `kbd` `scroll-area`。
- [x] A7：安装 `recharts`、`class-variance-authority`、`clsx`、`tailwind-merge`、`lucide-react`、`sonner`、`next-themes`。
- [x] A8：接入 sonner `<Toaster />`，建立与 AntD `message` 等价的调用封装（文案保持不变）。
- [x] A9：**验证点** — `npm run typecheck` / `npm run build -w admin` 均通过；7 个页面视觉等价已实测确认。
      **实测结论：调整引入顺序无效**。antd `reset.css` 仅 3.6KB，`grep` 确认其**不含** h1–h6 / ul / ol 规则，因此没有任何东西能挡住 preflight。受控对照（同页注入无 class 探针）：client（antd，无 Tailwind）h1=32px / h3=18.72px / ul=disc·40px（UA 默认完好）；admin（antd + Tailwind）h1=h3=16px / ul=none·0（被 preflight 清零）。
      实际采用**就地补偿**：`charts.tsx` 的 `<h3>` 加 `text-[1.17em]`、`Dashboard.tsx` 的 `<ol>` 加 `list-decimal pl-10`。
      补偿完备性已扫 7 页确认：所有 `<h*>` 均为图表标题且带补偿类；唯一 `<ol>` 为看板 Top10 且已补偿；其余 `<ul>` 全为 antd 自管组件（menu / pagination / list-item-action）。
      比值核对：client h3 = 18.72px = 1.17×16（基准 16px），admin h3 = 16.38px = 1.17×14（基准 14px），**比值 1.17 双侧一致**，视觉等价成立。

## B. shared 去 antd

- [x] B1：新增 `packages/shared/src/hooks/useAuthStatus.ts`，导出 `useAuthStatus()` → `{ status, retry }`，复用现有 `useAuthStore` 分支与 `retryBootstrapAuth`。
- [x] B2：改造 `packages/shared/src/components/AuthGate.tsx` 为 client 专用外壳（或移入 `client/src/`），**必须保留**：`auth-gate` / `auth-gate--checking` / `auth-gate--error` / `auth-gate__panel` / `auth-gate__brand` / `auth-gate__result` 类名，以及 `role="status"` / `aria-live="polite"` / `aria-busy="true"` / `role="alert"` / `aria-live="assertive"`。
- [x] B3：`packages/shared/src/components/SubjectCard.tsx` 去掉 `theme.useToken()`。
      ⚠️ **实现偏差更正**：最初的写法是硬编码亮色字面量，实测构成**暗色回归** —— client 支持暗色（`main.tsx:25` 按 `resolveMode` 切 `antdThemeDark`），而 `useToken()` 原本会跟随 ConfigProvider 解析。硬编码后暗色下实测：body 背景 `rgb(26,29,23)`、卡片 `rgba(35,39,31,.55)` 均已转暗，但标题仍是 `rgb(35,38,31)`（近黑）、副文字 `rgb(110,114,102)`、封面占位 `rgb(236,233,225)`（亮色）—— 近黑字压暗底，不可读。
      改为引用 client 已有的 `--od-*` 变量并保留字面量兜底：`--od-line` / `--od-ink-3` / `--od-ink` / `--od-ink-2`（与 `antdTheme` / `antdThemeDark` 逐值对齐）。
      复测（显式控制 `animetracker-theme`）：light 标题 `rgb(35,38,31)` = `#23261F` ✓ / dark `rgb(237,235,228)` = `#EDEBE4` ✓；副文字 dark `rgb(180,184,174)` = `#B4B8AE` ✓；封面占位 dark `rgb(46,51,42)` = `#2E332A` ✓。
- [x] B4：修正 `packages/shared/package.json`：移除 `react-markdown`（源码未使用），声明 `react-router-dom`（`SubjectCard` 实际使用）。
- [x] B5：`shared/src/index.ts` 调整导出；确认 admin 侧不再经 barrel 引入任何 antd 运行时代码。
- [x] B6：**验证点** — shared 测试 6/6 通过、client 测试 7/7 通过、`npm run typecheck` 通过。
      client 登录态三态已用 Playwright 实测（localhost:5173，拦截/延迟 `/api/client/auth/refresh` 触发各态）：
      - `checking`：`.auth-gate.auth-gate--checking.od-auth-gate` + `role="status"` + `aria-live="polite"` + `aria-busy="true"` + `.auth-gate__spinner` 存在，无 retry 按钮，文案「正在恢复登录状态…」。
      - `retryable-error`：`.auth-gate.auth-gate--error.od-auth-gate` + `role="alert"` + `aria-live="assertive"` + `.auth-gate__retry` 存在，文案「暂时无法确认登录状态…重新连接」。
      - 正常态：`auth-gate` 节点移除、children 直接渲染（已登录用户 test1，首页轮播与今日放送列表完整）。
      三态的 `auth-gate*` / `od-auth-gate` 类名与 ARIA 语义**全部原样保留**。
- [x] B7：grep 确认 `packages/shared/src` 下无 `from 'antd'` 的**运行时**引用（`theme.ts` 的 `import type` 允许保留）。

## C. 应用外壳

- [ ] C1：`shadcn add @efferd/app-shell-5`（含 `@efferd/logo`、`@efferd/use-keypress`）。
- [ ] C2：重写 `app-sidebar` 的导航为 7 个现有菜单项：`/admin/dashboard` 看板、`/admin/subjects` 番剧管理、`/admin/users` 用户管理、`/admin/import` 导入管理、`/admin/logs` 日志审计、`/admin/agent-config` Agent 配置、`/admin/agent-chat` Agent 对话。**删除 block 自带 demo 导航**。
- [ ] C3：`nav-user` 接入 `useAuthStore` 的 `user.username`，退出登录复用现有 `completeLogout(authApi.logout)`，**保留 `isLoggingOut` 防重复提交语义**，成功跳 `/admin/login`，失败提示"退出失败，请重试"。
- [ ] C4：接入 `theme-switcher`，与 shared `useThemeStore` / `resolveMode` 对齐（D5）。
- [ ] C5：`admin/src/layouts/AdminLayout.tsx` 替换为 AppShell 实现；`admin/src/main.tsx` 去掉 `ConfigProvider` + `antdTheme` + `antd/dist/reset.css`。
- [ ] C6：**验证点** — 7 个菜单项逐一点击可导航、当前路由高亮正确、用户名显示正确、退出登录成功与失败两条路径都试到。

## D. Dashboard-5

- [ ] D1：`shadcn add @efferd/dashboard-5`（含 `@efferd/formater`、`delta`、`indicator`、`share-bar-list`）。
- [ ] D2：按 `design.md` 的槽位映射表，逐个替换 9 张卡片的 demo 数据为 `adminDashboardApi` 真实数据。
- [ ] D3：`days` 选择器（7/30/90）改为 shadcn 实现，驱动 `trends(days)`。
- [ ] D4：每张卡片独立处理 `isLoading` / `error` / 空数组三态。
- [ ] D5：删除 block 残留 demo 常量；grep 核对 `94`、`555`、`Chrome`、`/pricing`、`Returning visitors`、`Core Web Vitals` 等已不存在。
- [ ] D6：删除 `admin/src/components/charts.tsx`（echarts 封装，仅为旧 Dashboard 服务）。
- [ ] D7：**验证点** — AC3 / AC4 / AC5 逐项核对，需要真实后端或明确标注的 mock 证据，不能仅凭断言。

## E. 其余 7 页迁移

逐页替换，**每页一次提交**，便于定位回归。每页迁完立即核对行为等价。

- [ ] E1：`AdminLogin.tsx` — Card + Input + Label + Button；保留角色非 ADMIN 的 `该账号无管理权限` 分支与 `publishSessionAvailable()`、`location.state.from` 回跳。
- [ ] E2：`Subjects.tsx` — Table + Dialog 表单 + 筛选控件；保留全部筛选维度（q / tag 多选 / scoreMin / scoreMax / year / weekday）、分页、`invalidateQueries(['admin-subjects'])`、编辑与删除确认。
- [ ] E3：`Users.tsx` — Table + Switch + Select；**保留 `pendingUserIds` 防重复切换语义**与禁用用户的确认对话框文案（"禁用后，该用户将在所有设备上立即退出。确定继续吗？"）。
- [ ] E4：`Import.tsx` — Radio group + Select + Table；保留 `st` 的 3000ms 轮询与 `totalLogs > 0` 时失效 `import-records` 的 effect。
- [ ] E5：`Logs.tsx` — Card + Select + Input + Table + 日期区段；保留 4 个统计卡与 action 列点击回填筛选。
- [ ] E6：`AgentConfig.tsx` — Card + List + Textarea + 表单；保留提示词加载/保存/重置、失效 `agent-config`、`staleTime: Infinity`。
- [ ] E7：`AgentChat.tsx` — 复刻 Sider + Content 布局；保留思考过程折叠（流式展开、完成后自动收起）、`aria-live`、滚动到底、流式中禁用输入、停止/发送切换。
- [ ] E8：`guards.tsx` — 替换 `message.error`，**并顺带修正 render 阶段副作用**（规范已记债务），补测试。
- [ ] E9：`admin/src/guards.test.tsx` — mock 目标从 `antd` 改为新的 toast 模块，保留原有断言意图。
- [ ] E10：**验证点** — 每页迁移前后行为对照证据；E8 附带新测试。

## F. 依赖清理

- [ ] F1：grep 确认 `admin/src` 下无 `from 'antd'` 残留。
- [ ] F2：从 `admin/package.json` 移除 `antd`、`echarts`、`echarts-for-react`（`@ant-design/icons` 在 admin 的 devDependencies，且未被使用，一并移除）。
- [ ] F3：`admin/vite.config.mts` 的 `manualChunks` 白名单补 `recharts` 与 radix 系规则；调整 `chunkSizeWarningLimit` 或给出说明。
- [ ] F4：`admin/vitest.config.mts` 检查是否需要新增别名/环境配置。
- [ ] F5：**验证点** — `npm run build -w admin`，确认产物中不含 antd/echarts chunk，体积无显著劣化。

## G. Spec 修订

- [ ] G1：`component-guidelines.md:29` — 区分 admin（shadcn/ui + Tailwind）与 client（AntD + `od-*`）。
- [ ] G2：`component-guidelines.md:33` — 更新 admin 暗色支持说明。
- [ ] G3：`component-guidelines.md:14` — 更新 shared 运行时依赖规则。
- [ ] G4：`directory-structure.md` / `hook-guidelines.md` — 更新 admin 页面/路由清单与 `@/` 别名约定。
- [ ] G5：`quality-guidelines.md:32` — 更新分包说明。
- [ ] G6：`index.md` 若有 admin 技术栈描述，一并更新。
      ⚠️ 这些文件为混合 CRLF/LF，Edit 会整体改写为 LF 放大 diff —— 优先 Write 重写，或在提交信息中说明。

## H. 质量门禁

```bash
cd frontend
npm run typecheck     # CI 强制
npm test              # 受影响 workspace（admin / shared）
npm run build         # 路由、依赖、构建配置均有变更 → 必须跑
```

- [ ] H1：`npm run typecheck` 通过。
- [ ] H2：`npm test -w admin` 与 `npm test -w @animetracker/shared` 通过。
- [ ] H3：`npm run build` 成功，分包体积无明显劣化。
- [ ] H4：AC1–AC8 逐条给出证据并勾选。

---

## 风险点与回滚

| 阶段 | 风险 | 回滚 |
|---|---|---|
| A | preflight 破坏现有 7 页样式 | 调整 Tailwind 引入顺序；本阶段单独提交便于回退 |
| B | AuthGate 拆分致 client 登录态回归 | 保留全部 `od-*` 类名与 ARIA；单独提交 |
| C | AppShell 文档/按键/主题机制带入不必要耦合 | 外壳单独提交 |
| D | demo 数据遗漏 | D5 grep 校验 + AC4 证据 |
| E | 逐页行为不等价（尤其 Users 防重复、Import 轮询、AgentChat 流式） | 每页一次提交，逐页回退 |
| F | 移除 antd 后仍有隐式引用 | grep 校验 + build 必须成功 |

## start 前的检查

- [ ] `prd.md` / `design.md` / `implement.md` 均已评审。
- [ ] `implement.jsonl` / `check.jsonl` 已填入真实 spec 条目（非占位）。
- [ ] `trellis-before-dev` 在进入 Phase 2 前运行。
