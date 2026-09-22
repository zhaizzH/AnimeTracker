# admin 迁移到 Tailwind + shadcn 并落地 dashboard-5

## Goal

让 `frontend/admin` 具备 Tailwind + shadcn/ui 地基，并把管理后台的**全部界面**（应用外壳 + 7 个页面）从 Ant Design 迁移到 shadcn/ui；看板页落地 Efferd 的 `@efferd/dashboard-5` 并接入 `adminDashboardApi` 的真实业务数据。

用户价值：管理后台整体获得一套现代、响应式、可组合的 UI 体系与统一的应用外壳，并保留按需引入更多 shadcn block 的能力。

> **范围变更记录**：初始请求为 `npx shadcn@latest add @efferd/dashboard-5`（单页）。澄清后用户选择「admin 界面所有都要替换,重构」，范围扩大为 **admin 全量 UI 重构**。

## Background（已确认事实 · 均有仓库证据）

### 当前 admin 技术栈

- 两个前端 workspace 都是 **Ant Design ^5 + 自研 CSS token**，没有任何 Tailwind / shadcn：
  - `frontend/admin/package.json`：`antd ^5`、`echarts ^6.1.0`、`echarts-for-react ^3.0.6`、`react ^18`、`react-router-dom ^7`、`zustand ^4`。
  - `frontend/client/package.json` 同样为 antd 栈。
- **不存在** `components.json`、`tailwind.config.*`、`postcss.config.*`、`@/components/ui/*`，也未安装 `class-variance-authority` / `tailwind-merge` / `clsx` / `radix-ui`。
- `frontend/package.json` 是 npm workspaces（`packages/*`, `client`, `admin`），`frontend/node_modules` 为提升后的共享依赖。
- `admin/vite.config.mts:7` 只配置了 `@shared` 别名，**没有 `@/` 别名**；block 大量使用 `@/components/...`、`@/lib/utils`、`@/lib/formater`。
- `admin/tsconfig.json` 的 `paths` 同样只有 `@shared/*`（同 client）。
- `admin/src/main.tsx` 引入 `antd/dist/reset.css` + shared `antdTheme` + `ConfigProvider`。
- `admin/src/index.html`（`src` 外为 `admin/index.html`）无 `class="dark"` 约定；样式规范明确「admin 当前只使用 shared light theme；不要假设已支持暗色」。

### dashboard-5 block 的真实构成（已拉取 `https://efferd.com/r/dashboard-5.json` 验证）

`type: registry:block`，**12 个文件**：

```
registry/blocks/dashboard/5/  audience-mix, browser-share, dashboard,
                              online-now, share-bar-list, top-countries,
                              top-pages, top-referrers,
                              traffic-sources-chart, visitors-chart, web-vitals
registry/blocks/dashboard/    delta.tsx
```

- `dependencies`: 无声明；实际代码 import `recharts`（admin 当前用 echarts）。
- `registryDependencies`: `["badge","button","card","chart","table","tooltip","@efferd/app-shell-5","@efferd/formater"]`。
- 缺失的本地依赖（内容不在本 block 内，需另行获取）：`@/components/indicator`、`@/lib/formater`、`@/lib/utils`。`online-now.tsx` 里写作 `@/components/../../components/indicator`（等价于 `@/components/indicator`）。

`@efferd/app-shell-5`（已拉取验证）：9 个文件，`dependencies: ["next-themes"]`，`registryDependencies: ["@efferd/use-keypress","avatar","breadcrumb","button","dropdown-menu","input-group","kbd","separator","sidebar","tooltip","@efferd/logo"]`。它是一个**完整的应用外壳**（侧边栏 + 顶栏 + 搜索 + 主题切换 + 用户菜单）。

引入该依赖树意味着 admin 内将同时存在两套 UI 体系（AntD 与 shadcn/Radix）与两个图表库（echarts 与 recharts）。

### 目标页面的真实数据源（可直接复用，无需改后端）

- `packages/shared/src/api/admin/dashboard.ts`：`overview()`、`trends(days)`、`collectionStats()`、`subjectStats()`、`hot(limit)`，经 `@shared` 命名空间 `adminDashboardApi` 导出（`packages/shared/src/index.ts:29`）。
- 类型见 `packages/shared/src/types/index.ts:23-27`：
  - `DashboardOverview`：userCount / subjectCount / collectionCount / episodeCount / importCount / todayNewUsers / todayNewCollections / todayLogins。
  - `TrendPointVO[]`：`{ date, newUsers, newCollections, logins }`。
  - `CollectionStatsVO`：`types[]`、`ratings[]`。
  - `SubjectStatsVO`：`seasons[]`、`importStatuses[]`、`importStat`、`scoreCounts[]`。
  - `HotItemVO[]`：`{ id, name, nameCn, image, collectionCount }`。
- `admin/src/pages/Dashboard.tsx` 现已消费以上全部 5 个接口，用 AntD `Card`/`Statistic`/`Row`/`Col`/`Segmented` 渲染 6 张统计卡与趋势/分布/热榜区块，图表走 `admin/src/components/charts.tsx` 的 echarts 封装。

**语义缺口**：dashboard-5 的卡片是流量分析语义（Audience mix / Browsers / Top pages / Top countries / Top referrers / Traffic sources / Core Web Vitals / Online now），与番剧业务数据（收藏类型分布、评分分布、季度分布、导入状态、热榜）**无法一一对应**。

### 项目规范约束（`.trellis/spec/frontend/`）

- `component-guidelines.md`：「UI 基础使用 Ant Design 与 shared 主题 token」；「admin 当前只使用 shared light theme；不要假设已支持暗色」；组件不得依赖消费应用「碰巧」安装的包 —— 装 Tailwind/shadcn 后**必须同步修订该规范**。
- `quality-guidelines.md` / `index.md`：质量门禁命令为 `cd frontend && npm run typecheck` / `npm test` / `npm run build`。

### 已知技术风险（需在 design.md 中给出方案）

- **Tailwind Preflight 与 AntD `reset.css` 冲突**：二者都做全局基础重置，直接共存可能破坏现有 6 个 admin 页面的 AntD 样式。
- **shadcn CLI 会改写入口**：`init` 可能重写 `admin/src/index.html`、`main.tsx`、`vite.config.mts`、`tsconfig.json`。
- **block 代码风格与仓库不一致**：block 使用制表符缩进 + 双引号，仓库为 2 空格 + 单引号。
- **`next-themes` 与现有主题机制**：admin 走 shared `antdTheme`（light-only），shadcn 组件的 `dark:` 变体需要一个 class 策略。
- **`@/` 别名**：需要在 vite + tsconfig 双侧新增，且不能影响 `@shared`。
- **构建 chunk 策略**：`admin/vite.config.mts:15-21` 是白名单式 `manualChunks`，recharts 不会被自动分 chunk。

## Requirements

- R1：让 `frontend/admin` 具备可用的 Tailwind + shadcn/ui 地基：依赖（tailwindcss、class-variance-authority、tailwind-merge、clsx、radix-ui 等）、`@/` 别名（vite + tsconfig 双侧）、Tailwind 配置与 CSS 变量主题、与 `antd/dist/reset.css` 共存的样式策略、`@efferd` registry 命名空间注册。
- R2：用 `@efferd/app-shell-5` 重写应用外壳，替换 `admin/src/layouts/AdminLayout.tsx`；保留现有 7 个菜单项（看板/番剧管理/用户管理/导入管理/日志审计/Agent 配置/Agent 对话）、当前路由高亮、登录用户名展示与退出登录流程（含 `isLoggingOut` 防重复提交语义）。
- R3：迁移全部 admin 页面到 shadcn/ui，替换其 AntD 实现，功能等价：`AdminLogin.tsx`(31) / `Dashboard.tsx`(98) / `Subjects.tsx`(65) / `Users.tsx`(71) / `Import.tsx`(38) / `Logs.tsx`(31) / `AgentConfig.tsx`(58) / `AgentChat.tsx`(82)，共 8 个页面文件、584 行（含 layout/components/guards）。
- R4：看板页落地 `@efferd/dashboard-5` 的布局与组件，并把卡片/图表接入 `adminDashboardApi` 真实数据（`@tanstack/react-query` 组织 queryKey，遵循 `hook-guidelines.md`），显式处理 loading / empty / error 状态。
- R5：处理 `packages/shared` 中的 AntD 耦合（`components/AuthGate.tsx`、`theme.ts`、`components/SubjectCard.tsx`），使 shared 不再依赖 antd 的**运行时** API。采用「拆分 AuthGate」：逻辑入驻 shared（`useAuthStatus()`），外壳由各 app 自行渲染；client 保留现有 `od-*` 外壳与 ARIA 语义不变。详见 `design.md`。

- R5b：支持暗色模式（推翻原「admin light-only」约定），启用 app-shell-5 的主题切换器并与 shared `useThemeStore` 对齐。
- R6：处置 admin 现有的 `antd` / `echarts` / `echarts-for-react` 依赖，以及 `admin/src/components/charts.tsx`（echarts 封装，51 行，仅被 Dashboard 使用）。
- R7：同步修订 `.trellis/spec/frontend/` 中被本次改动推翻的规范条目（UI 基础、暗色支持、shared 依赖声明、admin 页面与路由清单）。
- R8：质量门禁通过：`npm run typecheck`、受影响 workspace 的 `npm test`、`npm run build`。

## Acceptance Criteria

- [ ] AC1：应用外壳由 `@efferd/app-shell-5` 实现；7 个菜单项可导航、当前路由高亮正确、顶栏显示登录用户名、退出登录成功跳转 `/admin/login`，防重复提交语义与现状一致。
- [ ] AC2：8 个 admin 页面（含 `AdminLogin`）均不再直接 `import ... from 'antd'`，功能与迁移前等价（每个页面需给出迁移前后的行为对照证据）。
- [ ] AC3：`Dashboard.tsx` 使用 dashboard-5 的布局与 shadcn 组件渲染，不再依赖 AntD `Card`/`Statistic` 作为看板骨架。
- [ ] AC4：看板上的每一处数值/图表都来自 `adminDashboardApi` 的真实响应，不存在硬编码 demo 数据（`94`、`555`、`Chrome 58%`、`/pricing` 等）。
- [ ] AC5：加载中、空数据、请求失败三种状态都有明确文本或占位，不出现空白卡片或未捕获异常。
- [ ] AC6：`admin/package.json` 中 `antd` / `echarts` / `echarts-for-react` 的去留已明确落地；若移除，`charts.tsx` 一并处置，且 `npm run build` 不再打包它们。
- [ ] AC7：`cd frontend && npm run typecheck` 通过；`npm test`（受影响 workspace）通过；`npm run build` 成功且分包体积无明显劣化。
- [ ] AC8：`.trellis/spec/frontend/` 已更新，且与最终实现一致。

## Out of Scope

- 迁移 `frontend/client`（用户端）到 Tailwind/shadcn。
- 后端接口、`docs/spec/openapi.yaml`、shared 类型契约的改动（现有接口已足够，不改后端）。
- 改变 admin 各页面的业务功能或交互语义（本次是 UI 迁移重构，不是功能重设计）。
- 移除 `shared/package.json` 的 `antd` 依赖本身：`theme.ts` 仍需 `import type { ThemeConfig } from 'antd'`，且 client 依赖 `antdTheme`。本次只保证 shared 不再有 antd 的**运行时**引用。

## 任务地图（父任务持有需求与验收，不直接实现）

本父任务不下沉实现；实现由 4 个子任务承担。子任务间的**顺序依赖**写在各自 `prd.md` 的 `## Dependencies` 段，不靠树位置隐含表达。

| 子任务 | 覆盖阶段 | 拥有验收项 | 依赖 |
|---|---|---|---|
| `09-21-admin-ui-foundation` | A 地基 + B shared 去 antd | AC7（部分）、AC8（部分） | 无 —— **起点** |
| `09-21-admin-app-shell` | C 应用外壳 | AC1、AC7 | 需 foundation 完成 |
| `09-21-admin-dashboard-block` | D 看板 | AC3、AC4、AC5 | 需 foundation + app-shell 完成 |
| `09-21-admin-pages-migration` | E 其余页面 + F 清理 + G spec | AC2、AC6、AC7、AC8 | 需 foundation + app-shell 完成；**收尾** |

**跨子任务验收责任**：AC7（质量门禁）在每个子任务各自范围内成立（各自改动后必须 typecheck/test/build 通过）；最终的整体门禁与 AC1–AC8 全量核对由父任务在全部子任务完成后统一做集成审查。

## Key Decisions

| # | 决策 | 选择 |
|---|---|---|
| D1 | 应用外壳 | 用 `@efferd/app-shell-5` 替换 `AdminLayout`，保留现有 7 个菜单项与退出登录语义 |
| D2 | 迁移范围 | admin 全部界面：外壳 + 8 个页面 |
| D3 | shared 的 AntD 耦合 | 拆分 AuthGate：逻辑共享，外壳各 app 自渲；shared 移除 antd 运行时依赖 |
| D4 | 看板数据映射 | dashboard-5 的 9 个槽位全部重映射到番剧业务指标 |
| D5 | 暗色模式 | 支持，启用主题切换 |

技术方案、槽位映射表、风险与回滚见 `design.md`；执行顺序见 `implement.md`。

## Open Questions

（无 —— 阻塞项已全部解决。D1–D5 的落地细节见 `design.md`。）
