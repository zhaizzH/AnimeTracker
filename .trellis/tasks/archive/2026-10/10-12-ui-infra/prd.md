# 两端 Tailwind v4 + shadcn 基础设施

父任务：`.trellis/tasks/10-12-frontend-rebuild`（技术设计与总体约束见父任务 `design.md`）。

## Goal

在 client 引入 Tailwind CSS v4 + shadcn 基础设施，加固 admin 现有基础设施，并把两端主题统一到 `.dark` 类。完成后两端可启动「空壳」应用。

## 前置依赖

子任务 `10-12-rebuild-prep` 必须先完成（旧实现已删除、shared 已清 antd）。**顺序理由**：本子任务基于「src 为空」的前提铺设构建配置，若旧实现仍在，配置改动会与旧代码互相干扰。

## Requirements

- **R1 client 构建配置**：加 `@tailwindcss/vite` 插件；`@` → `./src` 别名（`vite.config.mts`、`tsconfig.json`、`vitest.config.mts` 三处，保留 `@shared`）。
- **R2 client shadcn**：新建 `client/components.json`（new-york / neutral / lucide / `@efferd` registry，对齐 `admin/components.json`）；runner CSS（`@import "tailwindcss"` + `tw-animate-css` + `@custom-variant dark (&:is(.dark *))`）；`lib/utils.ts` 的 `cn()`。
- **R3 client 依赖**：增 `tailwindcss`、`@tailwindcss/vite`、`radix-ui`、`class-variance-authority`、`clsx`、`tailwind-merge`、`lucide-react`、`sonner`。
- **R4 client 构建清理**：`vite.config.mts` 的 `optimizeDeps.include` 与 `manualChunks` 移除 antd 相关项，纳入新依赖。
- **R5 主题统一**：移植 admin `theme-bridge.tsx`（含 `matchMedia` change 监听）到两端；client 不再裸写 DOM；保留 shared 的 `useThemeStore` / `resolveMode`。
- **R6 admin 基线不动**：确认 `admin/components.json`（含 `@efferd` registry）与 Tailwind 配置完好、admin 的 typecheck/test 基线不受本次变更影响。**不改 admin 源码**（admin 已是 dashboard-5 终态，见 `10-12-admin-verify`）。

## Acceptance Criteria

- [ ] AC1：`npm run dev:client` 与 `npm run dev:admin` 均能启动空壳。
- [ ] AC2：`cd frontend && npm run typecheck` 通过。
- [ ] AC3：两端源码不含 antd 导入；`@shared` 可导入。
- [ ] AC4：暗色切换经 store → `html.dark` 生效，跟随系统时 `matchMedia` 变化实时响应（admin `theme-bridge` 已具备，client 需新补）。
- [ ] AC5：`npm run build` 通过（两端）。

## Out of Scope

- 安装 efferd 块、写页面、写路由（属子任务 3/4/5）。

## 交付给父任务

可启动的两端空壳 + 可用的 `cn()` / shadcn primitive 通道 + 统一主题机制。
