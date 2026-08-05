# AnimeTracker 用户端前端（client）

面向个人用户的番剧追番管理 Web 应用，基于 **React 18 + TypeScript + Vite** 构建，使用 Ant Design 5 作为 UI 组件库。

> 站点标题：**番组手账 - AnimeTracker**。管理端运营后台位于同级 [`../admin/`](../admin/README.md)（预览版，开发端口 `5174`）。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 18.3 + TypeScript |
| 构建 | Vite 6 |
| UI | Ant Design 5（`antd` + `@ant-design/icons`），中文 `zh_CN` 语言包 |
| 状态 | Zustand 5（全局状态）、React Query 5（`@tanstack/react-query`，服务端数据缓存） |
| 路由 | React Router 7（`react-router-dom`） |
| 请求 | Axios（封装于 `src/api/client.ts`，统一附加 JWT、解包响应、401 刷新） |
| 其他 | dayjs（日期）、react-markdown（AI 对话 Markdown 渲染） |

## 快速开始

```bash
cd frontend/client
npm install
npm run dev          # 开发服务器 http://localhost:5173
npm run build        # 类型检查 + 生产构建 → dist/
npm run preview      # 预览构建产物
```

## 开发代理

`vite.config.ts` 配置开发代理：浏览器中所有 `/api` 请求转发至 `http://localhost:8080`（业务后端），因此本地联调无需额外处理跨域。AI 对话通过 `/api/agent/stream` 走同一代理，由业务后端的 agent 代理层转发至 Python Agent（:8090）。

```
浏览器 → /api/* → Vite 代理 → business :8080 →（Agent 类请求）→ agent :8090
```

## 目录结构

```
src/
├── api/          # 接口封装：client(axios 实例)、auth、subjects、tags、collections、user、agent、common
├── components/   # 通用组件（含 ErrorBoundary）
├── hooks/        # 自定义 Hooks
├── pages/        # 页面级组件
├── store/        # Zustand 状态
├── styles/       # 主题样式（theme.css）
├── types/        # TypeScript 类型
├── utils/        # 工具函数
├── App.tsx       # 路由与布局
└── main.tsx      # 入口：Router + QueryClient + antd ConfigProvider
```

## 页面清单（`src/pages`）

| 页面 | 路由 | 说明 |
|------|------|------|
| `Home` | `/` | 首页 |
| `AnimeIndex` | `/anime` | 番剧库（列表 / 季度 / 标签筛选） |
| `SubjectDetail` | `/anime/:id` | 番剧详情（剧集、标签、收藏） |
| `Schedule` | `/schedule` | 放送时间表 |
| `MyCollections` | `/collections` | 我的收藏与观看进度 |
| `Agent` | `/agent` | AI 对话（搜索 / 发现 / 推荐，SSE 流式） |
| `Login` / `Register` | `/login` `/register` | 登录 / 注册 |
| `ForgotPassword` / `ResetPassword` | `/forgot` `/reset` | 找回 / 重置密码 |
| `VerifyEmail` | `/verify-email` | 邮箱验证 |
| `Profile` | `/profile` | 个人信息管理 |

## 鉴权与接口层

- `src/api/client.ts`：Axios 实例 `baseURL: '/api'`，请求拦截器自动附加 `Authorization: Bearer <token>`（取自 `localStorage`）。
- 响应拦截器按 `code === 0 || 200` 判定成功并解包 `data`；`401` 时尝试用 `refreshToken` 调用 `/api/user/auth/refresh` 续期，失败则清空登录态并跳转 `/login`。
- 接口分组对应后端：`/api/user/auth`、`/api/user`、`/api/user/subjects`、`/api/user/tags`、`/api/user/collections`、`/api/agent/*`。

## 前置依赖

- Node.js 18+（建议 20+），npm 9+。
- 需先启动业务后端（`backend/business`，端口 `8080`）与（可选）AI Agent（`backend/agent`，端口 `8090`）。
- 后端 API 文档：[`../../docs/backend.md`](../../docs/backend.md)；项目总览：[`../../README.md`](../../README.md)。
