# 前端开发规范

适用范围：`frontend/client`、`frontend/admin` 与 `frontend/packages/shared`。

## 开发前检查

1. 判断代码属于用户端、管理端还是两个应用共享的契约/组件。
2. 涉及 HTTP 时先读 `shared/src/api/http.ts` 与对应命名空间 API。
3. 涉及登录态时先读 auth store、coordinator、AuthGate 和路由 guard。
4. 涉及 SSE 时同时核对 Agent 事件 schema 与 `useAgentChat.ts`。
5. 新增服务端数据时设计完整 queryKey，并明确 mutation 后失效范围。

## 规范索引

| 主题 | 内容 |
|---|---|
| [目录结构](./directory-structure.md) | npm workspaces 与代码归属 |
| [组件与类型](./component-guidelines.md) | 组件职责、样式、可访问性、类型所有权与 HTTP 类型边界 |
| [Hook 与状态](./hook-guidelines.md) | Query、mutation、SSE、认证、Zustand 与 URL 状态 |
| [质量门禁](./quality-guidelines.md) | typecheck、Vitest、构建与审查 |

## 关键约束

- API 只使用相对路径 `/api/**`；Vite 代理到 Business。
- Access Token 只存内存，禁止恢复到 localStorage。
- 普通 JSON 响应由 shared HTTP 拦截器解包；SSE 使用 fetch 流，不能混用。
- shared API 以命名空间导出，避免 `list/remove/schedule` 等同名冲突。
- client 与 admin 不互相导入源码，共享能力进入 `@animetracker/shared`。
- Agent 工具能力由后端角色路由决定，不能从前端页面或“思考过程”文本推断 RAG 已启用；联调时阅读 [Agent 运行与提示词契约](../backend/agent-guidelines.md#agent-角色提示词与流式输出契约)。

## 质量检查

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

质量门禁按变更范围执行：CI 当前强制 `npm run typecheck`；提交前运行受影响 workspace 的 `npm test`；路由、依赖、构建配置或交付型变更再运行 `npm run build`。详见 [质量门禁](./quality-guidelines.md)。

## 合并前路径对照

供历史任务和记录定位；归档引用保留原貌，重新启用旧任务时更新其上下文路径。

| 原文件 | 当前主题 |
|---|---|
| `type-safety.md` | [component-guidelines.md](./component-guidelines.md#类型安全规范) |
| `state-management.md` | [hook-guidelines.md](./hook-guidelines.md#状态管理规范) |
