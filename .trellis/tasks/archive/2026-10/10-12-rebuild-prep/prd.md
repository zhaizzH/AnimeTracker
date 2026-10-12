# 重建准备：回滚锚点、清单核对与旧实现删除

父任务：`.trellis/tasks/10-12-frontend-rebuild`（技术设计与总体约束见父任务 `design.md`）。

## Goal

为两端 UI 重建建立安全网与核对依据，清理 `packages/shared` 的 antd 残留，并删除两端旧实现。本子任务不产出新 UI。

## 前置依赖

无。本子任务是 2 / 3 / 4 / 5 的前置（它们建立在「旧实现已删除」之上）。

## Requirements

- **R1 回滚锚点**：实施前 `git tag pre-frontend-rebuild`，确认工作区干净。
- **R2 核对表**：导出 `@shared` 引用清单与两端各页 API 依赖，作为后续重接依据，落盘到本任务 `research/`。
- **R3 字段核对**：逐项核对 `@efferd/dashboard-5` 各卡片所需后端字段是否在 `docs/spec/openapi.yaml` 与 shared 类型中存在；缺项登记为 deferred 并回报父任务。
- **R4 shared 清理**：移除 `packages/shared/src/theme.ts`、`index.ts:11` 的 `antdTheme`/`antdThemeDark` 导出、`packages/shared/package.json:12` 的 `antd` 依赖；改写 `SubjectCard.tsx` 中引用 `--od-*` 的注释与样式依赖。
- **R5 删除旧实现**：`git rm -r frontend/client/src`（**仅 client**；admin 经核验已是 `dashboard-5` 终态，不删除，见 `research/dashboard5-gaps.md`）；清理 client 仅服务旧实现的配置。

## Acceptance Criteria

- [ ] AC1：`git tag` 存在且指向删除前的 `main`。
- [ ] AC2：核对表落盘（`@shared` 引用点 + 两端各页 API 依赖）。
- [ ] AC3：`dashboard-5` 字段缺口清单已回报父任务（无缺口则显式写「无」）。
- [ ] AC4：shared 清理后 `cd frontend && npm run typecheck -w @animetracker/shared && npm test -w @animetracker/shared` 通过。
- [ ] AC5：`frontend/client/src` 已删除；`frontend` 源码内不再有 `from 'antd'` / `@ant-design/icons` / `od-` 引用（admin 早已无 antd，shared 已清）。

## Out of Scope

- 新建任何 UI（属子任务 2–5）。
- 修改后端契约。

## 交付给父任务

核对表、`dashboard-5` 字段缺口清单、shared 清理结果、删除范围确认。
