# AnimeTracker 用户端前端（client）

面向 C 端用户的番剧追番管理 Web 应用，提供番剧浏览 / 搜索、追番进度管理、放送时间表、标签体系、AI 对话助手等功能。基于 **React 18 + TypeScript + Vite 6 + Ant Design 5** 构建。

- **开发端口**：`5173`
- **生产构建**：`npm run build` → `dist/`

---

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 18.3 |
| 语言 | TypeScript | ~5.6（strict 模式） |
| 构建 | Vite | 6 |
| UI | Ant Design 5 + @ant-design/icons | 5.22+ |
| 状态管理 | Zustand 5（`authStore`） | — |
| 服务端状态 | TanStack React Query 5 | — |
| 路由 | React Router 7（`react-router-dom`） | — |
| HTTP | Axios（封装于 `src/api/client.ts`） | 1.7 |
| 日期 | Day.js | 1.11 |
| Markdown | react-markdown | 9（AI 回复渲染） |

---

## 快速开始

```bash
cd frontend/client
npm install
npm run dev          # 开发服务器 http://localhost:5173
npm run build        # 类型检查 + 生产构建 → dist/
npm run preview      # 预览构建产物
```

### 开发代理

`vite.config.ts` 配置：

- 开发服务器监听 `0.0.0.0:5173`。
- 所有 `/api` 请求转发至 `http://localhost:8080`（业务后端）。
- 路径别名 `@` → `src`。

```
浏览器 → /api/* → Vite 代理 → business :8080
```

---

## 目录结构

```
src/
├── main.tsx                  # 入口：StrictMode → BrowserRouter → QueryClientProvider → ConfigProvider → ErrorBoundary → App
├── App.tsx                   # 根组件：路由定义 + 懒加载页面 + 鉴权守卫
├── vite-env.d.ts
│
├── api/                      # API 层（每个模块一个文件）
│   ├── client.ts             # Axios 实例 + JWT 拦截器 + 401 自动刷新 Token
│   ├── auth.ts               # 认证（注册/登录/验证/找回密码/刷新/登出）
│   ├── subjects.ts           # 番剧条目（列表/搜索/季度/详情/剧集）
│   ├── collections.ts        # 收藏与观看进度
│   ├── agent.ts              # AI 助手（会话管理）
│   ├── tags.ts               # 标签
│   ├── user.ts               # 个人资料
│   └── common.ts             # 通用（文件上传）
│
├── components/               # 共享组件
│   ├── Layout.tsx            # App 布局（Header + Content + Outlet）
│   ├── Header.tsx            # 顶部导航
│   ├── ProtectedRoute.tsx    # 鉴权守卫（未登录 → /login）
│   ├── ErrorBoundary.tsx     # 全局错误边界
│   ├── AuthShell.tsx         # 认证页面外壳（居中卡片）
│   ├── SubjectCard.tsx       # 番剧卡片
│   ├── PageHeading.tsx       # 页面标题（含索引编号）
│   └── CollectionActions.tsx # 收藏操作面板（类型/评分/进度）
│
├── hooks/                    # 自定义 Hook
│   ├── useAuth.ts            # 认证操作（登录/注册/验证/登出）
│   └── useCollections.ts     # 收藏操作（React Query mutations）
│
├── pages/                    # 页面组件（全部 React.lazy 懒加载）
│   ├── Home.tsx              # 首页（今日放送 + 统计数据）
│   ├── AnimeIndex.tsx        # 番剧索引（搜索/过滤/排序）
│   ├── SubjectDetail.tsx     # 番剧详情
│   ├── Schedule.tsx          # 放送时间表（按周/年/季）
│   ├── MyCollections.tsx     # 我的收藏
│   ├── Agent.tsx             # AI 助手（SSE 流式对话）
│   ├── Login.tsx             # 登录
│   ├── Register.tsx          # 注册
│   ├── VerifyEmail.tsx       # 邮箱验证
│   ├── ForgotPassword.tsx    # 忘记密码
│   ├── ResetPassword.tsx     # 重置密码
│   └── Profile.tsx           # 个人中心
│
├── store/                    # Zustand 状态
│   └── authStore.ts          # 认证状态（token/refreshToken/user，localStorage 持久化）
│
├── styles/
│   └── theme.css             # 纸质感设计系统（全局 CSS 变量 + antd 样式覆盖）
│
├── types/
│   └── index.ts              # 所有接口/DTO/VO 类型定义
│
└── utils/
    └── index.ts              # 工具函数（getCurrentQuarter, COLLECTION_TYPE_LABELS）
```

---

## 路由

所有页面组件均使用 `React.lazy` 懒加载，配合 `Suspense` 统一显示加载状态。

### 公开路由（无需登录，无 Layout）

| 路径 | 页面 |
|------|------|
| `/login` | 登录 |
| `/register` | 注册 |
| `/verify-email` | 邮箱验证 |
| `/forgot-password` | 忘记密码 |
| `/reset-password` | 重置密码 |

### 受保护路由（需登录，`ProtectedRoute` 守卫）

| 路径 | 页面 |
|------|------|
| `/` | 首页（今日放送 + 统计） |
| `/anime` | 番剧索引（搜索/过滤/排序） |
| `/subject/:id` | 番剧详情 |
| `/schedule` | 放送时间表 |
| `/my-collections` | 我的收藏 |
| `/agent` | AI 助手 |
| `/profile` | 个人中心 |

---

## 核心架构

### 应用入口层级

```
React.StrictMode
  └── BrowserRouter
        └── QueryClientProvider (retry: 1, staleTime: 30s, refetchOnWindowFocus: false)
              └── ConfigProvider (antd 中文 + 主题定制)
                    └── ErrorBoundary
                          └── Suspense (fallback: "加载中...")
                                └── App
```

### API 层

- **Axios 实例**：`baseURL: '/api'`，`timeout: 30s`
- **请求拦截器**：自动从 localStorage 读取 `token`，附加 `Authorization: Bearer <token>`
- **响应拦截器**：解包 `Result<T>`（`{ code, message, data }`），code 非 0/200 视为错误
- **Token 自动刷新**：401 时尝试 `refreshAccessToken()`（调用 `POST /api/user/auth/refresh`），成功则重试请求，失败则登出并跳转 `/login`
- **便捷方法**：`http.get<T>()` / `http.post<T>()`

### 状态管理

| 场景 | 方案 |
|------|------|
| 登录态 / 用户信息 | `authStore`（Zustand + localStorage 持久化） |
| 服务端数据 | React Query（`staleTime: 30s`） |
| 页面局部 UI | React `useState` |

`authStore` 在 App 挂载时调用 `hydrate()` 从 localStorage 恢复登录状态。

---

## 设计系统

用户端采用独特的**纸质感设计系统**（`src/styles/theme.css`），通过 CSS 自定义属性实现：

| CSS 变量 | 色值 | 用途 |
|----------|------|------|
| `--paper` | `#f3eee3` | 主背景（纸张纹理） |
| `--paper-soft` | `#faf7f0` | 卡片背景 |
| `--paper-deep` | `#e8e0d0` | 表头/分段 |
| `--ink` | `#201d18` | 主文字 |
| `--accent` | `#c13a24` | 主强调色（红色） |
| `--gold` | `#a67c2d` | 评分星级 |
| `--green` | `#3f6b4f` | 状态绿 |
| `--blue` | `#3c5a6b` | 状态蓝 |

- 字体方案：衬线（中文宋体系）+ 无衬线（苹方/微软雅黑）+ 等宽
- 全局背景使用重复线性渐变模拟纸张纹理
- 卡片悬停效果为 `translateY(-4px)` + 偏移阴影
- 所有 antd 组件均有自定义样式覆盖
- 番剧详情页使用 "dossier" 布局（左海报 + 右元数据）
- AI 对话页使用 "book" 布局（左会话列表 + 右聊天面板）
- 响应式断点：900px 和 520px

---

## 核心功能

### AI 助手（`/agent`）

最复杂的页面，实现了基于 SSE 的流式 AI 对话：

- 会话管理（创建 / 删除 / 切换 / 历史缓存）
- 思考过程展示（`details` / `summary` 展开）
- 工具调用状态实时显示
- 使用 `react-markdown` 渲染 AI 回复
- 手动 Token 刷新（SSE 不走 axios 拦截器）

### 放送时间表（`/schedule`）

- 按周 + 季（春/夏/秋/冬）组织
- 周一到周日基于 `airWeekday` 分组
- 支持查看从 1950 年至今任意年份的放送数据

### 收藏系统

五种收藏类型，10 分制评分，集数进度追踪：

| 类型 | 标签 | 颜色 |
|------|------|------|
| 1 | 想看 | 蓝色 |
| 2 | 看过 | 金色 |
| 3 | 在看 | 绿色 |
| 4 | 搁置 | 灰色 |
| 5 | 抛弃 | 红色 |

### 认证流程

完整的用户系统：注册 → 邮箱验证 → 自动登录 → 登录/登出（JWT + Refresh Token）→ 忘记密码 → 重置密码 → 个人中心。

---

## 相关文档

- 管理端前端：[`../admin/README.md`](../admin/README.md)
- 前端总览：[`../README.md`](../README.md)
- 项目总览：[`../../README.md`](../../README.md)
- 后端 API 文档：[`../../docs/backend.md`](../../docs/backend.md)
