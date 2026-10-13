# 条目详情页信息栏改用 efferd contact-1 卡片

## Goal

将 client 条目详情页（`/subject/:id`）中现有的一行 `dl` 栏目信息，改为 `npx shadcn@latest add @efferd/contact-1` 形态的卡片网格：每项信息一张卡片，左图标、右「标题 + 值」。

现状（`frontend/client/src/pages/SubjectDetail.tsx:62-75`）：

```
<dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-sm md:grid-cols-3">
  [排名 sub.rank] [集数 sub.eps] [放送 formatDate(sub.airDate)]
  [类型 SUBJECT_TYPE_LABEL[sub.type]] [收藏 sub.collectionTotal]
</dl>
```

目标态：同一批字段以 contact-1 的卡片骨架呈现（`grid md:grid-cols-3` + 分隔背景 + 图标位 + 标题/值两行）。

## Background

用户请求：「`http://localhost:5173/subject/115` 下显示的栏目信息 `dl`，改为使用 `npx shadcn@latest add @efferd/contact-1` 的每个卡片显示」。

已拉取 `https://efferd.com/r/new-york/contact-1.json` 确认上游形态：

- 单文件 `registry/blocks/contact/1/contact.tsx`，导出 `Contact` 组件（无 props，数据模块级常量内联）。
- 结构：`h2` 标题 → 相对定位容器 → `FullWidthDivider position="top"` → `grid gap-px overflow-hidden bg-border px-px md:grid-cols-3` → 每卡片 `flex items-center gap-3 bg-background p-2 shadow-xs` → 图标框（`size-12 rounded-lg bg-muted/50`，`[&_svg]:size-4`）→ 文本列（`h2.font-heading.text-sm` + `p.text-muted-foreground.text-xs`）→ `FullWidthDivider position="bottom"`。
- registry 依赖：`@efferd/full-width-divider`（额外一个文件）。
- **卡片网格是硬编码 3 列**（`md:grid-cols-3`），且每项标题/值两行。
- **不兼容点**（同仓库既有记录）：产出文件用 `IconPlaceholder` 多图标库占位组件（本项目仅装 `lucide-react`，须换真图标）；数据结构是「标题+值」两项，而本项目现有字段是 5 项「标签+原始值」。

勘察结论：

- client 目前**没有** `full-width-divider` 与 `IconPlaceholder`；`cn` 已存在于 `@/lib/utils`（本项目 `components.json` 的 utils 别名正确，不存在仓库记录的 `from "cn"` 问题）；`font-heading` 已在 auth 页使用，字体层已就绪。
- 本页字段值与既有语义：`排名`（`sub.rank || '—'`）、`集数`（`sub.eps`）、`放送`（`formatDate(sub.airDate)`）、`类型`（`SUBJECT_TYPE_LABEL`）、`收藏`（`sub.collectionTotal`）。

## Requirements

### R1 展示形态

- 用 contact-1 的卡片网格骨架替换现有 `<dl>`，**保留 efferd 的 DOM/样式形态**：`gap-px` + `bg-border` + `px-px` 的分隔线效果、`bg-background` 卡片、`p-2` 内边距、左上图标框（`size-12 rounded-lg bg-muted/50`）、右侧「标题（`text-sm`）+ 值（`text-xs text-muted-foreground`）」。
- 图标用仓库既有 `lucide-react`，**不引入** `IconPlaceholder`（多图标库占位组件）。

### R2 字段映射（5 项 → 卡片）

| 卡片标题 | 值 | 建议图标 |
|---|---|---|
| 排名 | `sub.rank \|\| '—'` | `Trophy` / `TrendingUp` |
| 集数 | `sub.eps` | `ListVideo` / `Layers` |
| 放送 | `formatDate(sub.airDate)` | `CalendarDays` |
| 类型 | `SUBJECT_TYPE_LABEL[sub.type]` | `Tag` |
| 收藏 | `sub.collectionTotal` | `Star` / `Users` |

> 图标最终选定以 design 为准，本节只定语义。

### R3 数值语义不得退化

- 现有 `dl` 的 `dt`（标签）与 `dd`（值）是**语义化定义列表**。改为 contact-1 骨架后，`dt`/`dd` 会消失；**必须保证信息语义不丢失**（标题/值仍以合适语义标签或 aria 表达），不得只靠视觉呈现。
- 「排名」在无数据时显示 `—`、「类型」未知时显示 `未知(n)`，这两条现有兜底逻辑须保留。

### R4 依赖处理

- 不直接跑 `npx shadcn add @efferd/contact-1` 落库（会带入 `IconPlaceholder` 与对 `@efferd/full-width-divider` 的 registry 依赖）。按 design 结论在**本页**或**本地组件**中手工实现骨架。
- 若采用 `FullWidthDivider`，须在本项目内本地实现（不新增 efferd registry 依赖）；若不采用（本项目该区块不需要全宽出血分隔线），须在 design 中说明理由。

### R5 响应式与宽度

- 现有 `dl` 为 `grid-cols-2 md:grid-cols-3`；**已定沿用上游 `md:grid-cols-3`（移动端单列）**，不保留原 2 列断点。
- 卡片所在区域宽度沿用页面现有布局（`md:max-w-[920px]` 内容列），不得因改动撑破移动端。**上游默认 full-bleed 分隔线在本两列布局下会横向溢出，本页须用 `contained` 模式**（理由与取舍见 design D5）。

## Acceptance Criteria

- [ ] `/subject/115` 页面栏目信息以卡片网格呈现，形态与 efferd contact-1 一致（分隔线效果、图标框、标题/值两行），外层仍为 `<dl>`。
- [ ] 5 个字段（排名/集数/放送/类型/收藏）全部保留，值与改动前一致（含 `排名 0 → —`、`集数/收藏 0` 仍显示 `0`）。
- [ ] **占位符两情形不混淆**：缺值 → `—`（`rank 0` / `airDate null`）；未映射枚举 → `未知(n)`（保留原始码，如 `未知(9)`）。
- [ ] 无 `IconPlaceholder`、无 `href="#"`、无新增 efferd registry 依赖。
- [ ] `npm run typecheck -w client` 通过；受影响测试 `npm test -w client` 通过。
- [ ] **响应式**：375 / 640 / 768 / 1024 / 1440 五档均无横向滚动条、无卡片溢出；窄屏单列、`md` 起 3 列；长值换行不截断。
- [ ] 分隔线与卡片网格同宽（`contained`），不随视口横向出血。

## 决策结论（已与用户收敛）

| 主题 | 结论 |
|---|---|
| 卡片形态 | **严格还原上游**：`md:grid-cols-3`（移动端单列），卡片网格上下各一条分隔线 |
| 区块标题 | **不加**（原 `dl` 无标题，避免与「简介/标签/剧集」标题同级） |
| 响应式 | 窄屏单列、`md` 起 3 列；长值 `min-w-0` + 换行不截断；分隔线 `contained` 不出行（详见 design「响应式加固」） |
| 代码落点 | **抽本地组件** `client/src/components/subject-info-cards.tsx` |
| `dt`/`dd` 语义 | **保留**：外层仍 `<dl>`，卡片内 `<dt>`（标题）/`<dd>`（值） |
| `FullWidthDivider` | 本地移植上游组件（双模式），本页以 `contained` 模式落地以免横向溢出——偏差理由见 design D5 |
| 图标 | `lucide-react`：Trophy / ListVideo / CalendarDays / Tag / Star |

## Notes

- 明确的**非目标**：不改动评分进度条、简介、标签、关联条目、剧集表格等本页其它区块；不改 `subjectsApi` 数据结构；不把该卡片抽成跨应用共享组件；不引入 `IconPlaceholder` 或 `@efferd/*` registry 依赖。
- 任务类型：**复杂任务**（含依赖取舍、语义保留、响应式偏差决策），已产出 `design.md` + `implement.md`。
