# Hook 规范

## TanStack Query

- 服务端数据用 `useQuery`；queryKey 必须包含影响请求的全部筛选、分页和资源 ID。
- 写操作用 `useMutation`，成功后通过 `useQueryClient().invalidateQueries` 刷新权威数据。
- 所有服务端写入都必须处理权威缓存，不限于封装成 `useMutation` 的调用：收藏进度执行至少核对收藏详情、列表和计数；资料更新至少核对 `['me']` 与会话用户。
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

### 双 HTTP 客户端与认证时序

- `http`（Axios）负责普通 JSON：从内存 store 注入 Bearer、解包 `ApiResult<T>.data`，401 最多刷新并重放原请求一次；刷新接口本身不得再次触发刷新。
- `sessionHttp` 只负责 refresh 等会话请求，不依赖普通请求拦截器；`streamSse` 使用原生 fetch，不会自动执行 Axios 的 401 刷新。
- SSE 收到 401/403 时，调用方必须保留 Abort 语义，按“刷新一次 → 重新打开同一流一次”或直接进入未认证状态处理，禁止无限重试。
- `refreshWithLock` 只保证同一标签页 Promise 复用及 Navigator Locks 串行；跨标签页广播不会携带 token，也不保证复用另一标签页的刷新结果，失败仍按 `retryable-error`/未认证矩阵处理。

### SSE 事件与帧边界

- `streamSse` 的请求必须是 POST JSON，携带可选 Bearer 和 `AbortSignal`；响应应为 `text/event-stream`，帧以空行结束，最后一个无换行帧也必须被处理。
- 事件联合至少包含 `answer`、`thinking`、`function_call`、`status` 与 `end`；`function_call.state` 使用 `start|end|error`，工具状态必须从 running 进入 done/error，不得永久停在 running。
- `is_end=true` 或明确 end 事件后停止写入；Abort、网络断开和解析失败必须分别保留可重试的用户语义。
- 当前实现只按单个换行切分、未校验 Content-Type、未 flush 尾帧，且 `useAgentChat` 忽略 status 与 function_call error；这些是已知债务，新增 SSE 改动必须补 parser、状态机、断开和鉴权失败测试。

### 服务端写入缓存矩阵

| 写入 | 成功后的最低处理 |
|---|---|
| 收藏/进度执行 | 失效相关收藏详情、收藏列表、计数及受影响 Subject 查询 |
| 资料更新 | 更新 Zustand 会话用户，并失效 `['me']`，避免页面继续显示旧快照 |
| 其他 mutation | 根据实际 queryKey 列出最窄但完整的失效集合；不能只改局部 state |

当前 `ProgressPreviewModal` 执行成功后未刷新收藏查询，`Profile` 更新资料后未失效 `['me']`；后续修复应先补回归测试，再调整缓存策略。

## 常见错误

- queryKey 漏掉 page/filter，显示旧缓存。
- 在 render 中直接调用异步函数。
- effect 依赖不稳定对象导致自动创建多个 Agent 会话。
- 捕获所有错误后返回空数组，掩盖需要展示的错误。
