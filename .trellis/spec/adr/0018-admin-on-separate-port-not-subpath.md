# 0018 — 管理端用独立端口部署，前端 `baseURL` 固定 `/api`

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：[frontend/quality-guidelines.md](../frontend/quality-guidelines.md)、`docs/deploy/` 部署方案

## 背景

用户端（client）与管理端（admin）是两个独立 SPA。二者需要被部署到同一台主机、经同一入口访问。

## 决策

- 管理端部署在**独立端口**（生产 `:8081`，本地开发 `:5174`），而**不是**挂在用户端路径下（如 `/admin`）。
- 前端 `baseURL` **固定为 `/api`**（`frontend/packages/shared/src/api/http.ts`），两端共用同一相对前缀，由 Vite/nginx 代理到 business。

## 备选方案

1. **管理端挂用户端子路径 `/admin`。** 未采纳——需要为 admin 单独配置 Vite 的 `base`、router 的 `basename` 与静态资源路径，构建配置复杂度上升，且容易在刷新/深链接时出错。
2. **独立端口 + 固定 `/api`（采纳）。** 两个 SPA 都以根路径部署，各自的构建与路由无需特殊配置。

## 后果

**正面**

- 两个 SPA 互不干扰，各自以 `/` 为基路径，构建与路由配置保持默认。
- `baseURL` 固定 `/api` 使得 API 契约在两端完全一致，代理目标只需在一处（Vite/nginx）配置。

**代价与陷阱**

- **多暴露一个防火墙/NSG 端口**，运维需要显式放行 `:8081`。
- `subject.image` 等公开资源走根相对前缀 `/media` 时，**每个 server 块都要各自配一条 `/media/` 反代**（`:80` 与 `:8081` 各一条），漏配一处该端图片全 404。

**约束**

- 不得把 admin 改为用户端的子路径部署，除非同时处理 `base`/`basename` 与两条反代规则的迁移。
