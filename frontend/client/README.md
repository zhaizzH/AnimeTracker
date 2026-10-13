# AnimeTracker 用户端 (client)

> **一句话定位**：面向追番用户的 React 单页应用（Vite `:5173`），提供番剧索引与筛选、放送日历、收藏与追番进度、流式 AI 助手；经 `/api` 代理访问 business（`:8080`），**不直连 Agent**。

> 上级文档：[前端总览](../README.md) · [项目总览](../../README.md)

## 适用场景

- 按关键词、季度、标签浏览番剧，查看条目详情与剧集。
- 维护「想看 / 在看 / 看过 / 搁置 / 抛弃」与剧集进度，查看放送日历。
- 用自然语言与 AI 助手对话，确认后批量加入想看或更新进度。

## 前置依赖

| 组件 | 版本/地址 |
|------|-----------|
| Node.js | 22（推荐 LTS） |
| npm | 10+ |
| business 后端 | `:8080`（联调前需先启动，见 [`../../backend/business/README.md`](../../backend/business/README.md)） |

## 目录结构

```text
client/
├── vite.config.mts            # /api → http://localhost:8080；/media → MinIO
└── src/
    ├── main.tsx / router.tsx  # 入口与路由注册
    ├── pages/                 # Home / AnimeIndex / SubjectDetail / Schedule
    │                          # MyCollections / Profile / Agent / 认证页 / NotFound
    ├── components/
    │   ├── app-shell.tsx      # 外壳：吸顶顶栏 + 内容区（无侧栏）
    │   ├── app-header.tsx     # useScroll 驱动滚动背景态
    │   ├── footer.tsx         # 本地页脚
    │   ├── auth/              # AuthPage（登录/注册同面板）
    │   ├── ui/                # 本地 shadcn 原语
    │   └── ...                # SubjectGrid / CollectionActions / AgentChat / subject-info-cards
    ├── layouts/ hooks/ lib/ guards.tsx
    └── test/                  # Vitest 用例（集中存放）
```

## 页面与路由

- 认证路由（`/login`、`/register`、`/verify-email`、`/forgot-password`、`/reset-password`）由 `PublicOnly` 包裹，且**位于 `ClientLayout` 之外**，整屏渲染、无页头。
- `/login` 与 `/register` 渲染**同一个** `components/auth/auth-page.tsx`；`/register` 仅重定向到 `/login`。
- 404 是**顶层** `path: '*'`（`pages/NotFound.tsx`），同样在 `ClientLayout` 之外，未登录访问也不会被重定向。
- 其余页共享外壳 `components/app-shell.tsx`（`ClientLayout`）。

## 外壳、页脚与导航

- 外壳为「吸顶顶栏 + 内容区」，**无侧栏**；移动端复用 `portal.tsx` / `mobile-nav.tsx` 做全屏抽屉，`app-header.tsx` 用 `useScroll` 驱动滚动背景态。
- 页脚 `components/footer.tsx` 由布局在内容区尾部渲染；404 与认证页位于布局之外，**天然不显示**；全高对话页 `/agent` 以 `FOOTERLESS_PATHS` 显式排除。

## 数据、状态与 SSE

- 服务端数据用 TanStack Query；会话 `token` / `user` 复用 shared `useAuthStore`（**仅内存**）。
- URL 筛选现状：`AnimeIndex`（`q`/`page`）、`MyCollections`（`tab`/`page`）、`Schedule`（`year`/`quarter`/`tab`）。
- AI 助手复用 shared `useAgentChat` 与 `agentApi`；组件为 `components/AgentChat.tsx` + `AgentMarkdown.tsx`，另有浮层入口 `AIAssistantFloat.tsx`。SSE 契约见 [Hook 规范 · 前端 HTTP 与 SSE 认证/刷新契约](../../.trellis/spec/frontend/hook-guidelines.md#scenario-前端-http-与-sse-认证刷新契约)。

## 质量检查

```bash
cd frontend
npm run dev:client   # 本地启动 :5173
npm run typecheck
npm test
```

## 与相邻模块的关联

- 仅通过 `/api` 代理访问 business；Agent 能力经 business 代理层暴露，不直连 `:8090`。
- 跨端共享能力进入 [`@animetracker/shared`](../packages/shared/README.md)，不互相导入 admin 源码。
- 规范：[前端开发规范](../../.trellis/spec/frontend/index.md)。
