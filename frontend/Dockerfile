# ===================================================================
# AnimeTracker Frontend — 构建客户端与管理端,由 nginx 托管
# 客户端位于 /, 管理端位于 /admin/(vite base=/admin/, 见 compose 说明)
# ===================================================================
FROM node:22-alpine AS builder

WORKDIR /build

# 客户端
COPY client/package.json client/package-lock.json ./client/
RUN npm ci --prefix client

# 管理端
COPY admin/package.json admin/package-lock.json ./admin/
RUN npm ci --prefix admin

# 源码(构建上下文为 frontend/,node_modules/dist 已在 .dockerignore 排除)
COPY client ./client
COPY admin ./admin

RUN npm run build --prefix client
RUN npm run build --prefix admin -- --base=/admin/

# ---------- 运行阶段: nginx ----------
FROM nginx:1.27-alpine

# openssl 用于 compose 首次启动时生成自签占位证书(见 deploy/nginx/bootstrap.sh);
# curl 用于健康检查(生产模板下 / 返回 301 重定向,curl 不跟随且 3xx 视为成功)
RUN apk add --no-cache openssl curl

COPY --from=builder /build/client/dist /usr/share/nginx/html
COPY --from=builder /build/admin/dist /usr/share/nginx/html/admin

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS -o /dev/null http://127.0.0.1/ || exit 1
