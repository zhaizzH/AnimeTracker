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

## 新 Client（Next.js，pnpm workspace）

`apps/client` 是独立的 Next.js 公开站点（SSR / SEO 完整），与上面两个 Vite 工程并存但不共享源码。workspace 使用 pnpm（见 `pnpm-workspace.yaml` / `pnpm-lock.yaml`）：

```bash
cd frontend
pnpm install            # 安装整个 workspace（lockfile 已提交，CI 用 --frozen-lockfile）
pnpm generate           # 从 docs/spec/openapi.yaml 重新生成 api-contract 类型
pnpm lint / typecheck / test / build
pnpm --filter @animetracker/client e2e   # Playwright：生产构建 + 确定性 mock 后端
```

### 独立部署（opt-in，不影响既有 nginx 生产路由）

新 Client 以独立容器交付，默认不参与现有编排；需要时显式启用 `next-client` profile：

```bash
# 构建上下文必须为 frontend/（含 pnpm-workspace.yaml / pnpm-lock.yaml）
docker build -f apps/client/Dockerfile -t animetracker/client-next:latest .

# 单独拉起新 Client 容器（仅在启用 next-client profile 时创建）
docker compose -f compose.yml -f compose.prod.yml --profile next-client up -d client-next
```

容器只 `expose 3000`（不发布到宿主机），挂在 `frontend` 与 `backend` 网络：nginx 经 `frontend` 反代，SSR 经 `BUSINESS_API_URL` 走 `backend` 直连业务后端。对外路由需把 `deploy/nginx/client-next.conf.template` 挂载到 nginx 容器的 `/etc/nginx/templates/`（环境变量 `CLIENT_DOMAIN` 渲染 `server_name`），并配置 `CLIENT_DOMAIN`、`BUSINESS_API_URL`、`NEXT_PUBLIC_SITE_URL`（见 `.env.example`）。该模板是纯反代、无静态 SPA fallback，用于接入/验证阶段，不会自动切换现有 `frontend`/`admin` 流量。

## 相关文档

- 用户端前端：[`client/README.md`](client/README.md)
- 管理端前端：[`admin/README.md`](admin/README.md)
- 后端总览：[`../backend/README.md`](../backend/README.md)
- 项目总览：[`../README.md`](../README.md)
- 后端 API 文档：[`../docs/spec/openapi.yaml`](../docs/spec/openapi.yaml)
