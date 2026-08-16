# AnimeTracker 前端总览

本项目前端由两个相互独立的 React 工程组成，均基于 **React 18 + TypeScript + Vite 6 + Ant Design 5**，通过 Vite 开发代理将 `/api` 请求转发至业务后端（`http://localhost:8080`）。

| 工程 | 端口 | 说明 | 文档 |
|------|------|------|------|
| `client` | `5173` | 用户端追番应用：浏览 / 搜索、追番进度、时间表、标签、AI 助手 | [client/README.md](client/README.md) |
| `admin` | `5174` | 运营后台（部分功能开发中）：仪表盘、番剧 / 用户 / 导入 / 日志 / Agent 配置与管理员对话 | [admin/README.md](admin/README.md) |

```
Browser ──/api/*──► Vite dev proxy ──► business :8080
```

两个工程技术栈一致（Zustand + React Query + React Router 7），但用户端采用纸质感设计系统（`theme.css` 全局 CSS 变量），管理端采用明暗双主题（`theme.ts` + `global.css`），互不共享源码。

管理端核心数据页面已接入真实 `/api/admin/*` 接口；当前主要继续完善管理员 Agent 能力、细粒度权限与交互体验。

## 快速开始

```bash
cd frontend/client && npm install && npm run dev   # http://localhost:5173
cd frontend/admin  && npm install && npm run dev   # http://localhost:5174
```

生产构建均为 `npm run build` → `dist/`。开发联调需先启动业务后端（:8080），详见 [`../backend/README.md`](../backend/README.md)。

## 相关文档

- 用户端前端：[`client/README.md`](client/README.md)
- 管理端前端：[`admin/README.md`](admin/README.md)
- 后端总览：[`../backend/README.md`](../backend/README.md)
- 项目总览：[`../README.md`](../README.md)
- 后端 API 文档：[`../docs/spec/openapi.yaml`](../docs/spec/openapi.yaml)
