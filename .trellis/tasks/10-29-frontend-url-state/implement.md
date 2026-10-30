# 执行计划：前端筛选 URL 归一化与浮层保持

**审查已定**：导航反馈用 V1（浮层内系统提示），浮层尺寸不动，界面必须随操作真实变化。

## 切片 1：`AnimeIndex` 筛选迁入 URL

文件：`frontend/client/src/pages/AnimeIndex.tsx`

1. 读现有 `filters` state 四字段（`sort` / `order` / `year` / `weekday`）与 `applyFilters` / `nav` 调用点
2. 改为从 `useSearchParams` 派生：
   - `sort = params.get('sort') ?? 'score'`
   - `order = params.get('order') ?? 'desc'`
   - `year = params.get('year') ? Number(...) : undefined`
   - `weekday` 同理
3. `nav()` 扩展为同时写这四个键；**默认值不写入 URL**（保持地址栏干净）
4. `applyFilters()` 不再 `setFilters`，只调 `nav(patch)`
5. 删除 `filters` 的 `useState`

**TDD**：先写「直接打开 `/anime?year=2022&weekday=5` 渲染对应筛选」的失败测试，再实现。

**注意**：`useQuery` 的 `queryKey` 现含 `filters` 对象，改为从 URL 派生后必须保持引用稳定（用原始 string 值而非新对象），否则每渲染都触发请求。

## 切片 2：界面随操作变化（核心验收）

URL 改动必须驱动全部可见层面，不能只改地址栏：

1. **控件显示值**：`Select` 的 `value` 直接绑定 URL 派生值（不再绑 `useState`），改完立刻回显
2. **列表真实重查**：`queryKey` 含 `q / tags / page / sort / order / year / weekday` 全部字段；缺任一项会导致换筛选不重查
3. **加载态**：`SubjectGrid` 的 `loading` 已有骨架屏分支，确认重查期间 `isLoading` 为真、不被 `keepPreviousData` 抹平；若当前有 `placeholderData` 需评估是否保留（保留会让旧列表短暂停留，与「不残留旧列表」冲突时以 PRD 为准）
4. **空态**：`items.length === 0` 走 `emptyText`，确认不会因为缓存显示旧数据
5. **页码重置**：`nav()` 统一写 `page=1`

**TDD**（四条否定/正向断言，缺一不可）：
- 改年份后控件显示值变化
- 改年份后**卡片集合**变化（断言名称集合不同，不能只断言 URL）
- 重查期间出现骨架屏
- 无结果时显示空态而非旧列表

## 切片 3：浮层「agent 导航」标记位 + 系统提示

新文件 `frontend/client/src/components/agentNavigation.ts`：

```ts
export function markAgentNavigation(): void
export function showNavHint(label: string): void
```

模块级外部 store + `useSyncExternalStore` 让 `AIAssistantFloat` 订阅。
不引新状态库，不用 React context（setter 要在非组件上下文被 hook 回调调用）。

`AIAssistantFloat.tsx`：

1. `useEffect(() => setOpen(false), [location.key])` 改为：标记为真则跳过关闭并**立即复位**；未标记照旧关闭
2. 面板内渲染最后一条 hint：`⚡ 已跳转到{label}`
3. 面板关闭时收到 hint 入队，下次打开显示；队列只留最后一条
4. hint 是本地瞬时状态，**不进** `useAgentChat` 的 `messages`（那会持久化到后端）
5. 尺寸/位置不动，不做窄屏收起
6. 本任务**不接事件**，只用测试直接驱动两个 setter

**调用顺序约束**（写给 child 2）：`markAgentNavigation()` → `navigate()` → `showNavHint()`。
反了 `location.key` effect 会先执行，面板被关。

**TDD**：标记时路由变化面板仍开；未标记时照旧关闭；标记用后复位（第二次导航仍关）；
`showNavHint` 后面板出现提示且 `messages` 不变。

## 切片 4：回归

- 从 `/subject/:id` 标签链接跳 `/anime?tag=x` 不回归
- 改任一筛选页码回 1
- 前端既有测试基线全绿

## 验证

```bash
cd frontend && npm test -w client
cd frontend && npm run typecheck -w client
```

## 不做

- 不接 `ui_action`、不实现 `onUiAction`
- 不自己生成提示文案（`label` 由服务端 `ui_action.meta` 下发）
- 不做窄屏自动收起（原型 V3 已否）
- 不改 `Schedule` / `MyCollections`
- 不重写浮层组件
