# Hook 规范

## TanStack Query

- 服务端数据用 `useQuery`；queryKey 必须包含影响请求的全部筛选、分页和资源 ID。
- 写操作用 `useMutation`，成功后通过 `useQueryClient().invalidateQueries` 刷新权威数据。
- queryFn 调用 shared API 命名空间，不在 Hook 内重复 axios 配置。
- 条件请求使用 `enabled`，参考 SubjectDetail 的 ID 与 CollectionActions 的登录态。
- 全局默认 `retry: 1`、`refetchOnWindowFocus: false`；单页面按真实需要覆写轮询/staleTime。

## 自定义 Hook

- 名称以 `use` 开头，返回稳定的领域动作与状态，不泄露底层 AbortController。
- `useAgentChat` 负责会话、历史、SSE、停止和工具状态；client/admin 只提供不同 API 适配对象。
- 长生命周期回调用 `useCallback`；外部传入但引用不稳定的适配对象可用 ref 保存最新值。
- 异步竞态要有序列号或取消信号，参考 `historyRequest` 与 `AbortController`。
- effect 卸载时停止流式请求；不要让卸载组件继续写状态。

## 认证 Hook

- `useBootstrapAuth` 每个应用 Shell 只调用一次。
- 刷新必须走 `refreshWithLock`，复用标签页内 Promise 与 Navigator Locks。
- 401 重试只允许一次，且刷新接口本身不能再次触发刷新。
- 网络失败进入 `retryable-error`，401/403 才进入 `unauthenticated`。
- 跨标签页只广播“会话可用/已退出”，不广播 Access Token。

## 常见错误

- queryKey 漏掉 page/filter，显示旧缓存。
- 在 render 中直接调用异步函数。
- effect 依赖不稳定对象导致自动创建多个 Agent 会话。
- 捕获所有错误后返回空数组，掩盖需要展示的错误。
