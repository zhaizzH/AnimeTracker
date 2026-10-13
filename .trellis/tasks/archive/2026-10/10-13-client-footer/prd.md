# 两端页脚接入 efferd footer-1

## Goal

在 `frontend/client` 与 `frontend/admin` 接入 `npx shadcn@latest add @efferd/footer-1` 形态的页脚，让两端内容区底部有统一收尾；同时明确**哪些页面不显示页脚**（404、登录/注册/找回密码/重置密码/邮箱验证等占位整屏页），并将 efferd 上游的占位内容本地化为 AnimeTracker 自己的内容。

## Background

用户请求「讨论页脚使用 `npx shadcn@latest add @efferd/footer-1`，并考虑在哪些页面不应该显示，如 404 页等」。

实际拉取 `https://efferd.com/r/new-york/footer-1.json` 后确认：`@efferd/footer-1` **不是通用页脚**，而是 efferd 官方营销站页脚，产出单个 `Footer` 组件 + 依赖 `@efferd/logo`、`@efferd/github-icon`、`@efferd/x-icon`。其内容全部是占位：

- `navLinks`：`Features` / `Blog` / `About` / `Contact` / `Licence` / `Privacy`，**全部 `href="#"`**。
- `socialLinks`：X 与 Github 图标，**`href="#"`**。
- 版权：`© {year} efferd`。
- 右下角：`Built by Shaban`（`https://x.com/shabanhr` + `https://github.com/shabanhr.png` 外链）。
- 宽度 `mx-auto max-w-5xl`，`Logo` 类名 `h-4.5`。

因此**不能字面入库**——直接 `add` 会把 efferd 署名、死链与外链头像放进 AnimeTracker。已与用户确认三点：

1. **任务关系**：新建独立任务（本任务），排在在飞的 `10-13-client-topnav-shell`（用户端去侧栏改顶栏）之后，PRD 中写明顺序依赖，避免两个任务同时改 `AppShell` / `ClientLayout`。
2. **范围**：client 与 admin **两端都加**。
3. **内容处理**：**保留 efferd 的 DOM/样式骨架，仅替换文字与外链**（最小改动），便于后续与上游对照。

现状关键事实（勘察结论）：

- client 路由：`src/router.tsx`。`/login`、`/register`（重定向）、`/verify-email`、`/forgot-password`、`/reset-password`、`*`（404）均在 `ClientLayout` **之外**，不渲染 `AppShell`；`AppShell` 结构为「吸顶 `AppHeader` + children」。
- admin 路由：`src/router.tsx`。`/login` 与 `*`（404）在 `AdminLayout` **之外**；`AdminLayout` 为 `SidebarProvider + AppSidebar + SidebarInset`，内容区 `<div className="min-w-0 flex-1 p-4 md:p-6"><Outlet /></div>`。
- 两端页面**各自持有**容器宽度与内边距（client 多为 `mx-auto w-full max-w-[1400px] p-6`；admin 无统一 `max-w`，`AdminLayout` 统一 `p-4 md:p-6`）。
- 全高页面：client `pages/Agent.tsx` 用 `h-[calc(100vh-5.5rem)]`，admin `pages/AgentChat.tsx` 用 `flex h-[calc(100vh-120px)]`。页脚若进入外壳的正常文档流会把这俩撑出视口滚动条，需在 design 中定策略。
- 仓库无任何既有 `Footer` 组件（`grep` 命中的都是 `DialogFooter`/`CardFooter` 等 UI 原语与 `auth-shell` 的 slot 参数）。

## Requirements

### R1 顺序依赖（硬约束）

- 本任务必须在 `10-13-client-topnav-shell` **完成并提交后**开始实现。
- 理由：该任务正在重写 client `AppShell` / `ClientLayout` / 页面内边距，本任务的挂载点与全高策略都依赖其最终形态。
- 开工前先确认该任务已提交（`AppShell` 无 `Sidebar*` 引用、`app-header` 吸顶顶栏生效）。

### R2 组件形态与归属

- 两端各自新增**本地**页脚组件，`client/src/components/footer.tsx` 与 `admin/src/components/footer.tsx`（若 topnav 后 client 目录结构变化，以当时约定为准）。
- 组件保持 efferd footer-1 的 DOM 骨架与 Tailwind 类形态：上区「`Logo` + 社交图标」、中区 `nav` 链接列表、下区「版权 + 署名」用 `border-t` 分隔。
- 不引入 efferd 的 `github-icon` / `x-icon` 图标组件作为必需依赖；社交图标若保留，用仓库已有的 `lucide-react` 或两端各自的 `icons/` 约定实现（见 design）。
- client 与 admin 不互相导入源码；两端各自维护副本（与 `components/ui` 一致）。

### R3 内容本地化（保留骨架，最小改动）

- **\(已被用户后续决定覆盖\) `nav` 段整体删除**：两端顶栏/侧栏已承载导航，页脚再列一遍属重复（见 R7 决策项）。
- `navLinks` 由 `href="#"` 替换为**真实路由**；client 用 React Router `Link`，admin 用管理端路由。（若保留 nav 段时的方案；最终已删段。）
- `Logo` 复用两端既有 `components/logo.tsx`，点击回到各自首页（client `/`，admin `/dashboard`）。
- 版权改为 `© {year} AnimeTracker`。
- 删除 `Built by Shaban` 外链与其 github 头像 `<img>` 外链（保留 efferd 的「右侧署名位」布局，但内容改为项目自身文案或留空，见 R7 待定项）。
- 社交图标：若项目无真实社交账号，则移除社交图标区（或保留结构但置为站内链接），**不得留 `href="#"` 死链**。

### R4 显示与隐藏范围（核心诉求）

- **显示**：client 的 `ClientLayout` 内页面（`/`、`/anime`、`/schedule`、`/subject/:id`、`/my-collections`、`/agent`、`/profile`）与 admin 的 `AdminLayout` 内页面。
- **不显示**（两端一致）：404 页、`/login`、注册/邮箱验证/忘记密码/重置密码等**占位整屏页**——这些页面在路由上位于布局外壳之外，天然不渲染。
- **全高页面例外**：client `/agent` 与 admin `/agent-chat` 为占满视口高度的对话页，页脚会引入溢出滚动，**这两页不显示页脚**（已定，见 R7）。
- 实现上优先**把页脚挂在布局外壳内**（client `AppShell` / `ClientLayout` 之内、admin `AdminLayout` 内），使「不显示」由路由结构保证，而非逐页判断。

### R5 布局与对齐

- 页脚宽度须与各页内容容器对齐：client 页面为 `max-w-[1400px]`（上游 footer-1 是 `max-w-5xl`，需按项目实际调整）；admin 内容区无统一 `max-w`，需按 design 决定的方案处理。
- 外壳需保证「内容不足一屏时页脚下沉到视口底部、内容超一屏时页脚在文档末尾」——不要太短页面悬空、也不要遮住内容。
- 两端现有外壳均为 flex column（client `flex min-h-svh flex-col`；admin `SidebarInset` 内为 `flex-1` 内容列），预期待改动集中在「加一个页脚子节点 + 内容区 `flex-1`」。

### R6 测试

- client：现有 `src/test/shell.guards.test.tsx` 等相关测试需在当前外壳断言上补页脚存在性；404/登录页断言**不出现**页脚。
- admin：`src/layouts/AdminLayout.test.tsx` 同口径补充。
- 不新增测试文件，除非 design 判断必要。

### R7 决策项（已在 design 收敛）

- `Built by Shaban` 位 → **删除 X 外链**；GitHub 图标替换为 `https://github.com/zhaizzH`；底行保留 `© {year} AnimeTracker`。
- 页脚 `nav` 段 → **两端整体删除**（用户决定）：client 顶栏已有公开项、admin 侧栏常驻，页脚再列导航重复。
- 社交图标 → **仅保留 GitHub**（无 X 账号）。
- `/agent` 与 `/agent-chat` 全高对话页 → **不显示页脚**（用户在 `ClientLayout` / `AdminLayout` 内按路径显式排除）。
- admin 页脚宽度 → **不对齐 client 的 1400，保持管理端全宽**（admin 内容区本就无 `max-w`）。
- admin `Logo` → **从 client 复制** `logo.tsx`，注明待管理端自有图标后替换。

## Acceptance Criteria

- [ ] 顺序依赖满足：`10-13-client-topnav-shell` 已提交，本任务在其之上开工。
- [ ] client 与 admin **分别**存在本地 `footer` 组件，无跨应用导入；`frontend/packages/shared` 未被写入 UI 组件。
- [ ] 页脚 DOM 保持 efferd footer-1 骨架的上/下两段（上：Logo + 右侧图标位；下：`border-t` 分隔的版权行）；**中段 `nav` 已删除**，两端导航不重复。
- [ ] 页脚内**无 `href="#"` 死链、无 efferd 署名、无 `x.com/shabanhr` / `github.com/shabanhr.png` 外链**；版权为 AnimeTracker。
- [ ] client 7 个 `ClientLayout` 内页面均显示页脚；404、`/login`、`/verify-email`、`/forgot-password`、`/reset-password` 均**不显示**页脚。
- [ ] admin `AdminLayout` 内页面均显示页脚；admin 404 与 `/login` 均**不显示**页脚。
- [ ] 短内容页面（如 404 之外的普通页）页脚贴视口底部无悬空；长内容页面页脚位于文档末尾，不被内容遮挡。
- [ ] 页脚宽度与所在页内容容器对齐（client 与 `max-w-[1400px]` 对齐；admin 结论写入 design 并落地）。
- [ ] R7 五项决策在 design 中已给出结论并落地。
- [ ] 两端 `npm run typecheck` 通过；受影响 workspace `npm test` 通过；交付型变更运行 `npm run build` 通过。
- [ ] 浏览器免登录验证：client 首页滚动到底有页脚、`/login` 与任意错误路径无页脚；admin 同口径（登录态受限时以源码 + 测试为准，沿用既有「免登录优先」原则）。
- [ ] 如产生前端 spec 影响（新增本地组件、目录结构），同步 `.trellis/spec/frontend/*.md` 且**不整文件改写行尾**（保持原有混合 CRLF/LF）。

## Notes

- 明确的**非目标**：不重跑 `npx shadcn add @efferd/footer-1`（其 CLI 缺陷见仓库既有记录：`from "cn"` 导入、非 forwardRef Button、React 19 语法），改为按骨架手工落地；不改两端路由结构（除为页脚必要的挂载点）；不做响应式页脚的新设计，沿用 footer-1 已有的 `flex-wrap` 行为。
- 本任务与 `10-12-frontend-spec-drift-audit` 无冲突，后者已提交。
- 任务类型：两端各一个本地组件 + 两处布局挂载 + 两端测试同步，属**复杂任务**（需 `design.md` + `implement.md`），跨两个应用、含待定项收敛与全高页面策略决策。
