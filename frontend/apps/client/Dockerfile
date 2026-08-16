# ===================================================================
# AnimeTracker 新 Client — 独立 Next.js 容器(opt-in, compose profile: next-client)
# 多阶段构建:
#   1. 依赖层: 从根 pnpm lockfile 安装整个 workspace(--frozen-lockfile)
#   2. 构建层: 构建 @animetracker/client(output: standalone)
#   3. 运行时: 仅拷贝 .next/standalone + .next/static + public 到非 root 镜像,
#              不含任何开发依赖。
# 构建上下文必须是 frontend/(pnpm-workspace.yaml / pnpm-lock.yaml 所在目录):
#   docker build -f apps/client/Dockerfile -t animetracker/client-next:latest .
# ===================================================================

# ---------- 依赖与构建 ----------
FROM node:22-alpine AS builder
# 部分 node 镜像裁剪了 corepack,直接用 npm 全局安装锁定的 pnpm 版本
RUN npm install -g pnpm@10.33.2
WORKDIR /workspace

# 先拷贝锁文件与各 workspace 包的 package.json,利用 Docker 层缓存;
# 新增 workspace 包时需在下方同步追加其 package.json。
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/client/package.json ./apps/client/package.json
COPY packages/api-contract/package.json ./packages/api-contract/package.json
COPY packages/design-tokens/package.json ./packages/design-tokens/package.json
RUN pnpm install --frozen-lockfile

# 源码(构建上下文 .dockerignore 已排除 node_modules/.next 等)
COPY apps ./apps
COPY packages ./packages
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter @animetracker/client build

# ---------- 非 root 运行时: 仅 standalone 产物 ----------
FROM node:22-alpine AS runner
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup -S nodejs && adduser -S nextjs -G nodejs
WORKDIR /app
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/client/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/client/.next/static ./apps/client/.next/static
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/client/public ./apps/client/public

USER nextjs
EXPOSE 3000

# 健康检查: 根路径(SSR 首页)可达即视为健康
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:3000/ || exit 1

CMD ["node", "apps/client/server.js"]
