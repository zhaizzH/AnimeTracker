# 设计补充：前端筛选 URL 归一化与浮层保持

> 承接 `prd.md` / `implement.md`。本文只记 2026-10-29 跨 child 问答中定下的决定与代码事实，
> 不复制 spec。探针与源码证据见文末。

## D1 浮层对外暴露两个 setter，UI 归本 child

导航反馈（原型 V1 的 `⚡ 已跳转到「…」`）**归本任务**，不留给 `ui-action-event`。
理由：浮层组件在本任务改造范围内，让 child 2 只负责通道、不碰 UI 结构，两个 child 才不会抢文件。

对外接口（模块级，非 React context——setter 要被 hook 回调在非组件上下文调用）：

```ts
// frontend/client/src/components/agentNavigation.ts
export function markAgentNavigation(): void   // 标记「下一次路由变化由 agent 发起」
export function showNavHint(label: string): void  // 浮层内插一条系统提示
```

- `markAgentNavigation()` 内部置一个**一次性**标记位。`AIAssistantFloat` 的
  `useEffect(() => setOpen(false), [location.key])` 改为：标记为真则跳过关闭并**立即复位**；
  未标记照旧关闭。一次性是为了不让用户后续手动导航被误放行。
- `showNavHint(label)` 用**外部 store + `useSyncExternalStore`** 让 `AIAssistantFloat` 订阅。
  不用 `useState`：setter 要在组件外调用；不用 `zustand`：项目前端目前只有 auth 一个 store，
  为 3 个字段引一个 store 库不划算，`useSyncExternalStore` 足够。
- 面板**关闭**时收到 hint：入队，下次打开时显示。理由：agent 导航发生前面板可能本来就是关的
  （用户在 `/agent` 页之外，浮层默认收起），丢掉提示用户就看不到「刚才发生了什么」。
  队列只保留**最后一条**，不累积——连续两次导航只显示最后一次。
- **hint 的作废时机（2026-10-30 补，原设计遗漏）**：用户**手动**路由变化时立即清空。
  否则第一次 agent 导航的提示会永久贴在面板里，用户之后跳 `/schedule`、关面板再开，
  看到的还是「⚡ 已跳转到「2022 年的番」」——已不在那个页面，属于过期假信息。
  - 清空点挂在 `AIAssistantFloat` 的 `location.key` effect 的**非 agent 分支**：
    `if (consumeAgentNavigation()) return;` 之后跟 `setOpen(false); clearNavHint();`
  - **不能改成「打开面板时清空」**：prd 的「面板关闭时收到 hint，下次打开显示」要求保留，
    两者会直接冲突。
  - `agentNavigation.ts` 导出 `clearNavHint()`，与 `showNavHint` 同一套 listener 通知。
- 系统提示不进入 `useAgentChat` 的 `messages`（那是会话历史，会持久化到后端）。
  它是**本地瞬时 UI 状态**，与 `notice` 同性质。刷新后消失，不补。
- 尺寸/位置完全不动（V1 定案），不做窄屏自动收起（V3 已否）。

### 交互时序

```
onUiAction(action, params, label)     // child 2 提供
  → markAgentNavigation()
  → navigate(path)                    // react-router
  → showNavHint(label)
```

顺序不能反：先标记再 `navigate`，否则 `location.key` effect 先于标记执行，面板被关。

## D2 `label` 由服务端下发，前端不维护映射表

`ui_action.meta` 带一个 `label` 字段（如「2022 年的番」「我的收藏 · 在看」），
由 `navigation_emitter` 按白名单**固定模板**生成，**不是模型自由文本**。

理由：前端若自己把 5 个 action + 参数翻译成中文，等于把白名单知识复制两份；
服务端既然已经独占 URL 构造（spec §5），文案也归它，两端只传一个 string。

详见 `10-29-navigation-graph/design.md` D4。

## D3 筛选迁入 URL：4 个字段 + 引用稳定性

`AnimeIndex.tsx` 的 `sort` / `order` / `year` / `weekday` 从 `useState` 迁到 `useSearchParams`：

```ts
const sort = params.get('sort') ?? 'score';
const order = (params.get('order') ?? 'desc') as 'asc' | 'desc';
const year = params.get('year') ? Number(params.get('year')) : undefined;
const weekday = params.get('weekday') ? Number(params.get('weekday')) : undefined;
```

- `queryKey` 用**原始标量**而非新对象：`['subjects','search', q, sort, order, year, weekday, page, selectedTags]`。
  现有代码的 `filters` 对象每次渲染都是新引用，靠 tanstack 的结构化 key 比较才没炸；
  迁到标量后天然稳定，不必额外 `useMemo`。
- **非法 URL 值必须收窄**（2026-10-30 补）：`Number('abc')` 是 `NaN`，若直接进 queryKey 与请求参数，
  会产生永远不命中的缓存键并把 `NaN` 发给后端。`year` / `weekday` 都要 `Number.isFinite` 兜住，
  非法即视为未筛选。`order` 用三元收窄成联合类型，不用 `as` 断言（比原设计更好）。
- **关键词输入框要跟 q 走**（2026-10-30 补）：`const [keyword, setKeyword] = useState(q)` 只取挂载时的值。
  外部导航到 `/anime?q=2022` 后结果按 2022 查，但输入框仍显示旧值，再点搜索会把 URL 覆盖回去——
  违反「筛选控件显示值与新状态一致」，且 child 2 的 `open_anime_index` 带 `q?` 会直接踩。
  用 effect 同步 `q → keyword`；不要用 `key={q}` 重挂（会丢焦点）。
- `queryFn` 的 `subjectsApi.search({...})` 参数同理直接用标量展开。
  现有 `sort: 'score', order: 'desc', ...filters` 的写法删掉，改为显式传 7 个字段。
- `nav()` 重写为：以**当前 params 为底**重建 `URLSearchParams`（`new URLSearchParams(params)`），
  再应用 patch；默认值（`sort=score`、`order=desc`、无 year/weekday）**不写进 URL**，保持地址栏干净。
- 任何筛选变更统一 `page=1`（现有行为）。**翻页本身不算筛选变更**：
  `onPageChange` 走 `nav({page: p})`，不被重置回 1。
- `reset()` 改为 `setParams({})` + `setKeyword('')`，不再有 `setFilters`。

### `selectedTags` 的引用

`params.getAll('tag')` 每次渲染返回新数组。现有代码已在用且 tanstack 按内容比较 key，
保持现状即可，**不引入 `useMemo`**——不要顺手优化不在本任务范围内的事。

## D4 界面随操作变化：四条断言的可测形态

PRD 的四条硬要求翻译成具体断言，避免落地时只测 URL：

| 要求 | 断言形态 | 依赖 |
|---|---|---|
| 控件显示值同步 | `getByLabelText('年份')` 的文本含「2022」而非「全部年份」 | 无 |
| 列表真实重查并替换 | mock `subjectsApi.search` 按 `year` 返回**不同名称集合**；断言新集合出现、旧集合消失 | mock 必须真的按参数分支，否则测不出 |
| 重查期间加载态 | mock 返回可控 pending promise；断言骨架屏出现（`SubjectGrid` 的 `aria-hidden` 容器），resolve 后消失 | 需要可控 deferred，不能只用 `waitFor` |
| 无结果显示空态 | mock 返回 `content: []`；断言 `emptyText` 出现且旧卡片不在文档里 | 无 |

现有 `SubjectGrid` 的 `loading` 分支直接 return 骨架，**不会**残留旧列表，
且 `useQuery` 未配 `placeholderData`/`keepPreviousData`，换 key 即 `isLoading=true`。
所以 D4 主要是**写测试锁住现状**，而不是改组件。实现时若发现引入了新缓存行为，以 PRD 为准回退。

## D5 与后续 child 的接缝

本任务交付后、其它 child 未做时的状态：

- URL 能完整表达筛选 → 用户可分享/刷新不丢，**独立价值已兑现**
- `markAgentNavigation` / `showNavHint` 已导出但无人调用 → 用**测试直接驱动**验收，
  不依赖 `ui_action` 事件存在
- 浮层仍会在用户手动导航时关闭 → 行为不回归

child 2 完成 `onUiAction` 后，只需在 `AgentChat.tsx` 里接上这两个 setter，
**不需要再改 `AIAssistantFloat.tsx`**。

## 不做（重申）

- 不接 `ui_action`、不实现 `onUiAction`
- 不改 `Schedule` / `MyCollections`（已合规，键名见 `10-29-navigation-graph/design.md` D3）
- 不重写浮层组件、不引新状态库
- 不做窄屏自动收起、不做 toast 形态反馈

## 源码事实（已查证）

- `AnimeIndex.tsx:29` `filters` 是 `useState`；`nav()` 只重建 q/tag/page
- `AIAssistantFloat.tsx:16-18` `useEffect(() => setOpen(false), [location.key])` 无条件关面板
- `AIAssistantFloat.tsx` 在 `/agent` 路径下 `return null`（`location.pathname` 去尾斜杠比较），
  所以 `/agent` 页不受关闭逻辑影响；本任务的改造只影响其它路由
- `AgentChatProvider` 挂在 `ClientLayout`，全路由常驻，浮层与 `/agent` 页共享会话
- `SubjectGrid` `loading` 分支直接 return 骨架，空态走 `emptyText`
- `MyCollections` tab 键是 `'all' | '1' | '2' | '3' | '4' | '5'`（数字字符串，不是 want/watching），
  `page` 从 1 开始
- 测试栈：vitest + `@testing-library/react` + jsdom，已有 `anime-index.tag-url.test.tsx` 可参照
