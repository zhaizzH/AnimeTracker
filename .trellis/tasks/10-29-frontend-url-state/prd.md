# 前端筛选 URL 归一化与浮层保持

> **状态：已完成**（2026-10-30，提交 `bdf98880`）。9/9 验收项达标，1 项端到端链路仅有手工验证，详见文末「验收证据」。

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

- [x] `/anime?year=2022&sort=score&order=desc&weekday=5` 直接打开即为对应筛选结果
- [x] 在页面上改年份/星期/排序后，地址栏 URL 同步更新，刷新后状态不丢
- [x] 改任一筛选后页码回到 1
- [x] **界面随操作变化**（四条同时成立）：
  - [x] 筛选控件的显示值与新状态一致
  - [x] 结果列表内容真的变化（用不同年份断言卡片集合不同，不能只断言 URL）
  - [x] 重查期间出现加载态，结束后不残留旧列表
  - [x] 无结果时显示空态而非上一次结果
- [x] 从 `/subject/:id` 的标签链接跳到 `/anime?tag=x` 行为不回归 —— **部分覆盖**：URL 入参已验证，从详情页点链接的端到端链路未补自动化（手工验证通过）
- [x] 浮层提供一个可供外部标记「本次导航由 agent 发起」的入口，标记时路由变化不关面板；未标记时照旧关闭；标记为**一次性**，用后复位
- [x] `showNavHint(label)` 被调用时浮层内出现系统提示，且不写入会话历史（刷新即消失）
- [x] 面板关闭时收到 hint，下次打开显示最后一条，不累积
- [x] 前端测试基线不回归

### 追加验收（2026-10-30 实现期间发现，已达标）

- [x] 关键词输入框跟随外部 URL：直接打开 `?q=` 时回显，外部改 q 后跟随，再搜索不把 URL 覆盖回旧值
- [x] `?year=abc&weekday=xyz` 等非法值视为未筛选，不带 `NaN` 进 queryKey 与请求
- [x] 用户手动导航时作废上一条 navigation hint，不残留过期假信息


## Out of Scope

- 不实现 `ui_action` 事件（child `ui-action-event` 的事）
- 不实现 agent 侧任何工具或图节点
- ~~不实现导航反馈的系统提示 UI~~ **已改归本任务**（仅 UI 与 setter，不接事件）
- 不改 `Schedule` / `MyCollections`（它们已合规）
- 不把浮层改造成新组件；复用现有 `AIAssistantFloat` + `AgentConversation`
- 不做窄屏自动收起（原型 V3 已否掉，一期不采用）

## 验收证据（2026-10-30，提交 `bdf98880`）

### 门禁结果

| 门禁 | 结果 |
|---|---|
| `npm test -w client` | 11 文件 / **70 用例**全绿（起始基线 49） |
| `npm run typecheck -w client` | 无错误 |
| `npm run build -w client` | 通过 |

### AC → 测试映射

| 验收项 | 测试（文件 :: 用例名） |
|---|---|
| 带筛选 URL 直接打开 | `anime-index.tag-url` :: 直接打开带筛选的 URL 时四个字段全部进入查询，控件同步回显 |
| 改年份同步 URL + 页码归 1 | 同上 :: 改年份写回 URL、控件回显新值，并把页码重置回 1 |
| 改星期同步 URL | 同上 :: 改播出星期写回 URL 并回显，页码重置回 1 |
| 排序／方向回默认值移除键 | 同上 :: 排序改回默认值时从 URL 移除该键 / 方向改回默认值 `desc` 时从 URL 移除该键 |
| 翻页不重置页码 | 同上 :: 翻页不算筛选变更，页码不会被重置回 1 |
| 界面随操作变化 ① | 同上 :: ① 控件显示值同步：改年份后下拉立刻回显 2022 |
| 界面随操作变化 ② | 同上 :: ② 结果列表真实重查并替换：新集合出现、旧集合消失 |
| 界面随操作变化 ③ | 同上 :: ③ 重查期间出现骨架屏，结束后不残留旧卡片 |
| 界面随操作变化 ④ | 同上 :: ④ 无结果时显示空态，不保留上一次的列表 |
| 重置按钮 | 同上 :: 重置清空全部筛选：URL 回空、年份回全部年份、关键词清空 |
| 标签 URL 不回归 | 同上 :: URL ?tag= 直接作为查询条件，无需点击 / `/subject/:id` 标签链接（**仅 URL 侧，端到端链路手工验证**） |
| 关键词框跟随 URL | 同上 :: 直接打开带 q 的 URL 时输入框回显 / 外部导航改 q 后输入框跟随，再搜索不把 URL 覆盖回旧值 |
| 非法参数收尾 | 同上 :: `?year=abc&weekday=xyz` 时不带 NaN 进请求，控件回落到全部 |
| 标记后不关面板 | `agent.float` :: 标记 agent 导航后，路由变化不关面板 |
| 标记一次性 | 同上 :: 标记是一次性的：用后复位，用户下一次手动导航仍照旧关闭 |
| 未标记照旧关闭 | 同上 :: 路由切换时关闭浮窗，并能跳转完整助手（既有用例，未回归） |
| 提示不写会话历史 | 同上 :: `showNavHint` 后面板内出现系统提示，且不写入会话历史 |
| 面板关闭时 hint 保留 | 同上 :: 面板关闭时收到 hint，下次打开显示最后一条，不累积 |
| hint 过期作废 | 同上 :: 用户手动导航时作废上一条提示，再开面板不再显示 |

### 变异验证（断言确实能杀）

每条都在临时破坏实现后跑出红，随后 `cp` 还原并确认 `git diff --stat` 一致：

| 变异 | 转红用例 |
|---|---|
| 删 `clearNavHint()` | 用户手动导航时作废上一条提示，再开面板不再显示 |
| 删 `useEffect(() => setKeyword(q), [q])` | 外部导航改 q 后输入框跟随，再搜索不把 URL 覆盖回旧值 |
| 去掉 `Number.isFinite` 收窄 | `?year=abc&weekday=xyz` 时不带 NaN 进请求，控件回落到全部 |
| `useQuery` 加 `placeholderData`（旧列表停留） | ③ 重查期间出现骨架屏（`SubjectGrid` 骨架断言） |
| queryKey 删掉 `year, weekday` | ②③④ 三条同时红 |
| `SubjectGrid` loading 分支恒假 | ③ 转红 |

### 交付物

- `frontend/client/src/pages/AnimeIndex.tsx`：四字段迁入 URL、`nav()` 以当前 params 为底重建、`toNum` 收窄、关键词同步
- `frontend/client/src/components/agentNavigation.ts`（新）：`markAgentNavigation` / `consumeAgentNavigation` / `showNavHint` / `clearNavHint` / `useNavHint`
- `frontend/client/src/components/AIAssistantFloat.tsx`：agent 分支保留面板、非 agent 分支关面板并作废提示、面板内渲染 `⚡ 已跳转到「…」`
- 测试：`anime-index.tag-url.test.tsx`（9→25 用例）、`agent.float.test.tsx`（5→10 用例）

### 未做（明确留给后续）

- 不接 `ui_action` 事件；child 2 只需在 `onUiAction` 里按「`markAgentNavigation()` → `navigate(meta.path)` → `showNavHint(label)`」调用，**不必再改 `AIAssistantFloat.tsx`**
- 提示文案由服务端 `ui_action.meta.label` 下发，前端不维护 action→中文映射
