# admin 看板：dashboard-5 接入真实业务数据

> 父任务：`09-21-admin-tailwind-shadcn-dashboard`。本子任务覆盖父任务 `implement.md` 的阶段 D，是父任务最初请求的直接交付物。

## Goal

在已迁移的 Admin AppShell 中落地 `@efferd/dashboard-5` 的 9 槽位看板，并将所有内容映射为 `adminDashboardApi` 的真实番剧运营数据，不保留 traffic-analysis demo 数据。

用户价值：管理后台看板以现代、响应式的卡片网格呈现真实业务指标，且数据延迟、失败或为空时仍能清楚反馈状态。

## Dependencies

- `09-21-admin-ui-foundation` 已于 2026-09-22 完成并归档（`task.json` status=completed）；Tailwind/shadcn、`@efferd` registry、toast 与 `@/` 别名均已具备。
- `09-21-admin-app-shell` 已于 2026-09-22 完成并归档（commit `9a91355d`）；Dashboard 将渲染在现有 AppShell 内。
- 本子任务是父任务 Dashboard 阶段的实现目标；`09-21-admin-pages-migration` 仍处 planning，且不属于本子任务范围。

## Requirements

- R1：添加 `@efferd/dashboard-5` 所需组件与依赖闭包，包括 `@efferd/formater`、`delta`、`indicator`、`share-bar-list`；保留 block 的 9 槽位网格与视觉语法，按仓库规范整理导入代码风格。
- R2：9 个槽位全部展示以下真实业务内容，不展示原 demo 的流量分析指标：

  | # | 槽位 | 业务内容 | 数据源 |
  |---|---|---|---|
  | 1 | `VisitorsChart` | 7/30/90 天用户新增、收藏新增、登录次数趋势 | `trends(days)` |
  | 2 | `OnlineNow` | 今日新增用户、今日新增收藏、今日登录 | `overview()` |
  | 3 | `TopPages` | 收藏数最高的番剧 Top 10 | `hot(10)` |
  | 4 | `TopCountries` | 番剧播出季度分布 | `subjectStats().seasons` |
  | 5 | `TrafficSourcesChart` | 用户收藏类型分布 | `collectionStats().types` |
  | 6 | `AudienceMix` | 用户收藏评分分布 | `collectionStats().ratings` |
  | 7 | `BrowserShare` | 番剧自身评分分布 | `subjectStats().scoreCounts` |
  | 8 | `TopReferrers` | 番剧导入状态分布 | `subjectStats().importStatuses` |
  | 9 | `WebVitals` | 导入记录总数、成功数、失败数 | `overview().importCount` + `subjectStats().importStat` |

- R3：趋势周期选择器保留 7/30/90 天选项，使用 shadcn 控件，并驱动对应 `trends(days)` 请求及图表刷新。
- R4：每个卡片独立呈现 loading、请求失败和空数据状态；复用接口的卡片各自显示状态，不允许因某一查询失败而让其他查询数据一并消失。多个接口组合的导入卡片按其全部依赖共同呈现状态。
- R5：不改变数据层与现有 queryKey：`['dash','overview']`、`['dash','trends',days]`、`['dash','cs']`、`['dash','ss']`、`['dash','hot']`。
- R6：移除 block 中全部 demo 数据与文案。实现后检查数字 `94`、`555` 及 `Chrome`、`/pricing`、`Returning visitors`、`Core Web Vitals`、`Organic search` 等示例内容；检查应针对看板/block 文件，避免误报无关业务代码或依赖文件。
- R7：删除仅被旧 Dashboard 使用的 `admin/src/components/charts.tsx`，并确认全仓库没有残留引用。
- R8：`admin/src/pages/Dashboard.tsx` 不再导入 AntD 或使用 `Card`、`Statistic`、`Row`、`Col`、`Segmented`。

## Data semantics

- 收藏评分 `collectionStats().ratings` 是用户收藏记录的评分档（后端仅统计 `rate > 0`）；番剧评分 `subjectStats().scoreCounts` 是条目自身的分数按 `FLOOR(score)` 聚合（后端仅统计 `score > 0`）。卡片标题和辅助文案必须区分二者，不能都让用户误解为同一评分总体。
- `subjectStats().importStatuses` 的 `importStatus`：`0` 为待导入、`1` 为已导入；该统计是番剧条目状态分布，不是导入任务状态。
- `subjectStats().importStat` 统计导入记录总数、成功数、失败数；总数卡片采用 `overview().importCount`，成功/失败采用 `importStat.importSucceeded` / `importFailed`。数值为零是有效统计值，不当作请求错误。

## Acceptance Criteria

- [x] AC1：看板渲染在现有 AppShell 内；`Dashboard.tsx` 不导入 `antd`，不使用 AntD 布局/统计组件。
      → `frontend/admin/src/router.tsx:18-20` 经 `AdminLayout`/`Outlet` 渲染；`grep -n antd Dashboard.tsx` 零命中。
- [x] AC2：9 个槽位均展示其对应真实接口字段；实现或测试证据逐项说明字段到展示内容的映射。
      → 映射表见下方「字段映射证据」；`Dashboard.test.tsx` 首条用例逐槽断言。
- [x] AC3：限定在 Dashboard/block 实现文件核对，R6 所列 demo 数字与文案均不存在，且无其他 demo 统计数据残留。
      → `grep -rniE "chrome|/pricing|returning visitors|core web vitals|organic search"` 与 `\b(94|555)\b` 在 `components/dashboard/`、`Dashboard.tsx`、`delta.tsx`、`share-bar-list.tsx` 零命中（2026-09-29）。
- [x] AC4：逐卡验证 loading / 空数据 / 请求失败三态：每态都有可访问、明确的文本或占位；无空白卡片、无未捕获异常。导入卡片需覆盖其两个数据源的组合状态。
      → `card-state.tsx` 统一三态（`role=status/alert`、`aria-busy`）；测试覆盖「各卡独立加载」「单查询失败只影响自身卡片」「空数组显示空态」「导入卡片 overview 失败即失败」。
- [x] AC5：实际切换 7/30/90 天分别请求对应周期，所选周期的趋势数据更新；有自动化测试或可重复的浏览器证据。
      → 测试断言默认 30 天、切换 7/90 触发 `trends(days)` 且卡片描述随周期更新（`dataKey` 重渲染）。未做真实浏览器联调，标记为 API mock 级证据。
- [x] AC6：`admin/src/components/charts.tsx` 已删除，仓库无引用。
      → 文件已删除；`grep -rn "components/charts" frontend/`（排除 node_modules）零命中。
- [x] AC7：在 `frontend` 目录执行 `npm run typecheck`、`npm test -w admin`、`npm run build` 均通过。
      → typecheck 通过；admin 3 文件 16 用例通过；build 通过（Dashboard chunk 364.59 kB / gzip 109.87 kB，随 recharts 引入）。
- [x] AC8：收藏评分、番剧自身评分、番剧导入状态与导入记录统计的标签/辅助文案符合 Data semantics，不混淆指标口径。
      → 槽位 6「用户收藏评分分布」（辅助文案注明仅统计已评分记录）、槽位 7「番剧自身评分分布」（辅助文案注明与用户收藏评分为不同口径）、槽位 8「番剧导入状态分布」、槽位 9「导入记录」。

## 字段映射证据（AC2）

| # | 槽位组件 | 接口字段 | 展示内容 |
|---|---|---|---|
| 1 | `visitors-chart.tsx` | `trends(days)`: `date/newUsers/newCollections/logins` | 三序列面积图，周期由 7/30/90 按钮驱动 |
| 2 | `online-now.tsx` | `overview`: `todayNewUsers/todayNewCollections/todayLogins` | 今日运营三项统计 |
| 3 | `top-pages.tsx` | `hot(10)`: `id/nameCn ?? name/collectionCount` | 热门番剧 Top 10，key 用 `id` |
| 4 | `top-countries.tsx` | `subjectStats().seasons`: `seasonKey/count` | 播出季度分布表 |
| 5 | `traffic-sources-chart.tsx` | `collectionStats().types`: `type/count` | 收藏类型分布（未知类型保留原值） |
| 6 | `audience-mix.tsx` | `collectionStats().ratings`: `rate/count` | 用户收藏评分分布 |
| 7 | `browser-share.tsx` | `subjectStats().scoreCounts`: `rate/count` | 番剧自身评分分布 |
| 8 | `top-referrers.tsx` | `subjectStats().importStatuses`: `importStatus/count` | 番剧导入状态分布 |
| 9 | `web-vitals.tsx` | `overview().importCount` + `subjectStats().importStat.importSucceeded/importFailed` | 导入记录总数/成功/失败 |

## Out of Scope

- 迁移其余 admin 页面（`09-21-admin-pages-migration` 负责）。
- 从 `admin/package.json` 移除 AntD 或 ECharts 依赖（由后续页面迁移与清理任务处理）。本任务仅删除旧 Dashboard 专用的 `charts.tsx`。
- 修改后端接口、shared 类型或 queryKey；新增接口没有提供的指标。
- 改变 dashboard-5 网格布局之外的 AppShell、主题或导航行为。

## Key Decision

- 继承父任务 D4：9 个槽位全部重映射到番剧业务指标，保留 dashboard-5 的网格布局；业务标签及数据字段以本 PRD 为准，具体渲染与查询状态结构见 `design.md`。

## Risks

| 风险 | 缓解 |
|---|---|
| registry block 遗留 demo 数字/文案 | AC3 针对 Dashboard/block 文件扫描，并审查所有静态展示值与文案 |
| 收藏评分、番剧评分或两种导入状态统计被混为一谈 | 按 Data semantics 命名卡片，并以接口字段映射与测试核对 |
| 多卡片共享 query，状态处理被误做成整页状态 | 每张卡片独立渲染自己的 query 状态；组合数据卡片显式处理依赖集合 |
| 删除 ECharts wrapper 影响其他消费者 | 删除前搜索全仓引用；AC6 验证零残留 |

