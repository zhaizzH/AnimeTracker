# 用户端页面行为对齐：认证 5 页与业务 7 页

父任务：`.trellis/tasks/10-12-frontend-rebuild`（技术设计与总体约束见父任务 `design.md`）。

## Goal

把 client 全部页面重建到新外壳下，并**行为对齐现状**：重新接回 `@shared` 的真实 API，逐页渲染 loading / empty / error。完成后 client 功能可用。

## 前置依赖

`10-12-rebuild-prep`（已清 shared）、`10-12-ui-infra`（基础设施）、`10-12-client-shell`（外壳与路由骨架）。**顺序理由**：页面挂在外壳路由下，且需要 primitive 通道。

## Requirements

- **R1 认证 5 页**：Login / Register / VerifyEmail / ForgotPassword / ResetPassword。保留 `setAuthenticated` + `publishSessionAvailable`；Password 变更后走 `publishSignedOut` 登出（对齐现存 `Profile.tsx` 行为）。
- **R2 业务 7 页**：Home、AnimeIndex（多条件筛选）、Schedule（放送日历）、SubjectDetail、MyCollections（收藏 + 追番进度 CRUD）、Profile（三个弹窗）、Agent。
- **R3 数据接线**：全部经 shared 命名空间 API（`subjectsApi` / `collectionsApi` / `tagsApi` / `authApi` / `clientAgentApi` 等），HTTP 边界不重复解包、不使用 `any`。
- **R4 状态渲染**：每页显式渲染 loading / empty / error/disabled（`component-guidelines.md:23`）；统计值 `0` 不作为空态（`component-guidelines.md:25`）；列表 key 用稳定业务 ID。
- **R5 Agent 能力**：`/agent` 页、`AIAssistantFloat` 浮窗、`AgentChat` 会话与流式渲染（含「停止」）；浮窗开合、Esc、焦点管理可达；`aria-live="polite"` 保留。
- **R6 可访问性**：图标按钮有可读 label/tooltip；不只靠颜色表状态；保留键盘提交与焦点可达（`component-guidelines.md:46-52`）。
- **R7 测试**：重写直接耦合旧 markup 的用例，覆盖不减少。

## Acceptance Criteria

- [ ] AC1：12 页均可渲染，数据来自真实 API（联调 business :8080）。
- [ ] AC2：筛选、收藏/进度 CRUD、放送日历切换、Profile 三弹窗、Agent 流式对话与浮窗开合行为与现状对齐。
- [ ] AC3：每页具备 loading / empty / error 三态。
- [ ] AC4：`npm test -w client` 通过；覆盖不减少（认证守卫、登录登出、Agent 浮窗开合与 Esc、Agent 流式启停、表格横向滚动区域）。
- [ ] AC5：`npm run typecheck` 通过；页面源码无 antd 导入。
- [ ] AC6：图标按钮有无障碍名，Agent 流式消息区有 `aria-live`。

## Out of Scope

- 新增业务功能（只对齐现状）。
- 后端契约变更。

## 交付给父任务

功能可用的 client：12 页接真实数据、三态齐全、测试覆盖不减少。
