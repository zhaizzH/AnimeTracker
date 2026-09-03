# 前端质量门禁

## 质量门禁分层

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

| 层级 | 当前命令/要求 | 适用范围 |
|---|---|---|
| CI 强制 | `npm run typecheck` | 当前 `.github/workflows/ci.yml` 的前端门禁 |
| 提交前 | `npm test` 或受影响 workspace 的 Vitest | 普通组件、Hook、API 和状态改动 |
| 交付前 | `npm run build` | 路由、依赖、构建配置或可交付前端变更 |

CI 当前未强制 Vitest 和 build；不要在 spec 中把它们描述为已启用的 CI 门禁。项目没有 lint/format script，不能假设存在额外静态检查。

## 测试现状

- shared 有 API 上传与 `useAgentChat enabled` 测试。
- client 有首页、Agent Markdown 与浮层交互测试。
- admin 的首个测试位于 `src/guards.test.tsx`，覆盖 `RequireAdmin` 的未登录跳转、非管理员拒绝和管理员放行。
- Vitest 使用 jsdom；浏览器能力 shim 位于 `client/src/test/matchMedia.ts`。
- 新增关键 guard、mutation、SSE 或管理写操作时补最小测试，不以现有稀疏覆盖为标准。

## 构建与运行时事实

- client 开发端口为 5173，admin 为 5174；两个 Vite 配置都把 `/api` 代理到 Business `:8080`，并通过 `@shared` 指向 shared 源码。
- client 额外预打包常用 React、Ant Design、Query、Axios、Zustand 依赖；两个应用都使用显式 manual chunks，`chunkSizeWarningLimit` 为 560 kB（仅警告，不是硬失败阈值）。
- 根 `npm test` 必须实际遍历 workspaces；共享出口、认证、HTTP/SSE 变更至少同时检查 client/admin 消费方。

## 管理端守卫测试约定

- 测试通过 `MemoryRouter` 和真实 `Routes` 断言跳转结果，不直接调用守卫内部实现。
- mock `useAuthStore` 时显式设置 `status` 与 `user.role`，至少覆盖未登录、错误角色和正确角色。
- 未登录跳转还要断言 `location.state.from` 保留 path、query 与 hash，保证登录后可以返回原页面。
- 禁止使用 `vitest run --passWithNoTests` 掩盖管理端零测试；根目录 `npm test` 必须实际执行 admin 测试。

## 审查清单

- client/admin/shared 归属正确，没有跨应用源码导入。
- queryKey 包含全部参数，mutation 后缓存失效完整。
- token 未持久化，401 只重试一次，guard 不在 checking 时误跳转。
- SSE 能处理增量、结束、断开和组件卸载。
- OpenAPI、shared 类型、后端字段与 UI 状态同步。
- 对 HTTP/SSE 改动补 401/403、网络失败、Abort、尾帧和错误状态测试；对 mutation 补缓存失效断言。

## 禁止模式

- 页面自建 axios 实例或硬编码服务端 host。
- 用 `as any` 跳过接口漂移。
- 在 render 期间产生请求、导航或 message 副作用。
- 只验证 happy path，不覆盖 loading/empty/error/disabled。
- 修改 shared 公共出口后只检查一个应用。
