# 实施：两端 UI 基础设施

## 1. client 构建配置
- [x] `client/vite.config.mts`：加 `@tailwindcss/vite` 插件；`resolve.alias` 加 `'@': path.resolve(__dirname, 'src')`
- [x] `client/vite.config.mts`：`optimizeDeps.include` 移除 antd 相关、加入新依赖
- [x] `client/vite.config.mts`：`manualChunks` 移除 `vendor-antd*` 规则，改按新依赖划分
- [x] `client/tsconfig.json`：`paths` 加 `"@/*": ["./src/*"]`
- [x] `client/vitest.config.mts`：alias 加 `@`

## 2. client Tailwind + shadcn 骨架
- [x] `client/package.json`：加 tailwind/radix/cva/clsx/tailwind-merge/lucide-react/sonner
- [x] 新建 `client/components.json`（照 `admin/components.json`，含 `@efferd` registry）
- [x] 替换 `client/src/index.css` 为 runner CSS
- [x] 新建 `client/src/lib/utils.ts` 的 `cn()`

## 3. 主题统一
- [x] 新建 `client/src/components/theme-bridge.tsx`（移植 admin 版）
- [x] 改写 `client/src/main.tsx`：移除 `ConfigProvider`/antd reset 与裸 DOM 写入，挂 `ThemeBridge`
- [x] 确认 admin `theme-bridge.tsx` 与 `useThemeStore` 契约一致

## 4. 占位根与验证
- [x] `client/src` 建最小可渲染根（App + 空路由壳），排除页面
- [x] `admin/src` 建最小可渲染根，排除页面
- [x] 冒烟：`npm run dev:client` / `npm run dev:admin` 打开空白壳，切换暗色生效
- [x] `npm run typecheck`、`npm run build`

## 验证命令
```bash
cd frontend
npm run typecheck
npm run build
npm run dev:client
npm run dev:admin
```

## 回滚点
- 配置层可单独还原；整体回滚至 `pre-frontend-rebuild`。
