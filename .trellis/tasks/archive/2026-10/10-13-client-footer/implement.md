# Implement — 两端页脚接入 efferd footer-1

## 前置门禁（开工前必须满足）

- [x] `10-13-client-topnav-shell` 已 `finish` 并提交（提交 `b5e39780`）。
- [x] `git status` 无该任务遗留改动（仅本任务 `.trellis/tasks/10-13-client-footer/` 未跟踪）。
- [x] `app-shell.tsx` 已无 `Sidebar*` 引用，`app-header.tsx` 吸顶顶栏生效；`ClientLayout.tsx` 的 `<main>` **仍无 `flex-1`**，需本任务补。
- [x] admin `SidebarInset` 高度链成立（外 `min-h-svh`、内 `flex flex-col`、内容 div 已 `flex-1`）→ admin 侧只需追加页脚。
- [x] 已核对 `AdminLayout.test.tsx` 单数链接断言需改 `getAllByRole`（见 design「测试改动契约」）。

## 执行顺序

### 1. 组件落地

- [ ] 1.1 `admin/src/components/logo.tsx`：从 `client/src/components/logo.tsx` 复制，保留 `Logo`/`LogoIcon` 两导出，加「待管理端自有图标后替换」注释。
- [ ] 1.2 `client/src/components/footer.tsx`：按 design「上游骨架保留点」写 `<footer>`，内容导航为模块级常量、用 `Link`、GitHub 图标按钮指向 `https://github.com/zhaizzH`、`© {year} AnimeTracker`。宽度 `mx-auto max-w-[1400px] *:px-4 *:md:px-6`。
- [ ] 1.3 `admin/src/components/footer.tsx`：同骨架；导航复用 `ADMIN_NAV_ITEMS`；Logo 来自 1.1；不加 `max-w`；GitHub 图标同上。
- [ ] 1.4 检查两份组件均无 `href="#"`、无 `shaban`、无 `efferd` 字样（`grep`）。

### 2. 挂载

- [ ] 2.1 `client/src/layouts/ClientLayout.tsx`：`<main>` 加 `flex-1`；`<Outlet />` 之后按 `useLocation().pathname !== '/agent'` 条件渲染 `<Footer />`。
- [ ] 2.2 `admin/src/layouts/AdminLayout.tsx`：`SidebarInset` 的高度链已成立，**只需在内容 div（已含 `flex-1`）之后追加**按 `pathname !== '/agent-chat'` 条件渲染的 `<Footer />`；不要重排既有高度类。
- [x] 2.3 admin `SidebarInset` 高度链已核验成立（design「实现前核对结论」），无需补 `min-h-svh`。

### 3. 测试同步

- [ ] 3.1 `client/src/test/shell.guards.test.tsx`：补「布局内页面有 `contentinfo`」「`/agent` 无」；`linkCount` 计数用例无需改。
- [ ] 3.2 `admin/src/layouts/AdminLayout.test.tsx`：**把单数 `getByRole('link', …)` 断言改为 `getAllByRole(...)[0]`**（含 `user.click` 处），再补「内容页有 `contentinfo`」「`/agent-chat` 无」。
- [ ] 3.3 不新增测试文件；断言用 `getByRole`/`getAllByRole`。
- [ ] 3.4 client 404 与认证路由在 `ClientLayout` 外，现有测试未覆盖顶层 `*`；如需断言「404 无页脚」，在既有路由守卫测试文件中以顶层路由复现，不新建文件。

### 4. 验证命令

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

- [ ] 4.1 `npm run typecheck` 通过（CI 强制）。
- [ ] 4.2 `npm test` 通过（两端受影响 workspace）。
- [ ] 4.3 `npm run build` 通过（新增组件 + 布局改动属交付型变更）。

### 5. 浏览器免登录验证

- [ ] 5.1 client：首页等页面滚动到底出现页脚，宽度 1400 与页面容器对齐；访问 `/login`、任意错误路径无页脚；`/agent` 无页脚。
- [ ] 5.2 admin：登录态受限于无凭据时，以源码 + 测试为准（沿用既有「免登录优先」原则）；能登录则验证 `/subjects` 有页脚、`/agent-chat` 无页脚、admin 404 无页脚。
- [ ] 5.3 短内容页（如 admin `/import` 空态）页脚贴视口底部，不悬空。

### 6. 文档同步

- [ ] 6.1 `.trellis/spec/frontend/directory-structure.md`：登记两端新增 `footer.tsx` 与 admin 新增 `logo.tsx`；在「未接线脚手架」附近补一句「两端外壳内容区尾部统一挂 `Footer`，配置页/对话页/404 除外」。
- [ ] 6.2 用定点 `Edit`，保持该文件原有混合 CRLF/LF，**不得整文件 Write**。
- [ ] 6.3 视需要补 `component-guidelines.md` 中「两端各自维护组件副本、共享能力入 shared」的既有约束是否需提及 footer（大概率无需）。

## 审查门禁

- 每个阶段结束后重跑 `npm run typecheck`；第 2 阶段后跑受影响 `npm test`。
- 交付前跑一次全量 `npm run build`。
- 提交前 `git diff` 自查：无 efferd 残留、无死链、无 admin/client 交叉导入、spec 文件行尾未被改写。

## 回滚点

| 点 | 回滚动作 |
|---|---|
| 组件落地后发现问题 | 删两个 `footer.tsx` 与 admin `logo.tsx` |
| 挂载后布局异常 | 还原 `ClientLayout` / `AdminLayout` 两处布局改动 |
| 测试失败 | 还原对应测试断言（测试改动独立，不影响组件） |

无数据迁移、无状态副作用，回滚均为纯文件还原。

## 已确认项（原待实现确认，topnav-shell 落地后核对完毕）

- client `ClientLayout` 定稿形态：方案 B 的 `<main>` **未含 `flex-1`**，由 2.1 补上。
- admin `SidebarInset` 高度链**成立**，admin 侧无需补高度类。
- 仍待在 1.2 落地时确认：Tailwind v4 是否接受 `h-4.5`（`app-header` 现用 `h-4`）；不接受则改用 `h-4`。
