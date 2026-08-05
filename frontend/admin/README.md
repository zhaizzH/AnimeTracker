# AnimeTracker 管理端前端（admin）

面向运营人员的番剧管理后台 Web 应用，基于 **React 18 + TypeScript + Vite** 构建，使用 Ant Design 5 作为 UI 组件库。

> **站点标题**：**AnimeTracker 运营后台**。
> **当前状态：预览版（🟡 Preview）** —— 工程骨架、登录页与仪表盘已可交互（演示登录 + Mock 数据），其余页面为雏形，等待接入真实 `/api/admin/*` 后端接口。用户端前端位于同级 [`../client/`](../client/README.md)。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 18.3 + TypeScript |
| 构建 | Vite 6 |
| UI | Ant Design 5（`antd` + `@ant-design/icons`） |
| 状态 | Zustand 5（全局状态，如 `authStore`）、React Query 5（`@tanstack/react-query`，服务端数据缓存） |
| 路由 | React Router 7（`react-router-dom`） |
| 请求 | Axios（封装于 `src/api/client.ts`，统一附加 JWT） |
| 其他 | dayjs（日期） |

> 与用户端 `../client` 技术栈一致；**尚未引入 ProComponents**，表格 / 表单以 antd 基础组件实现。

## 快速开始

```bash
cd frontend/admin
npm install
npm run dev          # 开发服务器 http://localhost:5174
npm run build        # 类型检查 + 生产构建 → dist/
npm run preview      # 预览构建产物
```

## 开发代理

`vite.config.ts` 配置：

- 开发服务器监听 `0.0.0.0:5174`。
- 所有 `/api` 请求转发至 `http://localhost:8080`（业务后端），本地联调无需额外处理跨域。
- 路径别名 `@` → `src`。

```
浏览器 → /api/* → Vite 代理 → business :8080 (/api/admin/*)
```

## 目录结构

```
src/
├── api/          # 接口封装：client(axios 实例)、auth、dashboard、subjects、users、imports、logs、agent
├── components/   # 通用组件
├── layouts/      # 后台布局（侧边栏 / 顶栏）
├── mock/         # 演示数据：admin.ts、dashboard.ts（登录与仪表盘当前使用 Mock）
├── pages/        # 页面级组件（见下表）
├── store/        # Zustand 状态（authStore.ts）
├── styles/       # 主题样式
├── types/        # TypeScript 类型
├── theme.ts      # 「极光白昼」浅色后台主题
├── App.tsx       # 路由与布局
└── main.tsx      # 入口
```

## 页面清单（`src/pages`）

| 页面 | 文件 | 说明 | 状态 |
|------|------|------|------|
| 登录 | `Login.tsx` | 运营人员登录（演示模式，Mock 鉴权） | ✅ 可交互 |
| 仪表盘 | `Dashboard.tsx` | 概览统计（条目数 / 用户数 / 导入任务等，Mock 数据） | ✅ 可交互 |
| 番剧管理 | `Subjects.tsx` | 条目列表 / 检索 / CRUD 入口 | 🚧 雏形 |
| 用户管理 | `Users.tsx` | 用户列表、禁用 / 启用、角色管理 | 🚧 雏形 |
| 导入任务 | `ImportTasks.tsx` | 查看 / 触发 Bangumi 数据导入任务 | 🚧 雏形 |
| Agent 配置 | `AgentConfig.tsx` | 托管提示词（gateway / search / discover / recommend）可视化配置，对应 Agent 服务的 Redis 提示词快照 | 🚧 雏形 |
| 操作日志 | `Logs.tsx` | 审计日志查看（对应后端 `operation_log` 表） | 🚧 雏形 |

## 鉴权与接口层

- `src/api/client.ts`：Axios 实例 `baseURL: '/api'`，请求拦截器自动附加 `Authorization: Bearer <token>`（取自 `authStore`）。
- `authStore.ts`：维护登录态与 token；当前登录为**演示模式**（走 `mock/auth.ts`，不请求真实 `/api/user/auth`）。
- 接口分组对应后端 `/api/admin/*`：`/api/admin/auth`、`/api/admin/dashboard`、`/api/admin/subjects`、`/api/admin/users`、`/api/admin/imports`、`/api/admin/logs`、`/api/agent/*`（Agent 配置透传）。

## 后端能力（已就绪）

管理端 API 路径前缀为 `/api/admin/*`，由 `backend/business/admin`（Maven 模块 `animetracker-admin`）提供：

- **用户管理**：查看 / 禁用 / 启用用户，管理用户角色（`AdminUserController`）。
- **番剧管理**：条目 CRUD、剧集与标签维护（`AdminController`）。
- **仪表盘统计**：运营概览数据（`AdminDashboardController`）。
- **数据导入**：触发 / 查看 Bangumi 导入任务（`ImportController`）。
- **操作审计**：后台操作落库 `operation_log`，供「日志」页追溯（`AdminLogController`）。

后端接口定义见 [`../../docs/backend.md`](../../docs/backend.md)；业务后端总览见 [`../../backend/business/README.md`](../../backend/business/README.md)；导入器说明见 [`../../backend/data/importer/README.md`](../../backend/data/importer/README.md)。

## 待办

- [x] 初始化 Vite + React + TS 工程（端口 5174、代理、别名）
- [x] 「极光白昼」浅色后台主题 + 布局骨架
- [x] 登录页 + 仪表盘（演示模式 / Mock 数据）
- [x] 番剧 / 用户 / 导入 / Agent 配置 / 日志 页面雏形
- [ ] 登录接入真实 `/api/admin/auth`（替换 Mock 鉴权）
- [ ] 各页面接入真实 `/api/admin/*` 接口并移除 Mock
- [ ] 权限指令 / 路由守卫按角色控制
