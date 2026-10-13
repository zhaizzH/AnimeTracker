# Design — 条目详情页信息栏改用 efferd contact-1 卡片

## 边界与非目标

- **改动面**：client 新增 2 个本地组件（`full-width-divider`、`subject-info-cards`）+ `SubjectDetail.tsx` 一处替换 + 1 个新测试 + 前端 spec 目录结构补登记。
- **不改**：`packages/shared`（不加 UI 组件、改数据）、路由表、评分进度条 / 简介 / 标签 / 关联条目 / 剧集表格等本页其它区块、admin 端。
- **不跑** `npx shadcn add @efferd/contact-1`（会带入 `IconPlaceholder` 与对 `@efferd/full-width-divider` 的 registry 依赖），按上游骨架手工落地。

## 上游骨架保留点

efferd `contact-1`（`https://efferd.com/r/new-york/contact-1.json`）的 DOM 原样保留，只替换内容：

```
<div className="relative">                     ← 定位容器（divider 的参照系）
  <FullWidthDivider position="top" />
  <div className="grid gap-px overflow-hidden bg-border px-px md:grid-cols-3">
    <div className="flex items-center gap-3 bg-background p-2 shadow-xs">
      <div className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-muted/50
                      [&_svg]:size-4 [&_svg]:text-muted-foreground">  ← 图标位
      <div className="flex flex-col gap-y-0.5">
        <h2 className="font-heading text-sm">…</h2>      ← 本项目改为 dt
        <p className="text-muted-foreground text-xs">…</p> ← 本项目改为 dd
  <FullWidthDivider position="bottom" />
```

- 保留：`relative` 定位容器、`gap-px` + `bg-border` + `px-px` 的**分隔线网格效果**、卡片 `bg-background p-2 shadow-xs`、图标框 `size-12 rounded-lg bg-muted/50` 与 `[&_svg]:size-4 [&_svg]:text-muted-foreground`、标题 `font-heading text-sm`、值 `text-muted-foreground text-xs`、`md:grid-cols-3`。
- 替换/删除：上游 `h2` 区块标题（**删除**，见 D2）、`IconPlaceholder`（**换真图标**）、上游「标题+值」两项数据（**换本页 5 字段**）。

## 决策项（已收敛）

| # | 决策 | 结论 | 理由 |
|---|---|---|---|
| D1 | 列数与分隔线形态 | **严格还原上游**：`md:grid-cols-3`，移动端单列（`grid` 默认 1 列）；上下各一条分隔线 | 用户选定；不沿用原 `grid-cols-2` |
| D2 | 区块标题 | **不加标题** | 原 `dl` 本无标题；加「条目信息」会与「简介/标签/剧集」标题同级且语义空泛 |
| D3 | 代码落点 | **抽本地组件** `components/subject-info-cards.tsx` | 图标映射 + 字段拼装独立可测，详情页不堆长 |
| D4 | `dt`/`dd` 语义 | **保留**：网格项为 `<dt>`（标题）/`<dd>`（值），外层仍 `<dl>` | 语义不退化；`<dl>` 允许 `<div>` 包裹 `dt+dd` 分组（HTML5 合法）。上游把每项标题写成 `<h2>` 其实不合语义 |
| D5 | `FullWidthDivider` | **本地实现该组件**（原样移植上游），但本页以 `contained` 模式使用 | 见下行偏差说明 |
| D6 | 图标 | `lucide-react`：排名 `Trophy`、集数 `ListVideo`、放送 `CalendarDays`、类型 `Tag`、收藏 `Star` | 项目已装 lucide，`components.json iconLibrary: lucide` |
| D7 | 未映射 `type` 显示 | **保留 `未知(n)`**（原始码），与缺值的 `—` 区分 | 见「占位符约定」；`—` 无法表达「有值但未知」，原始码是可诊断信号 |

### D5 偏差说明（重要）

上游 `FullWidthDivider` 默认 `full-bleed`（`left-1/2 w-screen -translate-x-1/2`），其前提是**自身容器在视口中水平居中**（contact-1 外层是 `mx-auto max-w-4xl`）。本页的内容列处于「封面 aside + 内容」的两列 flex 中，**不在视口中心**：

- 1440 视口下，内容列中心约在 796px（视口中心 720px），`w-screen` 的出血线会右移到 1516px，**超出版口 76px → 产生横向滚动条**。这违反 PRD R5（不得横向溢出）。
- 该组件把 X 轴出血与 Y 轴定位（`-top-px` / `-bottom-px`）绑在同一个 `relative` 参照系上；「X 相对视口居中、Y 相对卡片块」在本布局下无法同时满足。

故本页以 `contained`（`data-contained=true` → `inset-x-0 w-full`）落地：**分隔线与卡片网格同宽**，视觉上仍是「卡片网格上下各一条线」，且无横向溢出。

保留双模式：本地 `full-width-divider.tsx` **完整移植上游两端模式**（`contained` prop 默认 `false`），仅调用处传 `contained`；若日后把该区块提升为整页容器宽的独立行（视口居中），把调用改回默认即得真出血，无需改组件。

## 占位符约定（保留 `未知(n)`）

本区块存在两种「无正常显示值」的情形，**语义不同，不得统一**：

| 情形 | 例 | 显示 | 依据 |
|---|---|---|---|
| **缺值** — 数据本身没有 | `rank: 0`（未上榜）、`airDate: null`（未定档） | `—` | 与 `formatDate` 既有返回一致（`format.ts:5,7`：空/非法值 → `'—'`） |
| **值存在但映射缺失** — 后端枚举新增，客户端 `SUBJECT_TYPE_LABEL` 未登记 | `type: 9` | `未知(9)` | 保留原始码是可诊断信号 |

- 保留 `未知(n)` 的理由：① `—` 语义是「没有」，无法表达「有值但未知」；② `SUBJECT_TYPE_LABEL` 是**客户端**对**后端枚举**的映射，后端加类型时原始码是唯一线索，抹成 `未知`/`—` 会让映射缺口对开发者隐形；③ 只读详情页，`未知(9)` 是「待补映射」信号而非用户可犯的错误。
- **不做**：把 `未知(9)` 改成 `未知`（丢线索）或 `—`（混淆「缺值」与「未知」两种情形）。
- 测试须同时锁住两种情形（见「测试」）。
- **spec 候选**：该「缺值 `—` / 未映射 `未知(n)`」区分是可跨页面复用的展示约定，收尾（Phase 3.3）时考虑提升进 `.trellis/spec/frontend/component-guidelines.md`。

## 响应式加固

本区块处在「封面 aside + 内容列」的两列 flex 内，**可用宽度随视口成阶梯变化**，须显式兜住：

| 视口 | 页面形态（`SubjectDetail.tsx:39`） | 内容列可用宽（估算） | 卡片列数 |
|---|---|---|---|
| < 768px | 上下堆叠（`flex-col`），aside 全宽 | ≈ 视口 − 48（`p-6`） | **1** |
| 768–1024 | 左右两列，aside 200px | 768 时 ≈ 488 | **3** |
| ≥ 1024 | 左右两列，内容列封顶 `max-w-[920px]` | ≤ 920 | **3** |

加固点：

1. **窄屏单列继承上游**：`grid` 默认 1 列，卡片上下堆叠；`gap-px` 的 1px 分隔在单列下自然变成行间分隔线，与桌面竖分隔视觉一致，无需额外样式。
2. **文本列 `min-w-0`**：flex 子项默认 `min-width:auto`，长值（如超长类型名、大数值）会把卡片撑宽并顶破网格。文本列加 `min-w-0`，值允许换行（`break-words`），**不截断**（截断会静默丢信息）。
3. **图标框 `size-12 shrink-0` 保持不动**：上游已 `shrink-0`，窄屏卡片内不会挤压图标；`size-12` 在单列下留白略大但可接受，**不做响应式缩放**（避免偏离上游形态）。
4. **`md:grid-cols-3` 在 768px 最窄档的可读性**：内容列 ≈ 488px ÷ 3 ≈ 162px/卡，减 `p-2`(16) − 图标 48 − `gap-3`(12) ≈ 86px 文本宽；本项目标签均 ≤ 3 字、值多为短串，可容纳。**不加 `min-w` 硬约束**，靠第 2 条的 `min-w-0` + 换行兜底。
5. **分隔线不随视口出行**：`contained` 模式 `inset-x-0 w-full`，宽度恒等于卡片网格，任何断点下都不会横向溢出（这是 D5 的直接收益）。
6. **验收断点**：375 / 640 / 768 / 1024 / 1440 逐一确认无横向滚动条、卡片不溢出、5 项信息完整可读。

> 无交互元素（卡片不可点击），因此无触控目标尺寸（44px）约束；图标一律 `aria-hidden="true"`，语义由 `<dl>/<dt>/<dd>` 承载。

## 组件契约

### `client/src/components/full-width-divider.tsx`

上游逐字移植（唯一差别：无——本项目 `cn` 已在 `@/lib/utils`，别名正确）：

```tsx
type FullWidthDividerProps = React.ComponentProps<"div"> & {
  contained?: boolean;
  position?: "top" | "bottom";
};
export function FullWidthDivider({ className, contained = false, position, ...props }: FullWidthDividerProps)
```

- 纯展示、`aria-hidden="true"`，无状态无 hook。
- **不得**新增 `@efferd/*` registry 依赖。

### `client/src/components/subject-info-cards.tsx`

```tsx
import type { LucideIcon } from 'lucide-react';
import { CalendarDays, ListVideo, Star, Tag, Trophy } from 'lucide-react';
import { formatDate } from '@shared';
import { cn } from '@/lib/utils';
import { FullWidthDivider } from '@/components/full-width-divider';

type Props = {
  rank: number;
  eps: number;
  airDate?: string | null;
  type: number;
  collectionTotal: number;
  className?: string;
};

export function SubjectInfoCards({ rank, eps, airDate, type, collectionTotal, className }: Props)
```

- 接收 5 个**标量**（不接收整个 `Subject` 对象），与 `SubjectDetail` 现有字段一一对应（`SubjectListItem`：`rank: number`、`eps: number`、`airDate?: string | null`、`type: number`、`collectionTotal: number`），便于测试构造、且不锁死 shared 类型。
- 内部模块级常量：
  - `SUBJECT_TYPE_LABEL: Record<number, string>`（从 `SubjectDetail.tsx` **移入**本组件，页面不再需要该常量）。
  - 图标 + 字段拼装数组，项类型 `{ label: string; value: string | number; Icon: LucideIcon }`。
- 值兜底：`放送` → `formatDate(airDate)`；`类型` 未登记 → `` `未知(${type})` ``；`收藏`/`集数` → 数字原样（含 `0`）；**`排名` → `rank > 0 ? rank : '—'`**。
  - ⚠️ 现有代码是 `sub.rank || '—'`。改为显式 `rank > 0`：**行为等价**（`rank: number`，合法值仅正整数或 0），同时避开 spec 明令的「统计值 `0` 不得以 truthiness 判空」写法。本处 `0` 仍显示 `—`，属**保持改动前行为**（AC 要求），非新规则。
- 根节点：`<div className={cn('relative', className)}>`；页面以 `className="mt-4"` 提供上间距（沿用原 `dl` 的 `mt-4`）。
- 渲染：`<dl>` 承载网格，每张卡片 `<div>` 包裹 `<dt>`/`<dd>`；文本列 `min-w-0`、值 `break-words`（见「响应式加固」第 2 条）；图标 `aria-hidden="true"`。
- 无状态、无 hook、无副作用、无网络 → 可直接单测。

### `client/src/pages/SubjectDetail.tsx` 改动

替换 62–75 行的 `<dl>…</dl>`：

```tsx
<SubjectInfoCards
  className="mt-4"
  rank={sub.rank}
  eps={sub.eps}
  airDate={sub.airDate}
  type={sub.type}
  collectionTotal={sub.collectionTotal}
/>
```

- 删除页面内 `SUBJECT_TYPE_LABEL`（移入组件）；`SUBJECT_TYPE_LABEL` 若页面别处未用则一并删除导入。
- 其余区块与 `import`（`Badge`、`Table*`、`Skeleton`、`formatDate` 等）不动；`formatDate` 页面是否仍用需确认（`剧集` 表格未用，`放送` 已移入组件）——若页面不再引用则删该导入。

## 测试

- 新增 `client/src/test/subject.info-cards.test.tsx`（沿用 `src/test` 集中式现状，与 `home.hero.test.tsx` 同风格）。
- 用例：
  1. 5 个标签全部渲染（排名/集数/放送/类型/收藏）且为 `<dt>`；值在对应 `<dd>`。
  2. **占位符两情形**：`rank: 0` → `—`、`airDate: null` → `—`（缺值）；`type: 9` → `未知(9)`（未映射，保留原始码）。二者不得被合并成同一种显示。
  3. 网格为 `<dl>`（语义保留）；`eps: 0` / `collectionTotal: 0` 原样显示 `0`，不被吞成 `—`。
- 不引入网络/QueryClient：组件无 hook。

## 兼容性 / 回滚

- 纯前端展示层改动，无接口/数据契约变化；不涉共享包 → 两端构建互不影响。
- 回滚：删除 2 个新组件与 1 个测试，`git checkout -- client/src/pages/SubjectDetail.tsx` 即可回到原 `dl`。

## 规范影响

- `.trellis/spec/frontend/directory-structure.md`：在「client 活代码组件」登记处补一句（新本地组件 + 其为 efferd 骨架落地）。
- **行尾保护**：frontend spec 文件为混合 CRLF/LF，`Edit` 会整文件重写为 LF 造成大 diff。改用 `python -I` 按字节 `replace` 目标子串（保留其余行尾），完成后 `git diff --stat` 确认只有目标行变动。

## 待定 / 已排除

- **不做**：把卡片区块提升为整页宽的独立行（会改变页面两列结构）——仅在此需求出现时再议，届时 D5 可回归真出血。
- **不做**：响应式列数的新设计、卡片点击跳转、图标以外的交互。
