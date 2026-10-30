# 前端筛选 URL 归一化与浮层保持

## Goal

让 `/anime` 的全部筛选条件可被 URL 完整表达；让 agent 发起的页面跳转不再关闭 AI 助手浮层。

**本任务不引入任何 agent 代码**，是纯前端改造，独立可交付、独立有价值（筛选结果可分享、刷新不丢状态）。

**审查结论已定**（原型见 [prototype.md](./prototype.md)）：导航反馈采用 **V1 浮层内系统提示**，浮层位置尺寸**完全不动**。

## Background（源码事实）

- `frontend/client/src/pages/AnimeIndex.tsx:29`：`q` / `tag` / `page` 走 `useSearchParams`，但 `sort` / `order` / `year` / `weekday` 是 `useState`。`applyFilters()` 只 `setFilters` + `nav()`，而 `nav()` 只重建 q/tag/page。**年份筛选无法通过 URL 表达**。
- `frontend/client/src/components/AIAssistantFloat.tsx:16-18`：`useEffect(() => setOpen(false), [location.key])` 在任何路由变化时关面板。组件已挂在 `layouts/ClientLayout.tsx:28`（`{user && <AIAssistantFloat />}`），非 `/agent` 路由全局可用。
- 对照：`Schedule.tsx` 的 `year`/`quarter`/`tab`、`MyCollections.tsx` 的 `tab`/`page` **已全在 URL**，本任务是补齐 `AnimeIndex` 的欠账，落实该文件注释里已写的「以 URL 为唯一来源」。

## Requirements

### 筛选 URL 化

- `AnimeIndex` 的 `sort` / `order` / `year` / `weekday` 迁入 `useSearchParams`，与 `q` / `tag` / `page` 同源
- 默认值（`sort=score`、`order=desc`）在 URL 缺省时生效，不强制写入 URL
- 任何筛选变更统一重置 `page=1`（现有行为保留）
- 直接访问带筛选的 URL（如 `/anime?year=2022&weekday=5`）能正确渲染筛选后的结果

### 界面必须随操作真实变化（核心要求）

URL 只是状态的载体，**不能出现「地址栏变了但界面没变」**。每次状态变更必须同时驱动全部可见层面一致更新：

- **筛选控件自身显示值**同步（年份下拉显示「2022」而不是「全部年份」）
- **结果列表真实重查并替换**（`useQuery` 的 key 必须含新状态，触发新请求；不得复用旧数据）
- **结果计数/分页**随之更新；改筛选后页码回 1
- **加载态**：重查期间显示骨架屏（`SubjectGrid` 已有 `loading` 分支），不得直接闪空
- **无结果**：显示空态文案，不得保留上一次的列表
- agent 导航进入时**同样适用**：页面渲染的是导航指定筛选后的结果，不是原状态

### 浮层保持

- 浮层新增「agent 发起的导航不关面板」能力；用户手动点导航链接仍照常关闭
- 浮层保持机制不依赖尚未存在的 `ui_action` 事件：本任务只提供开关/标记位，由后续 child 接入
- **导航反馈 UI 归本任务**（2026-10-29 归属决定）：浮层内系统提示 `⚡ 已跳转到…` 的渲染与
  模块级 `showNavHint(label)` setter 由本任务交付，文案由服务端 `ui_action.meta.label` 下发。
  本任务**不接事件**，只用测试直接驱动 setter 验收；`ui-action-event` 负责在 `onUiAction` 里调用。
  详见 [design.md](./design.md) D1/D2

## Acceptance Criteria

- [ ] `/anime?year=2022&sort=score&order=desc&weekday=5` 直接打开即为对应筛选结果
- [ ] 在页面上改年份/星期/排序后，地址栏 URL 同步更新，刷新后状态不丢
- [ ] 改任一筛选后页码回到 1
- [ ] **界面随操作变化**（四条同时成立）：
  - [ ] 筛选控件的显示值与新状态一致
  - [ ] 结果列表内容真的变化（用不同年份断言卡片集合不同，不能只断言 URL）
  - [ ] 重查期间出现加载态，结束后不残留旧列表
  - [ ] 无结果时显示空态而非上一次结果
- [ ] 从 `/subject/:id` 的标签链接跳到 `/anime?tag=x` 行为不回归
- [ ] 浮层提供一个可供外部标记「本次导航由 agent 发起」的入口，标记时路由变化不关面板；未标记时照旧关闭；标记为**一次性**，用后复位
- [ ] `showNavHint(label)` 被调用时浮层内出现系统提示，且不写入会话历史（刷新即消失）
- [ ] 面板关闭时收到 hint，下次打开显示最后一条，不累积
- [ ] 前端测试基线不回归

## Out of Scope

- 不实现 `ui_action` 事件（child `ui-action-event` 的事）
- 不实现 agent 侧任何工具或图节点
- ~~不实现导航反馈的系统提示 UI~~ **已改归本任务**（仅 UI 与 setter，不接事件）
- 不改 `Schedule` / `MyCollections`（它们已合规）
- 不把浮层改造成新组件；复用现有 `AIAssistantFloat` + `AgentConversation`
- 不做窄屏自动收起（原型 V3 已否掉，一期不采用）
