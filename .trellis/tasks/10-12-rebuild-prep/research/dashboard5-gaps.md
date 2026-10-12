# dashboard-5 字段核对结论

## 核对方法

1. 读 `packages/shared/src/api/admin/dashboard.ts`（真实端点）与 `packages/shared/src/types/index.ts`（类型）。
2. 读 `frontend/admin/src/components/dashboard/*.tsx` 的 props 形状。
3. 对 `docs/spec/openapi.yaml` 的 dashboard 段确认端点存在性。
4. grep 模板的两个已知liability（`flag.vercel.app`、多图标集）在当前 admin 的实际状态。

## 后端真实提供的端点（全部存在）

| 端点 | 类型 |
|---|---|
| `/api/admin/dashboard/overview` | `DashboardOverview { userCount, subjectCount, collectionCount, episodeCount, importCount, todayNewUsers, todayNewCollections, todayLogins }` |
| `/api/admin/dashboard/trends` | `TrendPointVO[] { date, newUsers, newCollections, logins }` |
| `/api/admin/dashboard/collection-stats` | `CollectionStatsVO { types[], ratings[] }` |
| `/api/admin/dashboard/subject-stats` | `SubjectStatsVO { seasons[], importStatuses[], importStat{importTotal,importSucceeded,importFailed}, scoreCounts[] }` |
| `/api/admin/dashboard/hot` | `HotItemVO[] { id, name, nameCn, image, collectionCount }` |

openapi.yaml 行号：overview 4089 / trends 4143 / collection-stats 4192 / subject-stats 4242 / hot 4322。

## 关键结论：**不存在「后端缺字段」的卡片**

模板卡片名与真实数据 1:1 对应，因为**现有 admin 的 dashboard 组件已经就是改造后的 dashboard-5**——文件名沿用模板（`visitors-chart`/`top-pages`/`audience-mix`/`web-vitals`…），但 props 已换成真实后端类型：

| 模板卡片名（efferd） | 现有 admin 实现的实际输入 | 对应端点 |
|---|---|---|
| `visitors-chart` | `newUsers` / `newCollections` / `logins` | trends |
| `online-now` | `todayNewUsers` / `todayNewCollections` / `todayLogins` | overview |
| `top-pages` | `HotItemVO[]` | hot |
| `top-countries` | `SubjectStatsVO['seasons']` | subject-stats |
| `top-referrers` | （表格形态） | subject-stats / hot |
| `traffic-sources-chart` | share-bar | collection-stats / subject-stats |
| `audience-mix` | `CollectionStatsVO['ratings']` | collection-stats |
| `browser-share` | `SubjectStatsVO['scoreCounts']` | subject-stats |
| `web-vitals` | `importCount` / `importSucceeded` / `importFailed` | subject-stats.importStat |

**因此 web-vitals（LCP/INP/CLS）等模板演示指标并不存在于现有实现**——先前的改造已把它们替换为导入统计。原假设的「Web Vitals 缺字段需降级」不成立。

## 模板 liability 的当前状态（均已在先前改造中处理）

| liability | 当前 admin 状态 |
|---|---|
| `flag.vercel.app` 外链 | **不存在**（已本地化） |
| `DeltaIcon` 多图标集（5 套） | **已收敛**：`delta.tsx` 仅 `import { Minus, TrendingDown, TrendingUp } from 'lucide-react'` |
| `@efferd/formater` | 现有 `admin/src/lib/formater.ts` 已提供 |

## 对子任务 5 的影响（需父任务知悉）

1. **不应「先装模板再适配」**：装 `@efferd/dashboard-5` 会引入模板的 demo 卡片实现（访客/在线/来源/国家/浏览器/Web Vitals 指标），其字段后端不提供；而现有实现已是适配版。
2. **正确做法**：`@efferd/dashboard-5` 仅用于取 **外壳 `app-shell-5`** 与少量 primitive；看板卡片**保留/重建现有 `admin/src/components/dashboard/*` 的适配实现**（它们本身就是 efferd 的形态 + 真实数据类型）。
3. **本子任务删除 `admin/src` 前必须保全该参考实现**——见 `implement.md` 步骤 4 的保全动作。
4. 子任务 5 的 `design.md` R4/R5 描述的「移除 flag.vercel.app」「图标收敛 lucide」**已是既成事实**，属无操作项。

## 给父任务的 deferred 清单

- 无「后端缺字段」项。
- 新增待确认项：`@efferd/dashboard-5` 是否仍值得安装，或其价值仅限于 `app-shell-5` 外壳（决策留父任务/用户）。
