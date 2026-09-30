# Design：admin 迁移到 Tailwind + shadcn/ui

> 需求与验收标准见 `prd.md`。本文只记录技术设计。

## 决策记录（用户已确认）

| # | 决策 | 选择 |
|---|---|---|
| D1 | 应用外壳 | 用 `@efferd/app-shell-5` 替换 `AdminLayout`，**保留 7 个菜单项**（不残留 AppShell 的 demo 导航） |
| D2 | 迁移范围 | admin 全部界面：外壳 + 8 个页面 |
| D3 | shared 的 AntD 耦合 | **拆分 AuthGate**：逻辑入驻 shared，外壳由各 app 渲染；shared 移除 antd |
| D4 | 看板数据映射 | dashboard-5 的 **9 个槽位全部重映射**到业务指标 |
| D5 | 暗色模式 | **支持**，启用主题切换，与 shared `useThemeStore` 对齐 |

## 架构与边界

### 目标依赖拓扑

```
admin (shadcn/ui 体系)
├── tailwindcss@4 + @tailwindcss/vite     ← CSS-first 配置，无 tailwind.config.js
├── radix-ui / lucide-react / cva / clsx / tailwind-merge
├── recharts                              ← 取代 echarts
├── next-themes                           ← 由 app-shell-5 引入
└── @animetracker/shared                  ← 迁移后不再携带 antd UI

shared (UI 无关)
├── api / types / store / coordinator     ← 不变
├── useAuthStatus()                       ← 新增：headless 登录态
└── SubjectCard                           ← 改为渲染无关

client (不变)
└── 自带 AntD 外壳（ClientAuthShell） + od-* 样式
```

### 关键边界：shared 必须 UI 无关

admin 要彻底移除 antd，但 `packages/shared/src/index.ts` 是 **barrel 文件**。若其中任何 `export { X } from './y'` 运行时依赖 antd，打包器就会把 antd 拖进 admin 产物，即使 admin 从不使用 X。

**可静态消除的（无需改动）**：
- `theme.ts` — `import type { ThemeConfig } from 'antd'`，仅类型，编译后消失。
- `index.ts` 的 `export { antdTheme, ... }` — 树摇可消除。

**必须重写的运行时耦合**：

| 文件 | 当前问题 | 处置 |
|---|---|---|
| `components/AuthGate.tsx` | `import { Button, Result, Spin, Typography, theme } from 'antd'` | shared 只保留 `useAuthStatus()`；外壳下沉到各 app |
| `components/SubjectCard.tsx` | `import { theme } from 'antd'`（`theme.useToken()`） | 改用本地常量/内联样式，成为渲染无关组件 |

> `SubjectCard` 的 schema 同时依赖 `react-router-dom`（未在 shared 声明），属规范已记录的存量债务；本次顺手修正声明，不改其行为。client 仍在 import 它，因此本次只做「去 antd」而不迁移到 shadcn。

### AuthGate 拆分契约

shared 新增：

```ts
// packages/shared/src/hooks/useAuthStatus.ts
export type AuthStatus = 'checking' | 'authenticated' | 'unauthenticated' | 'retryable-error';
export function useAuthStatus(): {
  status: AuthStatus;
  retry: () => void;   // 内部调用 retryBootstrapAuth()
};
```

各 app 自行渲染外壳：

| App | 外壳 | `checking` | `retryable-error` | 其他 |
|---|---|---|---|---|
| client | 现有 `AuthGate.tsx` 就地改造（保留 `auth-gate` / `od-*` 类名与 DOM 结构） | Spin + 标题 | Result + 重新连接按钮 | 直接渲染 children |
| admin | 新增 shadcn 版（Card + Skeleton/Spinner + Button） | Skeleton 面板 | 警告 Card + 重试 Button | 直接渲染 children |

**兼容性约束**：client 的 `main.tsx:26` 传入 `className="od-auth-gate"`，且现有 `auth-gate__panel`、`auth-gate__brand`、`auth-gate__result` 等类名与 `role="status"` / `aria-live` / `aria-busy` / `role="alert"` 语义**必须原样保留**，仅替换 antd 组件为等价元素，避免 client 视觉与可访问性回归。

> `admin/main.tsx` 当前无 `className`，无此约束。

## 数据流与契约

### 看板槽位映射（D4）

保留 dashboard-5 的 9 槽位网格与视觉语法，逐个换为业务指标。**网格跨度沿用 block 原值**：

| # | block 槽位（原语义） | 跨度 | 重映射为 | 数据源 |
|---|---|---|---|---|
| 1 | `VisitorsChart` 面积图 | `md:col-span-2 lg:col-span-3` | 新增趋势（用户/收藏/登录 三线） | `trends(days)` |
| 2 | `OnlineNow` | `lg:col-span-1` | 今日新增用户（含今日新增收藏/登录） | `overview()` |
| 3 | `TopPages` 表 | `md:col-span-2` | 热门番剧榜 | `hot(10)` |
| 4 | `TopCountries` | — | 季度分布 | `subjectStats().seasons` |
| 5 | `TrafficSourcesChart` | — | 收藏类型分布 | `collectionStats().types` |
| 6 | `AudienceMix` | — | 评分分布（`ratings`，复用为 1–10 档） | `collectionStats().ratings` |
| 7 | `BrowserShare` | — | 评分散点分布 | `subjectStats().scoreCounts` |
| 8 | `TopReferrers` | — | 导入状态分布 | `subjectStats().importStatuses` |
| 9 | `WebVitals` | `lg:col-span-4` | 导入总数 / 成功 / 失败 | `subjectStats().importStat` + `overview().importCount` |

`days` 的 7/30/90 选择器沿用现有 `Segmented` 语义，改用 shadcn 的 ToggleGroup/Button group 实现。

### Query 组织

沿用 `Dashboard.tsx` 现有 queryKey，**不改动**，避免影响其他消费方：

```
['dash','overview'] ['dash','trends',days] ['dash','cs'] ['dash','ss'] ['dash','hot']
```

每张卡片独立消费对应 query 的 `isLoading` / `error` / 空数组，实现 AC5。

### 全部页面所需 shadcn 组件清单

| 页面 | 需要的 shadcn 组件 |
|---|---|
| AppShell | sidebar, dropdown-menu, avatar, breadcrumb, input-group, kbd, separator, tooltip, button, + `@efferd/logo`, `@efferd/use-keypress` |
| Dashboard | card, chart, table, badge, button, tooltip, + `@efferd/formater`, delta, indicator, share-bar-list |
| AdminLogin | card, input, label, button, field/form |
| Subjects | table, dialog, input, select, textarea, button, badge, + 分页, 确认对话框 |
| Users | table, switch, select, + 确认对话框, badge |
| Import | radio-group, select, input, button, table, badge |
| Logs | card, select, input, table, button, badge, + 日期区段选择 |
| AgentConfig | card, input, textarea, button, list, + 确认对话框 |
| AgentChat | 复刻 `AgentChat.tsx` 的 Sider+Content 为 shadcn 布局, scroll-area, textarea, button, + 思考过程折叠 |

**无直接对应的交互**：AntD 的 `message` 全局提示与 `Popconfirm` 确认框，改用 sonner（toast）+ shadcn `alert-dialog`。`message.error/success` 的调用点（`AdminLogin`、`Subjects`、`Users`、`Import`、`AgentConfig`、`guards.tsx`）需逐一替换，且**保持提示文案不变**。

### `guards.tsx` 的 render 阶段副作用

现状在 render 中调用 `message.error('无管理权限')`，规范已列为债务。迁移到 shadcn 时顺带修正为 effect 或导航副作用，并**补测试**（现有 `guards.test.tsx` 通过 `vi.mock('antd')` 断言该调用，mock 目标需同步改为新的 toast 模块）。

## 兼容性与迁移

### Preflight 与 antd reset 的冲突窗口

admin 在迁移期间会**短暂共存** antd 与 Tailwind。Tailwind 的 Preflight 会重置 `button`/`h1`-`h6`/`ul` 等基础样式，可能影响尚未迁移的 antd 页面。

**方案**：按 D2 全量迁移，使共存窗口尽可能短；迁移顺序上**先建地基 + 外壳 + Dashboard，再逐页替换**，每页替换后立即核对无回归。若某页出现 preflight 冲突，优先在该页内用 shadcn 等价实现消除依赖，而不是回退全局样式。

### `@/` 与 `@shared` 别名共存

`admin/vite.config.mts:7` 与 `admin/tsconfig.json` 现有 `@shared` → `../packages/shared/src`。需新增 `@` → `./src`，二者互不影响。注意 `@shared` 是 `@` 的**前缀匹配歧义**风险：`@/` 与 `@shared` 分属不同键，Vite 按最长前缀精确匹配，无冲突，但需在实现后实测解析。

### 依赖去留

- 移除：`antd`、`echarts`、`echarts-for-react`、`@ant-design/icons`（已确认 admin 未使用 icons）。
- 新增：`tailwindcss`、`@tailwindcss/vite`、`recharts`、`next-themes`、`class-variance-authority`、`clsx`、`tailwind-merge`、`lucide-react`、`sonner`、`radix-ui` 及 block 所需 registry 组件对应包。
- `admin/src/components/charts.tsx` 随 echarts 一并删除，改由 dashboard-5 的 recharts 组件承担。
- **`shared/package.json` 的 `antd` 依赖**：`theme.ts` 仍需 `import type { ThemeConfig } from 'antd'`。因 client 依赖 `antdTheme`，须保留 antd 作为 shared 的依赖（或改为 devDependency + 类型内联）。**决策**：保留在 `dependencies`，并在 spec 中注明「shared 仅在类型层引用 antd，运行时不产出 antd 代码」；若后续 client 也迁移，再彻底移除。

### 暗色模式落地（D5）

- shadcn 的 `.dark` 变量策略 + `next-themes` 的 `class` 属性。
- 与 shared `useThemeStore` / `resolveMode` 对齐：admin 的 `main.tsx` 不再用 `ConfigProvider theme={antdTheme}` 单主题，改由 `next-themes` 驱动，并复用 shared 的 mode 解析规则，避免出现两套互相打架的主题状态。
- **同步修订 spec**：`component-guidelines.md:33`「admin 当前只使用 shared light theme；不要假设已支持暗色」随之失效。

### 代码风格

block 原始代码为**制表符 + 双引号**，仓库为 **2 空格 + 单引号**。落地后统一改写为仓库风格（仓库无 prettier/eslint，靠人工对齐现有文件）。

## 权衡

| 方案 | 取舍 |
|---|---|
| 保留 `AdminLayout`，仅迁移页面 | 改动更小，但外壳与页面风格割裂，且不满足用户「界面所有都要替换」的要求 |
| 直接删 shared 的 `antdTheme` | 会连带破坏 client（`client/main.tsx:25` 依赖 `antdThemeDark` 等），超出本次范围 |
| 一次性大爆炸迁移 | 共存窗口最短，但单次改动面过大、难以定位回归；采用「地基 → 外壳 → 逐页」渐进式 |
| 全量替换而非局部共存 | 终态干净（无 antd），但迁移期间需要每页核对 |

## 风险与回滚

| 风险 | 缓解 | 回滚点 |
|---|---|---|
| Preflight 破坏未迁移页面样式 | 渐进式迁移 + 每页视觉核对 | 每页各自一次提交 |
| `@efferd` block 自带 demo 数据遗漏 | AC4 逐项核对，grep demo 常量（`94`、`555`、`/pricing`、`Chrome`） | Dashboard 单独一次提交 |
| AuthGate 拆分导致 client 登录态回归 | 保留全部 `od-*` 类名与 ARIA 语义；client 侧不改视觉 | AuthGate 拆分单独一次提交 |
| `guards.test.tsx` 因 mock 目标变更失败 | 同步更新 mock，保留原有断言意图 | — |
| app-shell-5 引入 `next-themes` 与现有主题 store 冲突 | 先对齐 mode 解析，再接入切换器 | 主题部分单独提交 |
| 分包体积劣化 | `manualChunks` 白名单需补 `recharts` / radix 规则；跑 `npm run build` 对比 | — |

## 需同步修订的 spec

`.trellis/spec/frontend/`：

1. `component-guidelines.md:29` — 「UI 基础使用 Ant Design」→ 需区分 admin（shadcn/ui + Tailwind）与 client（AntD + `od-*`）。
2. `component-guidelines.md:33` — admin 暗色支持说明失效。
3. `component-guidelines.md:14` — shared 运行时依赖声明规则，随 shared 去 antd 一并更新。
4. `directory-structure.md` / `hook-guidelines.md` — admin 页面与路由清单、新增 `@/` 别名约定。
5. `quality-guidelines.md:32` — 分包说明随 charts 去留更新。

> 另注意：`.trellis/spec/frontend/` 文件为混合 CRLF/LF，Edit 会整体改写为 LF 并放大 diff —— 修订 spec 时优先用 Write 重写或接受该 diff 并在提交信息中说明。
