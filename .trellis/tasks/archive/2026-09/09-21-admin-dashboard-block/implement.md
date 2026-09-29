# Implement：dashboard-5 接入真实番剧数据

> 需求与验收见 `prd.md`，技术方案见 `design.md`。严格按顺序执行；本计划不包括 `task.py start`，需经用户审阅后另行确认。

## 执行前检查

- [ ] 确认当前 task 为 `.trellis/tasks/09-21-admin-dashboard-block` 且状态 planning；本任务所有改动只触及 Dashboard/block/相关测试与本任务 artifacts。
- [ ] 依赖确认：Foundation 与 AppShell 已归档完成。当前工作树有用户既有修改（包括 `frontend/admin/package.json` 等），先保留，不覆盖或提交无关改动。
- [ ] 读取 dashboard-5 registry 与其递归 registryDependencies，列出新增/改动文件；安装组件之前检查现有文件以避免覆盖并保留用户更改。若 CLI 将覆盖现有文件，先用隔离 registry 下载/对比或暂停确认，不能无检查覆盖。
- [ ] 全仓搜索 `charts.tsx` 的引用。若出现 Dashboard 之外消费者，先停下修订范围，不直接删除。

## 实现步骤

### D1 — 引入 block 及完整依赖

- [ ] 引入 `@efferd/dashboard-5` 与缺失 registry 组件 `@efferd/formater`、`delta`、`indicator`、`share-bar-list`，补齐 block 真正需要的 UI 组件和 npm 依赖。
- [ ] 检查新增组件中硬编码的 demo 数值、文案、fallback 与默认数据，不允许仅替换 Dashboard 页而遗留子组件 demo。
- [ ] 对本次新增/改写的 block 文件统一成 2 空格缩进、单引号、仓库分号风格；保留与仓库兼容的 TSX/API。

### D2 — 页面查询与 9 槽位接线

- [ ] 在 `admin/src/pages/Dashboard.tsx` 保留 5 个现有 QueryClient 查询函数和 queryKey，不改变 shared API/type 契约。
- [ ] 将趋势 query 数据接至面积图三序列：`newUsers`、`newCollections`、`logins`，标签明确为新增用户/新增收藏/登录次数。
- [ ] 将 `overview.todayNewUsers`、`todayNewCollections`、`todayLogins` 接至今日运营槽位，移除 online-now demo 语义。
- [ ] 将 `hot(10)` 响应接至 TopPages 槽位，显示 `nameCn ?? name`、`collectionCount`，列表使用 `HotItemVO.id` 稳定 key。
- [ ] 将 `subjectStats.seasons`、`collectionStats.types`、`collectionStats.ratings`、`subjectStats.scoreCounts`、`subjectStats.importStatuses` 分别接至季度、收藏类型、用户收藏评分、番剧自身评分、番剧导入状态槽位。
- [ ] 将导入记录卡片总数绑定 `overview.importCount`，成功/失败绑定 `subjectStats.importStat.importSucceeded` / `importFailed`，且两 query 状态均纳入卡片状态。
- [ ] 逐个审阅 slot 的用户可见 title/description、tooltip、empty/loading/error 文案及单位，确保不残留访客/浏览器/流量/国家/核心 Web 指标措辞，也不混淆两种评分/导入状态口径。

### D3 — 交互、异步状态与测试

- [ ] 将 7/30/90 天选择器改用现有 shadcn Button/ToggleGroup 方案，默认周期保留 30；确保 `days` 进入 `['dash','trends',days]` 并触发对应请求。
- [ ] 实现并统一每槽位 loading、error、empty 状态；统计零值必须显示为 0，不将 `0` 判断为空；首屏 error 不允许显示伪造数据。
- [ ] 为 Dashboard 添加 Vitest/Testing Library 测试：核对 9 项真实字段映射与语义标签，逐卡覆盖 loading/empty/error；覆盖 overview 和 subjectStats 的独立状态，以及导入卡片双依赖状态。
- [ ] 测试 7/30/90 三个周期切换对应的 `trends(days)` 调用和图表更新。对 Recharts 的 DOM 尺寸需求仅在测试环境 mock/shim。
- [ ] 在 Dashboard 切换到 shadcn 组件并删除旧 `antd` 用法；确认页面仍经 AdminLayout/AppShell Outlet 渲染。
- [ ] 全仓确认 `charts.tsx` 无其他消费者后删除 `admin/src/components/charts.tsx`，确认全仓零引用。
- [ ] 对 Dashboard 与新增/改写的 block 源码扫描原 demo 内容：`94`、`555`、`Chrome`、`/pricing`、`Returning visitors`、`Core Web Vitals`、`Organic search`，并人工检查其余默认展示值。

## 验证清单

在 `frontend/` 目录执行：

```bash
npm run typecheck
npm test -w admin
npm run build
```

- [ ] 记录三个命令的真实结果；若失败先定位并修复，不把未验证标为通过。
- [ ] 搜索确认 Dashboard 未 import antd，charts.tsx 已删除且无引用；本任务不要求清除 package.json 中 antd/echarts 依赖。
- [ ] 按 PRD AC1–AC8 逐项核对，将逐卡字段映射、三态测试、周期切换证据及 demo 检索结果更新至 PRD/任务验收记录。
- [ ] 最终全范围 check 覆盖本任务新增/修改 Dashboard、block、测试文件，不把其他工作区已有脏文件混入本任务变更。

## 风险文件与回滚点

- 主要改动：`frontend/admin/src/pages/Dashboard.tsx`、`frontend/admin/src/components/dashboard/**`（以 registry 实际路径为准）、Dashboard 测试，以及 `frontend/admin/src/components/charts.tsx` 删除。
- 用户已有变更：`frontend/admin/package.json` 当前已被修改；执行依赖安装前比较现有 diff，只做需要的增量编辑，不恢复或重写其他人的依赖改动。
- 若 registry 代码不适配项目配置，先保留现有 Dashboard/charts，回滚新增 block 文件后调整导入方案；不回滚 Foundation/AppShell 已提交实现。
- 若 AC 证据无法取得真实浏览器/后端数据，使用显式标记的 API mock 自动化验证字段契约，并将真实后端联调列为未完成，不能伪称实测。
