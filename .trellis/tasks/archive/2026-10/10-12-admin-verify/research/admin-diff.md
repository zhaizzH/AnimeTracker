# admin 核验差异清单

核验对象：`frontend/admin`（只读）。基线：`git 914f3237 feat(admin): dashboard-5 看板接入真实番剧运营数据`。

## 结论

**admin 已是 `dashboard-5` + `app-shell-5` 的目标形态，无需重建。** 有 1 处真实缺口（Logs 列表查询错误未透出）与 1 处外观差异（header 无 Kbd 快捷键提示/DecorIcon），均不影响「不删除重建」的结论。

## 逐维度核验

### 1. 外壳

| 项 | 现状 | 判定 |
|---|---|---|
| `SidebarProvider` + `SidebarInset` | `src/layouts/AdminLayout.tsx:31,34` | 已对齐 |
| `SidebarTrigger` + `Breadcrumb` header | `AdminLayout.tsx:36-42` | 已对齐 |
| 面包屑取自真实导航项 | `AdminLayout.tsx:17` 用 `ADMIN_NAV_ITEMS` 匹配 pathname | 已对齐 |
| Kbd 快捷键提示 / DecorIcon | 无 | **差异（外观）**：efferd app-shell-5 header 含 `⌘b` 提示与装饰图标；现为手写 header。无功能影响 |

### 2. 导航

`src/components/app-sidebar.tsx:24-30` 为真实 7 条路由（看板/番剧管理/用户管理/导入管理/日志审计/Agent 配置/Agent 对话），**无** demo 分组（product/workspace/administration）、**无** changelog 卡片。判定：已对齐。

### 3. 看板卡片

| 卡片 | props 实际类型 | 端点 | 判定 |
|---|---|---|---|
| visitors-chart | `TrendPointVO[]` + newUsers/newCollections/logins | trends | 已对齐 |
| online-now | todayNewUsers/todayNewCollections/todayLogins | overview | 已对齐 |
| top-pages | `HotItemVO[]` | hot | 已对齐 |
| top-countries | `SubjectStatsVO['seasons']` | subject-stats | 已对齐 |
| top-referrers | 表格 | subject-stats / hot | 已对齐 |
| audience-mix | `CollectionStatsVO['ratings']` | collection-stats | 已对齐 |
| browser-share | `SubjectStatsVO['scoreCounts']` | subject-stats | 已对齐 |
| web-vitals | importStat(importCount/Succeeded/Failed) | subject-stats | 已对齐（**非** LCP/INP/CLS 演示指标） |
| traffic-sources | `CollectionStatsVO['types']` | collection-stats | 已对齐 |

无 demo 数据；三态由 `src/components/dashboard/card-state.tsx`（`CardState = 'loading'|'error'|'empty'|'ready'`，`toCardState`/`toCompositeCardState`）统一提供，含 `errorText='加载失败，请稍后重试'`。判定：已对齐。

### 4. 外部请求与图标

- `grep -rn "vercel.app\|https://" src/` → **NONE**（模板的国旗外链早已移除）。
- 图标库仅 `lucide-react`（4 处 import，无 hugeicons/phosphor/tabler/remixicon）。
判定：已对齐。

### 5. 六页三态

| 页 | loading | empty | error |
|---|---|---|---|
| Subjects | ✓ (isLoading×4) | ✓ | 变更走 `toastError`（`Subjects.tsx:108`） |
| Users | ✓ (isLoading×4) | ✓ | 变更走 `toastError`（`Users.tsx:43,55`） |
| Import | ✓ (isLoading×3) | ✓ | 变更走 toast |
| Logs | ✓ (isLoading×4) | ✓ | **缺**：无 `isError` 分支、无 `toastError` |
| AgentConfig | ✓ (isLoading×2) | ✓ | 变更走 toast |
| AgentChat | SSE 流式（loading 语义不同） | — | 健康态提示 |

**缺口（唯一实质问题）**：`src/pages/Logs.tsx` 的列表查询失败没有错误分支，失败时只会呈现空态，用户无法区分「无日志」与「加载失败」。建议动作：为该查询补 `isError` 分支或 `toastError`（小改动，可独立验收）。

### 6. 确认弹窗 ref 链（spec 契约）

三处 `<AlertDialogTrigger asChild>` 的子节点均为 `<Button>`：
- `Subjects.tsx:228-230`（删除）、`AgentConfig.tsx:110-112`（重置）、`Users.tsx:111`（控制变量 `control`）。

`src/components/ui/button.tsx:40` 为 `React.forwardRef`，ref 可落到真实 DOM。判定：契约成立（jsdom 无法发现，此处以源码判定）。

### 7. 基线门禁

`npm run typecheck -w admin` 通过；`npm test -w admin` → 10 文件 / 55 用例全通过。

## 建议动作

1. **不重建 admin**（核心结论）。
2. （可选，小）为 `Logs.tsx` 列表查询补错误态。
3. （可选，外观）若要完全对齐 app-shell-5 的 header 观感，可引入 Kbd 快捷键提示与 DecorIcon；纯装饰，低优先。
