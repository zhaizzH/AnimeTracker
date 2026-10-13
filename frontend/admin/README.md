# AnimeTracker 管理端 (admin)

> **一句话定位**：面向运营管理员的 React 单页应用（Vite `:5174`），提供数据可视化看板（Recharts）、番剧/用户/导入/操作日志管理、Agent 提示词与模型配置热更新；经 `/api` 代理访问 business（`:8080`），**不直连 Agent**。

> 上级文档：[前端总览](../README.md) · [项目总览](../../README.md)

## 适用场景

- 仪表盘统计与趋势可视化。
- 番剧条目、用户、导入任务、操作审计日志管理。
- Redis 动态 Prompt 提示词与模型配置热更新，管理员专属数据抓取 Agent 对话。

## 前置依赖

| 组件 | 版本/地址 |
|------|-----------|
| Node.js | 22（推荐 LTS） |
| npm | 10+ |
| business 后端 | `:8080`（联调前需先启动，见 [`../../backend/business/README.md`](../../backend/business/README.md)） |
| 管理员账号 | 需 `role=ADMIN`，登录后 `RequireAdmin` 才放行 |

## 目录结构

```text
admin/
├── vite.config.mts            # /api → http://localhost:8080；/media → MinIO
└── src/
    ├── main.tsx / router.tsx  # 入口与路由注册
    ├── pages/                 # Dashboard / Subjects / Users / Import / Logs
    │                          # AgentConfig / AgentChat / NotFound（含同目录 *.test.tsx）
    ├── components/
    │   ├── auth/auth-page.tsx # 登录页（默认导出 AdminLogin），非 pages 下路由页
    │   ├── dashboard/         # 看板图表（recharts）
    │   ├── app-sidebar.tsx    # 侧栏导航（AppSidebar / ADMIN_NAV_ITEMS）
    │   ├── footer.tsx / ui/   # 本地页脚与 shadcn 原语
    │   └── ...
    ├── layouts/AdminLayout.tsx
    └── hooks/ lib/ guards.tsx
```

## 页面与路由

- 页面：`Dashboard`、`Users`、`Subjects`、`Import`、`Logs`、`AgentConfig`、`AgentChat`、`NotFound`。登录页是 `components/auth/auth-page.tsx`（默认导出 `AdminLogin`）。
- 除登录页静态导入外，其余页面在 `router.tsx` 中 `lazy` + Suspense。
- 登录页独立成路由、不经任何 shell；其余页共享 `layouts/AdminLayout.tsx`；`NotFound`（`path: '*'`）在 `AdminLayout` 之外。
- **admin 路由不带 `/admin` 前缀**（`/login`、`/dashboard`……），页面以站点根为基路径；生产部署在独立端口 `:8081` 的站点根（反代承载）。详见 [前端目录结构 · admin 页面与路由](../../.trellis/spec/frontend/directory-structure.md#admin-页面与路由) 与 [ADR 0018](../../.trellis/spec/adr/0018-admin-on-separate-port-not-subpath.md)。

## 图表与 UI

- 图表依赖 **recharts 3**（`frontend/admin/package.json`），经 shadcn `components/ui/chart.tsx` 原语消费；随 Dashboard 懒加载 chunk 走，不单独拆包。
- 已完全移除 Ant Design 与 ECharts 运行时依赖；若构建产物出现 `vendor-antd*` chunk，视为回归。
- UI 原语为各端本地维护的 `components/ui`（`@efferd` 只是 shadcn registry 源，不存在可安装的 `@efferd/*` 包）。

## 数据、状态与 SSE

- 服务端数据用 TanStack Query；会话 `token` / `user` 复用 shared `useAuthStore`（**仅内存**）。
- 鉴权需同时满足 `status=authenticated` 与 `role=ADMIN`；守卫测试用 `MemoryRouter` + 真实 `Routes` 断言跳转。
- AI 助手复用 shared `useAgentChat` 与 `adminAgentApi`（`pages/AgentChat.tsx`），自动化删除用 `adminAgentApi.deleteSession`；配置页 `AgentConfig.tsx` 用 `cfgInitialized` 门控回填，避免覆盖用户输入。

## 质量检查

```bash
cd frontend
npm run dev:admin    # 本地启动 :5174
npm run typecheck
npm test
```

## 与相邻模块的关联

- 仅通过 `/api` 代理访问 business；Agent 能力经 business 代理层暴露。
- 跨端共享能力进入 [`@animetracker/shared`](../packages/shared/README.md)，不互相导入 client 源码。
- 规范：[前端开发规范](../../.trellis/spec/frontend/index.md)。
