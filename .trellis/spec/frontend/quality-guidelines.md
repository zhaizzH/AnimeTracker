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

- **测试数量不在此记录**：手抄基线在本仓已经错过三次（写 202 实测 205、写 32 文件实测 33、文件清单漏掉新增文件）。要数字就现场跑：

```bash
cd frontend && npm test && npm run typecheck   # 三包用例数看末尾的 Tests 行
find frontend -name '*.test.*' -not -path '*/node_modules/*' | wc -l   # 测试文件数
```

- 新增测试文件后**不需要**回来改本文档；本文档只记口径与约定，不记清单。
- admin 曾只有 `src/guards.test.tsx` 一个测试（覆盖 `RequireAdmin` 的未登录跳转、非管理员拒绝和管理员放行）；重建后各页与 `AdminLayout` 均已有测试。
- Vitest 使用 jsdom；浏览器能力 shim 内联在 `client/src/test/setup.ts`（`matchMedia` 等），不是独立文件。
- admin 的 `vitest.setup.ts` 已注册 `@testing-library/jest-dom/vitest`，并补齐 radix-ui 在 jsdom 下必需的最小 polyfill（`hasPointerCapture`/`setPointerCapture`/`releasePointerCapture`/`scrollIntoView` 与 `ResizeObserver`）。新增用到 radix 原语的测试直接复用，不要重复定义。
- 测试中 mock 的查询必须在 `render` 之前完成赋值：多数页面在首次 effect 就会取数，render 后再改 mock 不会触发重取。
- **否定断言前先建立正向基线**：`expect(x).not.toBe(...)` 只有在用例自己把 `x` 置成期望的正向状态后才有意义，否则测的是 `beforeEach` 的复位值而不是被测行为——写出来就是恒红（本仓实际发生过一次：store 在 `beforeEach` 被复位成 `unauthenticated`，断言「刷新失败不应登出」因此永远失败，与实现无关）。
- 新增关键 guard、mutation、SSE 或管理写操作时补最小测试，不以现有稀疏覆盖为标准。
- thinking 的语言、空格与历史恢复需跨 shared Hook、client/admin 展示和 Python runtime 核对；现有 UI/Prompt 静态测试不能证明真实模型遵循语言指令。源码核对见 [Agent 运行与提示词契约](../backend/agent-guidelines.md#agent-角色提示词与流式输出契约)。

## 构建与运行时事实

- client 开发端口为 5173，admin 为 5174；两个 Vite 配置都把 `/api` 代理到 Business `:8080`，并通过 `@shared` 指向 shared 源码。
- **`/media` 也必须代理到 MinIO**：两个 `vite.config.mts` 各有 `'/media': { target: 'http://localhost:9000/anime-tracker', rewrite: p => p.replace(/^\/media/, '') }`。浏览器前缀 `/media` 在开发环境由 Vite 重写并转发到 MinIO 桶根，生产环境由 nginx 同源提供（见 [MinIO 公开 URL 与反代前缀](../backend/database-guidelines.md#scenario-minio-图片公开-url-与反代前缀)）。目标是 `/media/{object_name}`（前缀已映射桶根，**不含桶名**），与后端 `MINIO_PUBLIC_BASE_URL=/media` 必须一致；`subject.image` / `user.avatar` 直接作为 `<img src>` 使用，前端不拼接。改动前端代理时若漏掉 `/media`，本地封面/头像全 404。
- client 额外预打包 `optimizeDeps.include`（`vite.config.mts`）中的 React/Query/Axios/Zustand，以及 `react-router-dom`、`react-markdown`、`remark-gfm`、`sonner`、`react-dom/client`（**不含 Ant Design**）；admin 的分包规则为 `vendor-react`（React 运行时）、`vendor-data`（TanStack/axios/zustand）、`vendor-ui`（radix-ui/sonner）。两个应用都使用显式 manual chunks，`chunkSizeWarningLimit` 为 560 kB（仅警告，不是硬失败阈值）。
- admin 已完全去除 Ant Design 与 ECharts 运行时依赖；图表使用 recharts（随 Dashboard 懒加载 chunk 走，不单独拆包）。若构建产物出现 `vendor-antd*` chunk，说明新代码重新引入了 Ant Design，应视为回归。
- 根 `npm test` 必须实际遍历 workspaces；共享出口、认证、HTTP/SSE 变更至少同时检查 client/admin 消费方。
- 允许仓库内存在**未被引用的文件**（未接线脚手架、历史遗留）；目录规范只登记被引用的活代码。这类文件不得进入构建产物——若出现在构建输出或 chunk 中，说明它已被接线，应同步更新目录规范。

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
