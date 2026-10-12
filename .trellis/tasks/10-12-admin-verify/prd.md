# 管理端核验：确认现有 admin 对齐 dashboard-5 + app-shell-5

父任务：`.trellis/tasks/10-12-frontend-rebuild`。

> **本任务已从「重建 admin」改为「核验 admin」**（2026-10-12，依 `rebuild-prep/research/dashboard5-gaps.md` 的发现）。原任务 `10-12-admin-rebuild` 的删除+重装计划已作废：现有 admin 已是改造完成的 dashboard-5，重装会退回 demo 数据。

## Goal

核验现有 `frontend/admin` 是否已完全对齐 `@efferd/dashboard-5` + `@efferd/app-shell-5` 的目标形态，产出**差异清单**（而非重写）。不做破坏性改动；若发现真实缺口，登记后由父任务决定是否开新子任务。

## 背景（已确认事实）

- `git log`：`914f3237 feat(admin): dashboard-5 看板接入真实番剧运营数据`。
- `admin/src/components/dashboard/*.tsx` 的 props 已是后端真实类型：`HotItemVO[]`、`CollectionStatsVO['ratings']`、`SubjectStatsVO['seasons'|'scoreCounts']`、`importStat{importTotal,importSucceeded,importFailed}`、`DashboardOverview.todayNew*`。
- `flag.vercel.app` 外链**不存在**；`delta.tsx` 仅用 `lucide-react`。
- 后端 dashboard 端点仅 5 个（overview/trends/collection-stats/subject-stats/hot），全部被现有卡片消费；模板的访客/来源/国家/Web Vitals 演示指标已被替换为运营数据。
- `admin/src/components/dashboard/` 有 11 个文件 + `delta.tsx`/`share-bar-list.tsx`/`card-state.tsx`/`lib/formater.ts`。

## Requirements

- **R1 外壳核验**：确认 `AdminLayout` 是否基于 `app-shell-5`；列出与 `app-shell-5` 的形态差异（若有）。
- **R2 卡片核验**：逐卡片确认数据来源为真实端点、无 demo 残留、无外部请求。
- **R3 六页核验**：Subjects/Users/Import/Logs/AgentConfig/AgentChat 是否同属目标形态、是否各有 loading/empty/error。
- **R4 差异清单**：产出 `research/admin-diff.md`，按「已对齐 / 有差异 / 建议动作」三栏，标注证据（file:line）。
- **R5 不破坏**：本任务**默认不改 admin 源码**；除非核验发现的是明确缺陷，且改动极小、可独立验收。

## Acceptance Criteria

- [ ] AC1：`research/admin-diff.md` 落盘，逐项含证据。
- [ ] AC2：明确回答「admin 是否需进一步改动」；若需，给出最小动作清单与理由。
- [ ] AC3：`cd frontend && npm run typecheck -w admin && npm test -w admin` 通过（核验基线，不改代码）。
- [ ] AC4：无外部请求残留（`grep -rn "vercel.app\|https://" frontend/admin/src` 结果逐条判定）。

## Out of Scope

- 删除或重写 admin 源码（已作废）。
- 新增管理功能。

## 交付给父任务

`admin-diff.md` + 「是否需改动」的结论 + 最小动作清单（如有）。
