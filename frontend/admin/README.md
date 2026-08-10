# AnimeTracker 管理端前端（admin）

面向运营人员的番剧管理后台 Web 应用，基于 **React 18 + TypeScript + Vite 6 + Ant Design 5** 构建，提供仪表盘、番剧管理、用户管理、数据导入、Agent 配置、操作日志等管理功能。

- **开发端口**：`5174`
- **生产构建**：`npm run build` → `dist/`
- **当前状态**：🟡 预览版（登录与仪表盘已接入真实 API，其余页面陆续接入中）

> 站点标题：**AnimeTracker 运营后台**。用户端前端位于同级 [`../client/`](../client/README.md)。

---

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 18.3 |
| 语言 | TypeScript | ~5.6（strict 模式） |
| 构建 | Vite | 6 |
| UI | Ant Design 5 + @ant-design/icons | 5.22+ |
| 状态管理 | Zustand 5（`authStore` + `themeStore`） | — |
| 服务端状态 | TanStack React Query 5 | — |
| 路由 | React Router 7（`react-router-dom`） | — |
| HTTP | Axios（封装于 `src/api/client.ts`） | 1.7 |
| 日期 | Day.js | 1.11 |

> 与用户端 `../client` 技术栈一致；尚未引入 ProComponents，表格 / 表单以 antd 基础组件实现。

---

## 快速开始

```bash
cd frontend/admin
npm install
npm run dev          # 开发服务器 http://localhost:5174
npm run build        # 类型检查 + 生产构建 → dist/
npm run preview      # 预览构建产物
```

### 开发代理

`vite.config.ts` 配置：

- 开发服务器监听 `0.0.0.0:5174`。
- 所有 `/api` 请求转发至 `http://localhost:8080`（业务后端）。
- 路径别名 `@` → `src`。

```
浏览器 → /api/* → Vite 代理 → business :8080 (/api/admin/*)
```

---

## 目录结构

```
src/
├── main.tsx                  # 入口：React 挂载 + QueryClient + ConfigProvider
├── App.tsx                   # 根组件：路由定义 + 鉴权守卫
├── theme.ts                  # Ant Design 双主题配置（极光白昼 / 暗夜）
├── vite-env.d.ts
│
├── api/                      # API 层
│   ├── client.ts             # Axios 实例 + JWT 拦截器 + 401 自动刷新
│   ├── auth.ts               # 鉴权 API
│   ├── dashboard.ts          # 仪表盘 API
│   ├── subjects.ts           # 番剧管理 API（含文件上传）
│   ├── adminUsers.ts         # 用户管理 API
│   ├── imports.ts            # 数据导入 API
│   ├── logs.ts               # 操作日志 API
│   └── agent.ts              # Agent 配置 API
│
├── components/               # 通用组件
│   ├── StatCard.tsx          # 统计卡片（图标/数值/变化量，5 种色调）
│   ├── BarList.tsx           # 横向条形图列表
│   ├── DonutChart.tsx        # 环形图（conic-gradient 实现）
│   ├── TrendChart.tsx        # SVG 趋势折线图
│   └── ThemeToggle.tsx       # 主题切换（浅色/深色/跟随系统）
│
├── layouts/
│   └── AdminLayout.tsx       # 后台布局（侧边栏 + 顶栏 + 内容区）
│
├── mock/                     # 演示数据（开发/备用）
│   ├── admin.ts              # 番剧/用户/导入/日志/Agent mock
│   └── dashboard.ts          # 仪表盘 mock（趋势/概览/评分等）
│
├── pages/                    # 页面组件
│   ├── Login.tsx             # 登录（已接入真实 API）
│   ├── Dashboard.tsx         # 仪表盘（已接入真实 API）
│   ├── Subjects.tsx          # 番剧管理
│   ├── Users.tsx             # 用户管理
│   ├── ImportTasks.tsx       # 数据导入
│   ├── AgentConfig.tsx       # Agent 配置
│   └── Logs.tsx              # 操作日志
│
├── store/                    # Zustand 状态
│   ├── authStore.ts          # 鉴权状态（token/user，localStorage 持久化）
│   └── themeStore.ts         # 主题状态（light/dark/system，localStorage 持久化）
│
├── styles/
│   └── global.css            # 全局样式（明暗双主题 CSS 变量体系）
│
└── types/
    └── api.ts                # 全部 TypeScript 类型定义
```

---

## 路由

| 路径 | 页面 | 需要登录 |
|------|------|----------|
| `/login` | 登录 | 否 |
| `/dashboard` | 仪表盘 | 是 |
| `/subjects` | 番剧管理 | 是 |
| `/users` | 用户管理 | 是 |
| `/import` | 数据导入 | 是 |
| `/logs` | 操作日志 | 是 |
| `/agent` | Agent 配置 | 是 |
| `*` | 重定向至 `/dashboard` | — |

受保护路由由 `ProtectedLayout` 守卫（检查 `authStore.token`），嵌套在 `AdminLayout` 内渲染。

---

## 页面清单

| 页面 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 登录 | `Login.tsx` | ✅ 可交互 | 真实 API 登录 + ADMIN 角色检查 + 终端风格动画 |
| 仪表盘 | `Dashboard.tsx` | ✅ 可交互 | 调用 6 个真实 API，展示概览统计、趋势图、收藏分布、热门榜 |
| 番剧管理 | `Subjects.tsx` | 🟡 功能较完整 | 列表 + 搜索/过滤 + CRUD + 详情 Drawer + 封面上传 |
| 用户管理 | `Users.tsx` | 🟡 雏形 | 列表 + 关键字/角色过滤 + 角色调整 Modal |
| 数据导入 | `ImportTasks.tsx` | 🟡 雏形 | 导入状态 + 启动表单 + 当前任务 + 历史记录（5s 轮询） |
| Agent 配置 | `AgentConfig.tsx` | 🟡 功能较完整 | 提示词列表/编辑器 + 模型配置 + Agent 健康状态 |
| 操作日志 | `Logs.tsx` | 🟡 功能较完整 | 日志列表 + 多维过滤 + 详情 Drawer + 统计 + CSV 导出 |

---

## 核心架构

### 鉴权流程

- 登录调用真实 `POST /api/client/auth/login` 接口
- 登录成功后检查 `user.role === 'ADMIN'`，非管理员拒绝进入
- Token / RefreshToken 存入 `localStorage` + `authStore`
- Axios 拦截器自动附加 JWT，401 时自动刷新 Token
- 登出调用 `authApi.logout()` 并清理本地状态

### API 层

- **Axios 实例**：`baseURL: '/api'`，`timeout: 30s`
- **请求拦截器**：自动附加 `Authorization: Bearer <token>`
- **响应拦截器**：解包 `Result<T>`，code 非 0/200 时 reject
- **Token 刷新**：401 时调用 `POST /api/client/auth/refresh`，失败则登出
- 接口分组对应后端 `/api/admin/*`：dashboard、subjects、users、imports、logs、agent

### 状态管理

| Store | 持久化 | 说明 |
|-------|--------|------|
| `authStore` | localStorage（token/refreshToken/user） | 登录态、用户信息、登出 |
| `themeStore` | localStorage（`animetracker-admin-theme`） | 主题模式：light / dark / system |

### 主题系统

支持**明暗双主题**，主色调为青色（`#00b3a4` 浅色 / `#2fd6c8` 深色）：

- `theme.ts`：完整的 Ant Design `ThemeConfig`，覆盖所有核心 token 和组件 token
- `global.css`：CSS 自定义属性体系，通过 `[data-theme='dark']` 切换
- `ThemeToggle` 组件：三模式切换（浅色 / 深色 / 跟随系统 `prefers-color-scheme`）
- `AdminLayout`：侧边栏（224px）+ 顶栏（标题/面包屑 + 时钟 + 主题切换 + 用户信息）
- 响应式：`<900px` 侧边栏缩为图标模式，`<760px` 精简顶栏

---

## 通用组件

| 组件 | 说明 |
|------|------|
| `StatCard` | 统计卡片（图标 + 标签 + 数值 + 变化量），支持 5 种色调 |
| `BarList` | 横向条形图列表，支持自定义颜色 |
| `DonutChart` | 纯 CSS conic-gradient 环形图 + 图例 |
| `TrendChart` | 手写 SVG 折线图（720×210 viewBox，支持 3 条曲线） |
| `ThemeToggle` | Ant Design Dropdown 实现的三模式主题切换 |

---

## 后端能力

管理端 API 路径前缀为 `/api/admin/*`，由 `backend/business/admin`（Maven 模块 `animetracker-admin`）提供：

- **仪表盘统计**：运营概览数据（`AdminDashboardController`）
- **番剧管理**：条目 CRUD、剧集与标签维护（`AdminSubjectController`）
- **用户管理**：查看 / 禁用 / 启用用户，管理角色（`AdminUserController`）
- **数据导入**：触发 / 查看 Bangumi 导入任务（`ImportController`）
- **操作审计**：后台操作落库 `operation_log`（`AdminLogController`）

---

## 待办

- [x] 初始化 Vite + React + TS 工程（端口 5174、代理、别名）
- [x] 「极光白昼」浅色后台主题 + 暗夜深色主题 + 布局骨架
- [x] 登录页接入真实 API + ADMIN 角色检查
- [x] 仪表盘接入真实 API
- [x] 番剧 / 用户 / 导入 / Agent 配置 / 日志 页面雏形
- [ ] 各页面全面接入真实 `/api/admin/*` 接口并移除 Mock
- [ ] 权限指令 / 路由守卫按角色细粒度控制

---

## 相关文档

- 用户端前端：[`../client/README.md`](../client/README.md)
- 前端总览：[`../README.md`](../README.md)
- 项目总览：[`../../README.md`](../../README.md)
- 后端 API 文档：[`../../docs/spec/openapi.yaml`](../../docs/spec/openapi.yaml)
- 业务后端详解：[`../../backend/business/README.md`](../../backend/business/README.md)
