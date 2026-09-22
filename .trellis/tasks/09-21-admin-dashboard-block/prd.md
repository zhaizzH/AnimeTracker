# admin 看板：dashboard-5 接入真实业务数据

> 父任务：`09-21-admin-tailwind-shadcn-dashboard`。本子任务覆盖其 `implement.md` 的**阶段 D**，是父任务最初的请求来源。

## Goal

落地 `@efferd/dashboard-5`，把它的 9 个卡片槽位按设计映射表**全部重映射**到 `adminDashboardApi` 的真实业务数据，并清除全部 demo 常量。

用户价值：管理后台看板获得 dashboard-5 的现代布局与视觉语法，同时展示真实的番剧运营指标，而非流量分析示例数据。

## Dependencies

**前置依赖：`09-21-admin-ui-foundation` 与 `09-21-admin-app-shell` 均须完成。** 需要 shadcn 地基、`@efferd` 命名空间、sonner 封装，以及已替换为 AppShell 的外壳（看板渲染在 AppShell 内）。

**被依赖**：无。但本子任务是父任务原始请求的直接交付物，是集成审查的重点。

## Requirements

- R1：执行 `shadcn add @efferd/dashboard-5`，含 `@efferd/formater`、`delta`、`indicator`、`share-bar-list`。
- R2：按 `design.md` 的槽位映射表逐个替换 9 张卡片的 demo 数据为真实数据：

  | # | 槽位 | 跨度 | 重映射为 | 数据源 |
  |---|---|---|---|---|
  | 1 | `VisitorsChart` 面积图 | `md:col-span-2 lg:col-span-3` | 新增趋势（用户/收藏/登录 三线） | `trends(days)` |
  | 2 | `OnlineNow` | `lg:col-span-1` | 今日新增用户（含今日新增收藏/登录） | `overview()` |
  | 3 | `TopPages` 表 | `md:col-span-2` | 热门番剧榜 | `hot(10)` |
  | 4 | `TopCountries` | — | 季度分布 | `subjectStats().seasons` |
  | 5 | `TrafficSourcesChart` | — | 收藏类型分布 | `collectionStats().types` |
  | 6 | `AudienceMix` | — | 评分分布 | `collectionStats().ratings` |
  | 7 | `BrowserShare` | — | 评分散点分布 | `subjectStats().scoreCounts` |
  | 8 | `TopReferrers` | — | 导入状态分布 | `subjectStats().importStatuses` |
  | 9 | `WebVitals` | `lg:col-span-4` | 导入总数 / 成功 / 失败 | `subjectStats().importStat` + `overview().importCount` |

- R3：`days` 选择器（7/30/90）改用 shadcn 实现，驱动 `trends(days)`。
- R4：每张卡片**独立**处理 `isLoading` / `error` / 空数组三态。
- R5：沿用现有 queryKey，**不改动数据层契约**：`['dash','overview']` `['dash','trends',days]` `['dash','cs']` `['dash','ss']` `['dash','hot']`。
- R6：清除全部 demo 常量，`grep` 核对以下内容已不存在：`94`、`555`、`Chrome`、`/pricing`、`Returning visitors`、`Core Web Vitals`、`Organic search` 等。
- R7：删除 `admin/src/components/charts.tsx`（echarts 封装，仅为旧 Dashboard 服务）。
- R8：`admin/src/pages/Dashboard.tsx` 不再使用 AntD `Card`/`Statistic`/`Row`/`Col`/`Segmented`。
- R9：block 代码风格（制表符 + 双引号）统一改写为仓库风格（2 空格 + 单引号）。

## Acceptance Criteria

- [ ] AC1：看板渲染在 AppShell 内；`Dashboard.tsx` 不再 `import ... from 'antd'`。
- [ ] AC2：9 张卡片全部来自 `adminDashboardApi` 真实响应，**逐卡核对数据与接口字段的对应关系**并给出证据。
- [ ] AC3：`grep` 确认 R6 列出的 demo 常量已全部消失。
- [ ] AC4：每张卡片在 loading / 空数据 / 请求失败下均有明确文本或占位，无空白卡片、无未捕获异常。需逐卡给出三态证据。
- [ ] AC5：`days` 切换（7/30/90）实际触发 `trends` 重新请求且图表更新。
- [ ] AC6：`admin/src/components/charts.tsx` 已删除，且全仓库无残留引用。
- [ ] AC7：`cd frontend && npm run typecheck` 通过；`npm test -w admin` 通过；`npm run build` 成功。
- [ ] AC8：语义映射自洽 —— 例如「评分分布」用于 `ratings`（0–10 档）与 `scoreCounts` 时，两者的口径差异有明确注释，避免误读为同一指标。

## Out of Scope

- 迁移其余 7 个页面（属 `admin-pages-migration`）。
- 从 `admin/package.json` 移除 echarts 依赖（本子任务只删 `charts.tsx`；依赖移除属 `admin-pages-migration` 的清理阶段）。
- 修改后端接口或 shared 类型契约 —— 现有 `adminDashboardApi` 已足够。
- 新增看板指标（不发明接口没有的数据）。

## Key Decisions（继承父任务）

- D4：dashboard-5 的 9 个槽位**全部重映射**到番剧业务指标，保留 block 的槽位网格与视觉语法。

## 风险与注意事项

| 风险 | 缓解 |
|---|---|
| demo 数据遗漏 | AC3 的 grep 清单逐项核对；9 张卡逐卡过 |
| 语义误映射（`ratings` vs `scoreCounts` 口径混淆） | AC8 要求注释说明口径差异 |
| 三态处理偷懒（只做 loading） | AC4 要求逐卡三态证据 |
| 硬编码 `94` 等数字恰好与真实值巧合一致 | grep 常量本身，而非只看渲染结果 |

## 已确认的接口与类型（无需再查）

- `packages/shared/src/api/admin/dashboard.ts`：`overview()` / `trends(days)` / `collectionStats()` / `subjectStats()` / `hot(limit)`。
- 类型见 `packages/shared/src/types/index.ts:23-27`。
- 命名空间导出：`packages/shared/src/index.ts:29` 的 `adminDashboardApi`。
