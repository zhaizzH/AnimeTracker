# 设计：admin 核验

## 性质

本任务是**只读核验**，不是重建。不改动 `frontend/admin/src`（AC3 的 typecheck/test 只是基线，不是改动）。

## 核验维度

| 维度 | 判据 | 证据锚点 |
|---|---|---|
| 外壳 | 是否 `app-shell-5` 形态（SidebarProvider/侧栏/头部） | `admin/src/layouts/AdminLayout.tsx` |
| 导航 | 7 条真实路由，无 demo 分组 | `admin/src/components/app-sidebar.tsx:23` |
| 卡片数据 | props 为后端真实类型 | `admin/src/components/dashboard/*.tsx` 顶部 props |
| 无 demo 残留 | 无外部请求、无硬编码演示序列 | `grep -rn "vercel.app\|https://"` |
| 图标 | 仅 lucide | `admin/src/components/delta.tsx:4` |
| 六页 | 各有 loading/empty/error | 各 `pages/*.tsx` |
| 确认弹窗 | `AlertDialogTrigger asChild` + `forwardRef` 契约 | `component-guidelines.md:41-44` |

## 不变量

- 核验不动 `packages/shared`、不动 client。
- 若发现缺陷，**不在本任务就地重写**；写入 `admin-diff.md` 的「建议动作」，交父任务决策。

## 与父任务的关系

父任务 Cross-Child AC 里「admin 看板由 dashboard-5 卡片渲染真实数据」由本任务提供证据（而非由重建产生）。
