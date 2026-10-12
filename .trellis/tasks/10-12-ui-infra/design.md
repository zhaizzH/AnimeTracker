# 设计：两端 UI 基础设施

总体架构见父任务 `design.md` §2.1–§2.2；此处写本子任务的边界与对照。

## 边界

- 动：`frontend/client/{vite.config.mts,tsconfig.json,vitest.config.mts,package.json,components.json,src/index.css,src/main.tsx,src/lib/utils.ts,src/components/theme-bridge.tsx}`；`frontend/admin/` 仅「确认不改」。
- 不动：`packages/shared`（子任务 1 已清理完成）。

## client 基础设施对照（照 admin 模板）

| 项 | admin 现状 | client 目标 |
|---|---|---|
| Tailwind 插件 | `@tailwindcss/vite` | 新增 |
| `@` 别名 | vite + tsconfig | 三处补（含 vitest） |
| components.json | 已存在 | 新建，字段对齐 |
| runner CSS | `@import "tailwindcss"` + `tw-animate-css` + `@custom-variant dark` | 同，替换 857 行 `od-*` |
| `cn()` | `lib/utils.ts` | 新建 |
| theme-bridge | 已有 | 移植 |

## 契约

- 主题契约收敛为：`useThemeStore`(`mode`,`followSystem`) → `resolveMode()` → `html.dark` + `style.colorScheme`。**唯一写入点**是 `ThemeBridge`，两端一致。
- 不引入 `next-themes` 的 Provider 接管（shared 已有自己的 store），避免与 `useThemeStore` 双源。

## 取舍

| 取舍 | 选择 | 理由 |
|---|---|---|
| 是否抽公共 shadcn 包 | 不抽 | 两端外壳不同源，抽了固化耦合（父 design §5） |
| 是否用 next-themes | 只用其 CSS 约定，不用其 Provider | shared store 已是权威，双源会导致闪烁 |
| vitest 是否加 Tailwind | 加 `@` 别名即可 | 测试不需 Tailwind 编译，但组件 import 需要别名可解析 |

## 回滚

- 独立的配置层变更，回滚只需还原 `vite.config.mts` / `tsconfig.json` / `package.json` / `index.css` / `main.tsx`。
- 回滚锚点：子任务 1 的 tag `pre-frontend-rebuild`。
