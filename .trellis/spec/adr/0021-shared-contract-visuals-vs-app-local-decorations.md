# 0021 — 前端「契约性视觉」下沉 shared，装饰件与 `ui` 原语层各端自持

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：[frontend/component-guidelines.md](../frontend/component-guidelines.md)、[frontend/directory-structure.md](../frontend/directory-structure.md)

## 背景

用户端（client）与管理端（admin）是两个独立 SPA，各自维护 `components/ui`，且不互相导入源码。随着两端都引入 shadcn 派生原语与登录页装饰件，出现了「逐字节相同的文件要不要上提到 `@animetracker/shared`」的反复抉择：

- `auth-divider.tsx`（16 行）与 `floating-paths.tsx`（78 行）在两端**逐字节相同**。
- `ui/empty.tsx`、`ui/input-group.tsx` 在两端各有独立副本。
- `TagChip.tsx`（标签胶囊样式）在两端各有独立副本：client 供番剧索引/详情页，admin 供番剧列表的标签筛选（2026-10-22 起管理端搜索卡片与 client `/anime` 索引页同构）。
- 但 `packages/shared/src/components/SubjectCard.tsx` 确是一个**被两端共用**的视觉组件（渲染 Subject 呈现）。

一句话口号式的「视觉件一律不放 shared」会与 `SubjectCard` 的事实冲突，因此需要一条能同时解释两者的边界。

## 决策

以**性质**而非「是否视觉」划界：

- **契约性视觉下沉 shared**：承载跨应用共享的**领域契约展示**的组件放 `packages/shared/src/components`（如 `SubjectCard` 渲染两端共用的 Subject 呈现）。判断标准是它表达的是**领域契约**，两端必须一致。
- **装饰件与 `ui` 原语层各端自持**：`components/ui/*`（shadcn 派生原语）以及纯装饰件（`auth-divider`、`floating-paths`、`empty`、`input-group`）**各端各持一份，允许逐字节重复，不上提 shared**。

## 备选方案

1. **RSC/共享库式：所有相同的视觉件都上提 shared。** 未采纳——为省约 94 行引入一条跨应用共享依赖面，两端原语会被耦合在同一版本下，任一端的 shadcn 定制都会牵动另一端。
2. **口号式：视觉件一律不进 shared。** 未采纳——与 `SubjectCard` 既在 shared 又正常被两端消费的事实冲突，规则一落地即被例外打破。
3. **按性质划界（采纳）。** 领域契约展示下沉，装饰件与原语层各端自持。

## 后果

**正面**

- 两端原语与装饰件可独立迭代，不必同步发布；`components/ui` 的定制自由度保留。
- `SubjectCard` 一类真正的跨端契约组件有明确归属，不再被「视觉件」这条粗规则误伤。

**代价与陷阱**

- 允许**逐字节重复**，同一处视觉 bug 可能在两端各修一次；修改 `auth-divider`/`floating-paths`/`TagChip` 这类副本时须两端同步。
- 判据是「是否表达跨端领域契约」，有主观空间：新组件到底该进 shared 还是各端自持，需要在 code review 时显式判断，不能默认。

**约束**

- 不因「两端相同」就把装饰件或 `ui/*` 原语上提 shared；上提必须能说明它承载的是跨端领域契约。
- 新增 shared 组件前先确认它不依赖单一应用的路由、全局 CSS 或专属运行时（`SubjectCard` 对 `react-router-dom` 的依赖是已知边界债务）。
