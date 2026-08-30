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
| [组件规范](./component-guidelines.md) | 页面、共享组件、样式与可访问性 |
| [Hook 规范](./hook-guidelines.md) | Query、mutation、SSE 与副作用 |
| [状态管理](./state-management.md) | TanStack Query、Zustand、本地与 URL 状态 |
| [类型安全](./type-safety.md) | shared 类型、边界收窄与跨层同步 |
| [质量门禁](./quality-guidelines.md) | typecheck、Vitest、构建与审查 |

## 关键约束

- API 只使用相对路径 `/api/**`；Vite 代理到 Business。
- Access Token 只存内存，禁止恢复到 localStorage。
- 普通 JSON 响应由 shared HTTP 拦截器解包；SSE 使用 fetch 流，不能混用。
- shared API 以命名空间导出，避免 `list/remove/schedule` 等同名冲突。
- client 与 admin 不互相导入源码，共享能力进入 `@animetracker/shared`。

## 质量检查

```bash
cd frontend
npm run typecheck
npm test
npm run build
```
