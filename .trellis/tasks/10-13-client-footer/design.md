# Design — 两端页脚接入 efferd footer-1

## 边界与非目标

- **改动面**：两端各新增一个本地 `footer` 组件 + 各处布局挂载一个子节点 + 两端测试同步 + 前端 spec 目录结构同步。
- **不改**：路由表结构（`router.tsx` 不动）、`packages/shared`、auth 外壳、admin 侧栏链、`components/ui` 既有原语。
- **不跑** `npx shadcn add @efferd/footer-1`（CLI 缺陷见仓库既有记录），按上游骨架手工落地。

## 上游骨架保留点

efferd `footer-1` 的 DOM 层级原样保留，只替换内容：

```
<footer mx-auto max-w-* *:px-4 *:md:px-6>
  <div flex flex-col gap-6 py-6>
    <div flex items-center justify-between>      ← Logo | 图标位
    <nav><ul flex flex-wrap gap-4 …>             ← 链接列表
  <div flex items-center justify-between border-t py-4 …>  ← 版权 | 署名
```

- 保留：`*:px-4 *:md:px-6`（子元素统一内边距）、上/下区 `justify-between`、`border-t` 分隔、`text-muted-foreground text-sm`、链接 `hover:text-foreground`、`flex-wrap` 响应式。
- 替换：`max-w-5xl` → 按应用实际宽度；`Logo className="h-4.5"` 保留该尺寸类（Tailwind v4 支持小数间距）。

## 组件契约

两端各一份，签名一致，**语义标签统一为 `<footer>`**（便于测试与 a11y）：

```
// client/src/components/footer.tsx
export function Footer(): JSX.Element
// admin/src/components/footer.tsx
export function Footer(): JSX.Element
```

- 内部导航数据为**模块级常量**（上游同为模块级 `navLinks`），不接收 props。
- client 用 `Link`（react-router-dom v7），admin 同为 `Link`。
- 无状态、无 hook、无副作用，所以不依赖 `AppPathContext` / `ShellUserContext`，两端可独立挂载与测试。

### client 页脚内容

| 位置 | 内容 |
|---|---|
| 上区左 | `<Logo className="h-4.5" />` 包在 `Link to="/"` 里（沿用 client `Logo`） |
| 上区右 | 单个 GitHub 图标按钮 → `https://github.com/zhaizzH`（`target="_blank" rel="noreferrer"`） |
| 中区 | `首页 /` 、`番剧索引 /anime`、`每周日程 /schedule` |
| 下区左 | `© {year} AnimeTracker` |
| 下区右 | 保留位置但不再放外链署名；改为 `AnimeTracker`（纯文本，无链接） |

### admin 页脚内容

| 位置 | 内容 |
|---|---|
| 上区左 | `Logo` → `Link to="/dashboard"`（**新复制** `admin/src/components/logo.tsx`，见下） |
| 上区右 | 同 client：GitHub 图标按钮 → `https://github.com/zhaizzH` |
| 中区 | 复用 `ADMIN_NAV_ITEMS`（`/dashboard`、`/subjects`、`/users`、`/import`、`/logs`、`/agent-config`、`/agent-chat`）——直接 `import` 自 `@/components/app-sidebar`，避免导航定义分叉 |
| 下区左 | `© {year} AnimeTracker` |
| 下区右 | 同 client 纯文本 |

### Logo 复制（admin）

- 从 `client/src/components/logo.tsx` 复制为 `admin/src/components/logo.tsx`，导出 `Logo` 与 `LogoIcon` 两名与 client 一致，文件顶部注释注明「当前为 client 同款占位，待管理端自有图标后替换」。
- 属共享能力的**有意重复**：spec 规定两端不互相导入源码、各自维护组件副本（与 `components/ui` 同口径）。因此**不入** `packages/shared`。
- 复制后 admin 无 `Logo` 引用质量问题：`import { Logo } from '@/components/logo'`。

### 图标

- 不引入 `@efferd/github-icon` / `@efferd/x-icon`。用两端既有的 `lucide-react`：GitHub 图标用 `Github`。
- X 图标删除（用户确认）；仅留 GitHub。
- 按钮形态保留上游：`<Button asChild size="icon" variant="ghost"><a aria-label="GitHub" …>`。

## 挂载点与「不显示」的保证方式

原则：**挂在布局外壳内，让路由结构本身保证排除**，不做逐页条件判断。

### client

`AppShell`（topnav-shell 定稿后的形态）为「吸顶 `AppHeader` + children」的 flex column。挂载点二选一，**优先 B**：

- 方案 A：`AppShell` 内 `{children}` 之后加 `<Footer />`。
- **方案 B（选）**：`ClientLayout` 内、`<Outlet />` 之后加 `<Footer />`。

选 B 理由：`AppShell` 通过 `path`/`user` 注入、被测试直接复用（`shell.guards.test.tsx`），把页脚放进 `AppShell` 会让「外壳」承担页面级内容；且 B 天然与 `AIAssistantFloat` 的挂载位（`ClientLayout` 内、`user` 判断）在同一层级，语义一致。

- 需在 `ClientLayout` 给内容区加 `flex-1`（当前 `<main>` 无 `flex-1`，页脚下沉需要它），使不足一屏时页脚贴底。
- **`/agent` 例外**：`ClientLayout` 用 `useLocation()` 判断 `pathname === '/agent'` 时不渲染 `<Footer />`。这是本任务**唯一**的路径判断，理由是该页是 `h-[calc(100vh-…)]` 全高对话页，页脚会撑出滚动条（用户已确认不显示）。

### admin

`AdminLayout` 内容区现为 `<div className="min-w-0 flex-1 p-4 md:p-6"><Outlet /></div>`。改为：

```
<SidebarInset>
  <header …/>
  <div class="flex min-w-0 flex-1 flex-col">
    <div class="flex-1 p-4 md:p-6"><Outlet /></div>
    <Footer />
  </div>
</SidebarInset>
```

- 外层加 `flex flex-col` + 内容 `flex-1`，保证页脚下沉；内边距保留在内容 div 上，页脚自持内边距（对齐上游 `*:px-*`）。
- **`/agent-chat` 例外**：`AdminLayout` 用 `useLocation()` 判断 `pathname === '/agent-chat'` 时不渲染 `<Footer />`。
- admin 404 与 `/login` 本就在 `AdminLayout` 之外，无需处理。

### 「不显示」清单（由结构保证 + 两处显式判断）

| 页面 | client | admin | 保证方式 |
|---|---|---|---|
| 404 | 不显示 | 不显示 | 路由在布局之外 |
| `/login` 等认证页 | 不显示 | 不显示 | 路由在布局之外 |
| `/agent` / `/agent-chat` | 不显示 | 不显示 | 布局内路径判断 |
| 其余布局内页面 | 显示 | 显示 | 默认 |

## 宽度对齐

- **client**：各页宽度**并不统一**（`Home`/`AnimeIndex`/`Schedule`/`MyCollections`/`Agent` 为 1400，`SubjectDetail` 为 1280，`Profile` 为 720）。因此页脚**与外壳顶栏对齐**（`app-header` 的 `nav` 用 `mx-auto … max-w-[1400px] px-4 md:px-6`），而不是逐页对齐——顶栏与页脚作为外壳上下框线共用同一 1400 节奏，页面可窄于它。
  - 页脚 `className="mx-auto max-w-[1400px] *:px-4 *:md:px-6"`。
  - 注：上游用的 `max-w-5xl`（1024）与项目不一致，取 1400，**这是对上游的有意偏离**。
- **admin**：内容区无统一 `max-w`（`AdminLayout` 只给 `p-4 md:p-6`），管理端表格类页面需要全宽，**不给 admin 页脚加 `max-w`**，只保留 `*:px-4 *:md:px-6`；横向与内容区对齐。
  - 结论：admin 页脚宽度 = `AdminLayout` 内容区宽度，保持管理端全宽语义（R7 待定项结论：不对齐 client 的 1400）。

## 布局下沉的正确性

现两端外壳：
- client：`AppShell` → `<div className="flex min-h-svh w-full flex-col">`。加 `flex-1` 到 `<main>` 后，短页面时 main 撑开、footer 贴底；长页面时正常文档流。`min-h-svh` 已由 topnav-shell 提供。
- admin：`SidebarInset` 在 `SidebarProvider` 内已有视口高度（admin 侧栏布局），加 `flex flex-col` + `flex-1` + `Footer` 后，同一机制生效。**需在实现时验证 `SidebarInset` 的高度链确实成立**（`h-svh`/`min-h-svh` 或 `flex-1`）；若不成立，退路是在外层 div 加 `min-h-svh`。

## 测试策略

不新增测试文件，改既有：

- client `src/test/shell.guards.test.tsx`：补充「布局内页面存在页脚」「404 / 认证页无页脚」「`/agent` 无页脚」断言。若该文件在 topnav-shell 中已被改写，按其定稿结构接入。
- admin `src/layouts/AdminLayout.test.tsx`：`TestApp` 已用 MemoryRouter 覆盖 `/subjects` 等路径，补「内容页有页脚」「`/agent-chat` 无页脚」；admin 404 仍在布局外，可在同文件补一条顶层 `*` 断言或沿用既有守卫测试口径。
- 断言用语义角色（`screen.getByRole('contentinfo')`，`<footer>` 的隐式 role）而非 `data-testid`，与仓库既有 `getByRole` 风格一致。

## 实现前核对结论（topnav-shell 落地后已确认）

- **topnav-shell 已提交**（`b5e39780`）。`AppShell` 现为 `flex min-h-svh w-full flex-col` + `<AppHeader />` + children；`ClientLayout` 的 `<main>` **仍无 `flex-1`** → 方案 B 需自行补。
- **`AppHeader` 用 `sticky top-0 z-50`**（非 `fixed`），占据文档流高度，不留内容偏移问题。
- **admin `SidebarInset` 高度链成立**：`SidebarProvider` 外层 `group/sidebar-wrapper` 为 `flex min-h-svh w-full`，`SidebarInset` 自身为 `relative flex w-full flex-1 flex-col`，其内内容 div 已含 `flex-1` → admin 侧**只需在内容 div 后追加 `<Footer />`**，无需重排高度，也无需补 `min-h-svh`。
- **admin 内容区无 `max-w`**（仅 `p-4 md:p-6`），确认 design 的「admin 不对齐 1400」结论。
- **`ADMIN_NAV_ITEMS` 为 `as const`，7 项**；`isAdminNavItemActive` 用 `pathname === path` 精确匹配（与 client 的 `isNavItemActive` 前缀语义不同）——页脚若做高亮需用 admin 自己的判据。

## 测试改动契约（重要）

页脚复用 `ADMIN_NAV_ITEMS` 后，admin 每个导航链接会出现**两次**（侧栏 + 页脚）。`AdminLayout.test.tsx` 现有断言：

- `screen.getByRole('link', { name: '看板' })` / `'用户管理'` / `'导入管理'` / `'日志审计'` / `'Agent 配置'` / `'Agent 对话'` —— 均为**单数** `getByRole`，多匹配会抛错。
- `'番剧管理'` 已是 `getAllByRole(...)[0]`（既有先例）。
- 「navigates through the existing route」用例 `user.click(screen.getByRole('link', { name: '看板' }))` 同样会抛错。

→ 实现时必须把这些断言改为 `getAllByRole(...)[0]`（沿用文件内既有写法）。client 侧用 `linkCount()`（`queryAllByRole`）与 `toBeGreaterThan(0)`，天然兼容，无需改动计数用例。

## 兼容性与风险

- **`h-4.5`**：Tailwind v4 支持任意小数间距；若无该工具类，退化为 `h-4` 或 inline style。
- **admin 测试断言收敛**：见上「测试改动契约」，属必要的测试同步而非功能回归。
- **`ADMIN_NAV_ITEMS` 复用**：admin 页脚直接 import 该常量 → 页脚与侧栏导航永不脱钩；副作用是 `app-sidebar` 被页脚引入，若未来拆 admin 导航定义需同步。可接受。
- **admin 页脚导航与侧栏冗余**：管理端侧栏常驻，页脚再列一遍导航在 UX 上属冗余；但为满足「保留 efferd 骨架」而保留 `nav` 段。若后续认为冗余，删除页脚 `nav` 段是局部改动。
- **行尾**：改 `.trellis/spec/frontend/*.md` 时保持混合 CRLF/LF，用定点 Edit，勿整文件 Write。
- **回滚**：删除两个 `footer.tsx`、还原两处布局挂载与两处测试断言即可，无数据/状态副作用。
