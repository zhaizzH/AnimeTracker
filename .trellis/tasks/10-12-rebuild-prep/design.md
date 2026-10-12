# 设计：重建准备

技术设计与总体不变量见父任务 `.trellis/tasks/10-12-frontend-rebuild/design.md`；此处只写本子任务特有的边界与回滚。

## 边界

- 只动：`packages/shared/{src/theme.ts,src/index.ts,package.json,src/components/SubjectCard.tsx}`、`frontend/client/src` 的删除、client 仅服务旧实现的配置项。**admin 不动**（已核验为 dashboard-5 终态）。
- 不动：`packages/shared` 的其余逻辑（api/auth/sse/types/store）、`docs/`、`backend/`、`frontend/package.json` 的 workspaces 定义。

## 契约影响

- `@shared` 的导出面**收窄**：移除 `antdTheme`/`antdThemeDark`。已核对唯一消费方是 `client/src/main.tsx`（随删除消失），无其他引用点。
- `packages/shared/package.json` 移除 `antd` 依赖后，shared 不再需要 antd 运行时；其类型/工具代码不 import antd。
- 其余 62 处 `@shared` 引用在删除后暂时全部悬空，由子任务 3/4/5 接回——这是预期状态，本子任务结束时代码不可构建。

## 取舍

| 取舍 | 选择 | 理由 |
|---|---|---|
| 删除与清理是否分开提交 | 合并为一个子任务 | 两者都属「拆除」，分开会让中间态无意义 |
| shared 的 antd 是否留到后面清 | 本子任务清 | 先清可让后续子任务不必面对两套令牌 |

## 回滚

- 本子任务**整体可回滚**：`git checkout pre-frontend-rebuild -- frontend/packages/shared` 可恢复 shared；`frontend/` 两端源码由同一 tag 恢复。
- 删除操作不使用 `rm`，用 `git rm`，保证可追溯。
