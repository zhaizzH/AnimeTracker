# Design：dashboard-5 接入真实番剧数据

> 需求与验收见 `prd.md`。本设计限定在 admin Dashboard 页面和 registry block 组件，不改 API、shared 类型、AppShell 或其他页面。

## 架构与边界

- `admin/src/pages/Dashboard.tsx` 继续作为页面组合根：拥有 `days` UI state，调用现有 5 个 `useQuery`，并将各自的结果/状态传给 dashboard-5 9 个展示槽位。
- 将 `@efferd/dashboard-5` 与缺失的 `@efferd/formater`、`delta`、`indicator`、`share-bar-list` 按 registry 闭包落入 `admin/src/components`；保留组件层级、网格跨度和 Recharts/shadcn 视觉结构，只重写领域标题、数据字段、显示文案与状态处理。
- 复用已有 shadcn primitives、`cn()`、`@/` 别名和 `@shared` API；不另建 API client、响应类型或全局加载/错误状态。
- 查询仍沿用现存 queryKey：
  - `['dash', 'overview']` → `adminDashboardApi.overview()`
  - `['dash', 'trends', days]` → `adminDashboardApi.trends(days)`
  - `['dash', 'cs']` → `adminDashboardApi.collectionStats()`
  - `['dash', 'ss']` → `adminDashboardApi.subjectStats()`
  - `['dash', 'hot']` → `adminDashboardApi.hot(10)`

## 槽位数据流与语义

| # | 组件/槽位 | 页面传入/使用字段 | 展示语义与边界 |
|---|---|---|---|
| 1 | `VisitorsChart` | `TrendPointVO[]`: `date`, `newUsers`, `newCollections`, `logins`；周期由 `days` state 驱动 | 「新增趋势」三序列：新增用户、新增收藏、成功登录次数。7/30/90 控件使用 shadcn Button/ToggleGroup 中仓库已可用的原语，不增加新 queryKey。 |
| 2 | `OnlineNow` | `DashboardOverview`: `todayNewUsers`, `todayNewCollections`, `todayLogins` | 改为「今日运营」之类不暗示实时在线数的标题，不显示在线访客 demo 值。 |
| 3 | `TopPages` | `HotItemVO[]`: `id`, `nameCn ?? name`, `collectionCount`, 可选 `image` | 「热门番剧」Top 10，排序由接口提供；React key 用稳定 `id`。 |
| 4 | `TopCountries` | `SeasonCountVO[]`: `seasonKey`, `count` | 「播出季度分布」，标明番剧条目数量。 |
| 5 | `TrafficSourcesChart` | `CollectionStatsVO.types[]`: `type`, `count` | 「收藏类型分布」；类型映射 1–5 为想看/看过/在看/搁置/抛弃，未知值保留数字以免隐藏服务端新值。 |
| 6 | `AudienceMix` | `CollectionStatsVO.ratings[]`: `rate`, `count` | 「用户收藏评分分布」；这是用户给收藏条目的评分档，只含 `rate > 0` 的记录。 |
| 7 | `BrowserShare` | `SubjectStatsVO.scoreCounts[]`: `rate`, `count` | 「番剧自身评分分布」；后端将番剧 `score > 0` 按 `FLOOR(score)` 分档，和槽位 6 的用户评分不是同一个口径。 |
| 8 | `TopReferrers` | `SubjectStatsVO.importStatuses[]`: `importStatus`, `count` | 「番剧导入状态分布」：0 待导入、1 已导入；不称为导入任务成功/失败。未知状态以原值呈现。 |
| 9 | `WebVitals` | `overview.importCount`、`subjectStats.importStat.importSucceeded/importFailed` | 「导入记录」总数取 `overview.importCount`，成功/失败取 importStat。两个 query 均完成才展示值；任一失败显示错误，任一加载中显示加载态。 |

## 卡片状态契约

实现独立、可复用的轻量状态分支或在每个槽位内遵循同一规则，但不能把 5 个查询提升成一个整页门控：

1. **Loading**：显示简短、可访问的「加载中…」文本或等价 skeleton，并有 `aria-busy`；只影响消费该 query 的卡片。
2. **Error**：显示明确「加载失败，请稍后重试」等文案，不吞错成空数组；React Query 保留的旧 `data` 若存在，可由实现选择保留已有图表并标明刷新失败，但首次失败不能呈现 demo/伪造值。
3. **Empty**：空数组显示「暂无数据」等提示；统计值 `0` 是有效业务数据，不以 truthiness 判断为空。复合导入卡片在两个来源成功返回后展示真实的零值。
4. **Partial dependency**：热点/趋势/分布等单查询卡片只看自身 query；今日运营看 overview；导入记录卡片必须考虑 overview 与 subjectStats 两个 query 的 loading/error 状态，任一错误不得拼出误导性部分总览。
5. **图表空值**：空数组先渲染有语义的 empty 内容，不把空数组误解为查询成功后可留白；chart 区域应设置合理可访问名称。

## 趋势交互和测试边界

- `days` 默认值维持当前 30；控件仅接受 7、30、90。
- 选择周期更新 state，因 `days` 位于 `['dash','trends',days]` 中而触发对应 query；不手动绕过 React Query，也不修改其他缓存键。
- 为 Dashboard 新增组件测试，使用 QueryClientProvider + MemoryRouter（如页面需路由依赖），mock shared API 函数，验证字段映射、分离状态、三个周期 query 参数及切换后图表标题/数据更新。
- 通过可控 Promise 分别驱动 loading、error、empty，至少对 9 个卡片槽位逐个覆盖三态。共享 query 的多个槽位可用参数化测试保证相同 query 状态传到每个卡片；导入复合卡片另覆盖两个依赖任一 loading/error 的情况。
- 需为 recharts `ResponsiveContainer` 等 jsdom 边界提供最小 mock/尺寸 shim；mock 限定在测试，不影响生产渲染。

## 兼容性与迁移

- Foundation/AppShell 已完成；页面依旧通过现有 Router 的 AppShell Outlet 渲染，不能在 Dashboard 内再建立 shell。
- 当前 `Dashboard.tsx` 的 AntD import 与 `components/charts.tsx` 是本阶段切换点；删除 charts 前先仓库级搜索使用方，避免误删其他消费者。
- 当前 AppShell commit 的 Tailwind shadcn chart primitive 文件仍有 registry 原始双引号/分号风格；本任务新增/改写的 dashboard-5 相关文件应统一为 2 空格 + 单引号，不需要顺带重排现存无关 UI primitive。
- ECharts 包仍由 admin 其他页面迁移任务统一移除；本阶段不编辑依赖清理逻辑，除 dashboard 所需 registry 组件的必需依赖闭包外。

## 权衡

- 让页面组合 query、block 负责呈现可保持数据边界清晰，也最容易保证 9 槽位独立状态；不把 query 搬进每张 block，避免重复请求和破坏既有 queryKey。
- 槽位按当前 PRD 全量保留，虽然流量分析组件名与番剧业务不同；必须用用户可见标题改写，不能让原组件名/原语义泄漏至 UI。
- 不扩展接口来合并 overview 与 subjectStats：导入卡片短暂等待两个既有请求，换取不改变后端/shared 契约。

## 风险与回滚

| 风险 | 缓解 | 回滚点 |
|---|---|---|
| registry 引入导致路径别名或缺失组件构建失败 | 添加后检查完整依赖闭包、typecheck、build | 恢复 Dashboard/charts 变更并删除新增 block 文件 |
| demo 数字藏在 delta、indicator 或子组件默认值 | 对所有新增/修改的 dashboard-5 文件进行 demo 文案和值检索与逐槽审查 | 删除/重映射对应卡片静态值 |
| Recharts 在 jsdom 下缺少尺寸导致测试误报 | 测试环境使用隔离的 ResponsiveContainer mock，另以 build 验证真实组件 | 仅回退测试 shim，不更改生产图表 |
| 旧图表 wrapper 被其他代码使用 | 删除前全仓引用搜索，删除后再次搜索 | 若发现其他消费者则停止删除并回到需求阶段调整范围 |
