# AnimeTracker 前端

> **一句话定位**：npm workspaces 单仓，含用户端 `client`（:5173）、管理端 `admin`（:5174）与共享包 `@animetracker/shared`；React 18 + TypeScript 5 + Vite 5，经 `/api` 代理统一访问 business（:8080），不直连 Agent。

> 上级文档：[项目总览](../README.md)

## 适用场景

- 用户端：番剧索引、多条件筛选、放送日历、收藏与追番进度管理、流式 AI 助手。
- 管理端：ECharts 数据看板、番剧/用户/导入/操作日志管理、Agent 提示词与模型配置、管理员 Agent 对话。
- 共享包：双端共用的 API 封装、鉴权协调、SSE 消费、类型与公共组件。

## 前置依赖

| 组件 | 版本 |
|------|------|
| Node.js | 22（推荐 LTS） |
| npm | 10+ |
| business 后端 | :8080（联调前需先启动，见 [`../backend/business/README.md`](../backend/business/README.md)） |

## 目录结构

```text
frontend/
├── package.json             # workspaces 根（packages/*, client, admin）
├── client/                  # 用户端 SPA（Vite :5173）
│   ├── vite.config.mts      # /api → http://localhost:8080 代理
│   └── src/
│       ├── pages/           # Home / AnimeIndex / SubjectDetail / Schedule / MyCollections / Profile / Agent / 认证页
│       ├── components/ layouts/ hooks/ styles/ guards.tsx router.tsx
│       └── test/            # vitest 用例
├── admin/                   # 管理端 SPA（Vite :5174，含 Tailwind）
│   ├── vite.config.mts      # /api → http://localhost:8080 代理
│   └── src/
│       ├── pages/           # Dashboard / Subjects / Users / Import / Logs / AgentChat / AgentConfig / AdminLogin
│       ├── components/ layouts/ hooks/ lib/ guards.tsx router.tsx
│       └── *.test.tsx
└── packages/shared/         # @animetracker/shared 共享包
    └── src/
        ├── api/             # http 封装 + auth/subjects/collections/tags/files/agent 与 api/admin/*
        ├── auth/            # coordinator：双端 token 刷新协调
        ├── sse.ts           # Agent SSE 流式消费
        ├── store/           # Zustand：auth / theme
        ├── hooks/           # useAgentChat / useAuthStatus / useBootstrapAuth
        ├── components/      # AuthGate / SubjectCard
        └── types/           # 跨端共享类型
```

## 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| React / react-dom | 18 | UI |
| TypeScript | 5 | 类型 |
| Vite | 5 | 构建与开发服务器 |
| Vitest | 2 | 单元测试 |
| Ant Design | 5（shared 固定 `^5.29.3`） | 组件库 |
| TanStack Query | 5 | 服务端状态 |
| Zustand | 4 | 客户端状态 |
| React Router | 7 | 路由 |
| react-markdown | 9 | Agent 回答渲染 |
| ECharts 6 + echarts-for-react | — | 管理端看板 |

## 快速开始

```bash
cd frontend
npm install

# 终端 1：用户端 http://localhost:5173
npm run dev:client

# 终端 2：管理端 http://localhost:5174
npm run dev:admin
```

两端 Vite 均已配置 `/api → http://localhost:8080` 代理（`changeOrigin: true`），前端只发同源请求，无需额外 CORS 配置。

## 测试与检查

```bash
npm run test        # 全部 workspace 的 vitest
npm run typecheck   # 全部 workspace 的 tsc
npm run build       # client + admin 产物构建
```

## 与相邻模块的关联

- **business**（[`../backend/business/README.md`](../backend/business/README.md)）：唯一 API 来源；Agent 对话走 business 代理层 `/api/{client,admin}/agent/*`，不直连 :8090。
- **接口契约**：[`../docs/spec/openapi.yaml`](../docs/spec/openapi.yaml)（手工维护）。
- **项目总览**：[`../README.md`](../README.md)。

## 待补充

1. **页面/组件开发规范**：路由守卫、TanStack Query 键约定、antd 主题定制的成文规范暂无。
2. **shared 包发布边界**：`@animetracker/shared` 仅供仓内消费，无独立版本与发布流程。
