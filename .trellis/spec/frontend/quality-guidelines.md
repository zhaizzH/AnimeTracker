# 前端质量门禁

## 必跑命令

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

CI 当前只执行 `npm run typecheck`；提交前仍应运行相关 Vitest，交付型变更再运行 build。

## 测试现状

- shared 有 API 上传与 `useAgentChat enabled` 测试。
- client 有首页、Agent Markdown 与浮层交互测试。
- admin 当前没有测试文件。
- Vitest 使用 jsdom；浏览器能力 shim 位于 `client/src/test/matchMedia.ts`。
- 新增关键 guard、mutation、SSE 或管理写操作时补最小测试，不以现有稀疏覆盖为标准。

## 审查清单

- client/admin/shared 归属正确，没有跨应用源码导入。
- queryKey 包含全部参数，mutation 后缓存失效完整。
- token 未持久化，401 只重试一次，guard 不在 checking 时误跳转。
- SSE 能处理增量、结束、断开和组件卸载。
- OpenAPI、shared 类型、后端字段与 UI 状态同步。

## 禁止模式

- 页面自建 axios 实例或硬编码服务端 host。
- 用 `as any` 跳过接口漂移。
- 在 render 期间产生请求、导航或 message 副作用。
- 只验证 happy path，不覆盖 loading/empty/error/disabled。
- 修改 shared 公共出口后只检查一个应用。
