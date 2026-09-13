# 前端 Hook 与状态管理

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [Hook 规范](#hook-规范)
- [状态管理规范](#状态管理规范)

## Hook 规范

### TanStack Query

- 服务端数据用 `useQuery`；queryKey 必须包含影响请求的全部筛选、分页和资源 ID。
- 写操作用 `useMutation`，成功后通过 `useQueryClient().invalidateQueries` 刷新权威数据。
- 所有服务端写入都必须处理权威缓存，不限于封装成 `useMutation` 的调用：收藏进度执行至少核对收藏详情、列表和计数；资料更新至少核对 `['me']` 与会话用户。
- queryFn 调用 shared API 命名空间，不在 Hook 内重复 axios 配置。
- 条件请求使用 `enabled`，参考 SubjectDetail 的 ID 与 CollectionActions 的登录态。
- 全局默认 `retry: 1`、`refetchOnWindowFocus: false`；单页面按真实需要覆写轮询/staleTime。

### 自定义 Hook

- 名称以 `use` 开头，返回稳定的领域动作与状态，不泄露底层 AbortController。
- `useAgentChat` 负责会话、历史、SSE、停止和工具状态；client/admin 只提供不同 API 适配对象。
- 长生命周期回调用 `useCallback`；外部传入但引用不稳定的适配对象可用 ref 保存最新值。
- 异步竞态要有序列号或取消信号，参考 `historyRequest` 与 `AbortController`。
- effect 卸载时停止流式请求；不要让卸载组件继续写状态。

### 认证 Hook

- `useBootstrapAuth` 每个应用 Shell 只调用一次。
- 刷新必须走 `refreshWithLock`，复用标签页内 Promise 与 Navigator Locks。
- 401 重试只允许一次，且刷新接口本身不能再次触发刷新。
- 网络失败进入 `retryable-error`，401/403 才进入 `unauthenticated`。
- 跨标签页只广播“会话可用/已退出”，不广播 Access Token。

#### 双 HTTP 客户端与认证时序

- `http`（Axios）负责普通 JSON：从内存 store 注入 Bearer、解包 `ApiResult<T>.data`，401 最多刷新并重放原请求一次；刷新接口本身不得再次触发刷新。
- `sessionHttp` 只负责 refresh 等会话请求，不依赖普通请求拦截器；`streamSse` 使用原生 fetch，不会自动执行 Axios 的 401 刷新。
- SSE 收到 401/403 时，调用方必须保留 Abort 语义，按“刷新一次 → 重新打开同一流一次”或直接进入未认证状态处理，禁止无限重试。
- `refreshWithLock` 只保证同一标签页 Promise 复用及 Navigator Locks 串行；跨标签页广播不会携带 token，也不保证复用另一标签页的刷新结果，失败仍按 `retryable-error`/未认证矩阵处理。

#### SSE 事件与帧边界

- `streamSse` 的请求必须是 POST JSON，携带可选 Bearer 和 `AbortSignal`；响应应为 `text/event-stream`，帧以空行结束，最后一个无换行帧也必须被处理。
- 事件联合至少包含 `answer`、`thinking`、`function_call`、`status` 与 `end`；`function_call.state` 使用 `start|end|error`，工具状态必须从 running 进入 done/error，不得永久停在 running。
- `is_end=true` 或明确 end 事件后停止写入；Abort、网络断开和解析失败必须分别保留可重试的用户语义。
- 当前 `packages/shared/src/sse.ts` 只按单个换行切分、未校验 Content-Type、未 flush 尾帧。`useAgentChat` 未单独处理 status 与 function_call error；含 `content.text` 的其他事件还可能落入正文拼接分支。`is_end` 仅跳过当前事件，没有锁住后续帧。这些是已知债务，新增 SSE 改动必须补 parser、状态机、断开和鉴权失败测试。

#### thinking 展示的现状

- `packages/shared/src/hooks/useAgentChat.ts` 按收到的 `content.text` 直接累加 thinking；没有翻译、空格修复或中文校验。
- client 的 `src/components/AgentChat.tsx` 与 admin 的 `src/pages/AgentChat.tsx` 分别渲染折叠区，不能只验证一端。
- 历史加载只恢复 role/content，不恢复 thinking；刷新后思考区域消失不是翻译成功或服务停止思考的证据。
- 排查连续英文单词先检查后端 chunk 的 `strip()`，不要先在前端插空格。完整链路见 [Agent 运行与提示词契约](../backend/agent-guidelines.md#agent-角色提示词与流式输出契约)。
- SSE 的 401/403 当前会进入通用中断分支，没有 Axios 自动刷新，也未区分主动 Abort 与故障；“刷新一次/停止重试”是后续应实现的契约。

#### 服务端写入缓存矩阵

| 写入 | 成功后的最低处理 |
|---|---|
| 收藏/进度执行 | 失效相关收藏详情、收藏列表、计数及受影响 Subject 查询 |
| 资料更新 | 更新 Zustand 会话用户，并失效 `['me']`，避免页面继续显示旧快照 |
| 其他 mutation | 根据实际 queryKey 列出最窄但完整的失效集合；不能只改局部 state |

当前 `ProgressPreviewModal` 执行成功后未刷新收藏查询，`Profile` 更新资料后未失效 `['me']`；后续修复应先补回归测试，再调整缓存策略。

### 常见错误

- queryKey 漏掉 page/filter，显示旧缓存。
- 在 render 中直接调用异步函数。
- effect 依赖不稳定对象导致自动创建多个 Agent 会话。
- 捕获所有错误后返回空数组，掩盖需要展示的错误。

## 状态管理规范

### 状态归属

| 状态 | 工具 | 例子 |
|---|---|---|
| 服务端缓存 | TanStack Query | 番剧、收藏、用户、导入状态、日志 |
| 跨应用会话状态 | Zustand 内存 store | token、user、auth status |
| 可持久化 UI 偏好 | Zustand persist | light/dark、跟随系统 |
| 单组件交互 | React state/ref | modal、输入、选中项、AbortController |
| 导航状态 | Router / URL | path 参数、返回地址、已实现的可分享筛选 |

### 鉴权状态机

`AuthStatus` 只有 `checking / authenticated / unauthenticated / retryable-error`。AuthGate 负责启动期门控，RequireAuth/RequireAdmin 只在确定状态后重定向。

- Access Token 只存 `useAuthStore` 内存，刷新凭据由 HttpOnly Cookie 承载。
- 初始化时主动删除旧 `animetracker-auth` localStorage，禁止重新启用 token 持久化。
- 登录成功设置 token/user 并广播 session available；退出成功清空并广播 signed out。
- 管理端同时验证 `status=authenticated` 与 `role=ADMIN`。
- 网络故障保留重试入口，不把它等同于退出登录。
- 跨标签页只同步会话事件；收到 `session-available` 后重新 refresh，不接收或持久化 Access Token。锁只串行刷新，不承诺跨标签页结果共享。

### Query 缓存

- 读取返回值视为服务端快照，不复制到 Zustand。
- mutation 后失效最窄但完整的 queryKey 集合。
- 轮询仅用于确有后台进度的资源，当前导入状态为 3 秒。
- 表单草稿保留本地，提交成功后再同步 Query。
- 不直接修改缓存来伪造 Agent 或 Business 写入成功。

#### URL 筛选的实现边界

- 当前 client AnimeIndex 仅将 `q/page` 写入 URL；admin Subjects/Logs 的筛选仍主要保存在本地 state。规范中的“可分享筛选”是目标模式，不得当成所有页面的现行事实。
- 新增 URL 筛选时必须定义：字段编码、默认值、刷新/返回可恢复性，以及筛选变化时页码归零。

### 主题状态

`useThemeStore` 仅持久化非敏感 UI 偏好；`resolveMode` 在 followSystem 时读取 `prefers-color-scheme`。持久化新字段前先确认不含身份、令牌或服务端权威数据。
当前 followSystem 只读取一次媒体查询值，未订阅系统主题变化；补订阅时必须在 effect 中注册/清理监听，并覆盖浏览器不支持 matchMedia 的降级路径。
